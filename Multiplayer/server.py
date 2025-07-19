import socket
import threading
import time
import random
import json

# --- Server Configuration ---
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)
MAX_PLAYERS = 4     # Maximum number of players allowed to connect

# --- Game Constants (Server-side) ---
DISPLAY_W = 1320    # Width of the game display
DISPLAY_H = 680     # Height of the game display
CAR_WIDTH = 77      # Width of the player car
THING_WIDTH = 65    # Width of obstacle cars
THING_HEIGHT = 130  # Height of obstacle cars
INITIAL_THING_SPEED = 7 # Base speed of obstacles

# --- Game State ---
# This dictionary holds the authoritative state of the game.
# It is shared across threads and protected by a lock.
game_state = {
    'players': {},      # Dictionary of active players: {player_id: {x, y, score, crashed, car_img_index}}
    'obstacles': [],    # List of active obstacles: [{id, x, y, speed, img_index}]
    'road_offset': 0,   # For continuous road scrolling visual effect (client side)
    'game_active': False, # True when at least one player is connected
    'player_count': 0,  # Current number of connected players
    'player_ids': []    # List of active player IDs for easy iteration
}

# Lock for thread-safe access to game_state to prevent race conditions
game_state_lock = threading.Lock()
# Lock for thread-safe access to active_connections
active_connections_lock = threading.Lock()

# --- Obstacle Management ---
obstacle_id_counter = 0 # Unique ID counter for obstacles

def create_new_obstacle(y_offset=0):
    """
    Creates a new obstacle with a random position and speed.
    Args:
        y_offset (int): Vertical offset to start the obstacle further up the screen.
    Returns:
        dict: A dictionary representing the new obstacle.
    """
    global obstacle_id_counter
    obstacle_id_counter += 1
    return {
        'id': obstacle_id_counter,
        'x': random.randrange(0, DISPLAY_W - THING_WIDTH),  # Random X position within screen bounds
        'y': -THING_HEIGHT - y_offset,                      # Start above the screen
        'speed': INITIAL_THING_SPEED + random.randint(0, 5), # Vary speed slightly
        'img_index': random.randint(0, 4)                   # Index for client-side image array (0-4 for 5 images)
    }

# Initialize some obstacles when the server starts
game_state['obstacles'].append(create_new_obstacle(y_offset=0))
game_state['obstacles'].append(create_new_obstacle(y_offset=200))
game_state['obstacles'].append(create_new_obstacle(y_offset=400))


# --- Client Handling ---
def handle_client(conn, addr, player_id):
    """
    Handles communication with a single client in a separate thread.
    Receives player input and commands, updates game state accordingly.
    Args:
        conn (socket.socket): The socket object for the client connection.
        addr (tuple): The address (IP, port) of the client.
        player_id (str): The unique ID assigned to this player.
    """
    print(f"Connected by {addr}, assigned ID: {player_id}")

    # Assign a random car image index to the player for their representation on other clients
    player_car_img_index = random.randint(0, 4) # Assuming 5 car images (index 0-4)

    # Add player to game state
    with game_state_lock:
        game_state['players'][player_id] = {
            'x': DISPLAY_W * 0.45,  # Initial X position
            'y': DISPLAY_H * 0.7,   # Initial Y position
            'score': 0,             # Initial score
            'crashed': False,       # Crash status
            'car_img_index': player_car_img_index # Image index for this player's car
        }
        game_state['player_count'] += 1
        game_state['player_ids'].append(player_id)
        if game_state['player_count'] >= 1:
            game_state['game_active'] = True # Activate game loop when first player connects

    try:
        # Send the assigned player ID to the client immediately
        # This is crucial for the client to know its identity in the game state.
        conn.sendall(json.dumps({'your_id': player_id}).encode('utf-8'))

        while True:
            # Receive data from client (player input or commands)
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break # Client disconnected

            try:
                client_message = json.loads(data)
                with game_state_lock:
                    if player_id in game_state['players']: # Check if player still exists in state
                        player_data = game_state['players'][player_id]

                        if client_message.get('command') == 'reset_player':
                            # Client requested to reset after a crash
                            print(f"Player {player_id} requested reset.")
                            player_data['x'] = DISPLAY_W * 0.45
                            player_data['y'] = DISPLAY_H * 0.7
                            player_data['score'] = 0
                            player_data['crashed'] = False
                        elif 'x_change' in client_message and 'y_change' in client_message:
                            # Player movement input
                            if not player_data['crashed']: # Only allow movement if not crashed
                                player_data['x'] += client_message['x_change']
                                player_data['y'] += client_message['y_change']

                                # Keep player within screen bounds (server-side validation)
                                player_data['x'] = max(0, min(player_data['x'], DISPLAY_W - CAR_WIDTH))
                                player_data['y'] = max(0, min(player_data['y'], DISPLAY_H - 155)) # Assuming car height ~155
            except json.JSONDecodeError:
                print(f"Invalid JSON received from {addr}: {data}")

    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        # Remove player from game state and active connections on disconnect
        with game_state_lock:
            if player_id in game_state['players']:
                del game_state['players'][player_id]
                game_state['player_ids'].remove(player_id)
                game_state['player_count'] -= 1
                if game_state['player_count'] == 0:
                    game_state['game_active'] = False # Pause game if no players left
                    print("No players left, game paused.")
        
        with active_connections_lock:
            if player_id in active_connections:
                del active_connections[player_id]
        
        print(f"Client {addr} (ID: {player_id}) disconnected.")
        conn.close()

# --- Game Logic Loop (Server-side) ---
def game_loop_server():
    """
    The main game logic loop running on the server.
    Updates obstacle positions, checks for collisions, and manages scores.
    """
    while True:
        if not game_state['game_active']:
            time.sleep(0.1) # Sleep if no players are active
            continue

        with game_state_lock:
            # Update obstacle positions
            for obstacle in game_state['obstacles']:
                obstacle['y'] += obstacle['speed']

            # Remove off-screen obstacles and add new ones
            new_obstacles = []
            for obstacle in game_state['obstacles']:
                if obstacle['y'] > DISPLAY_H:
                    # Obstacle passed the screen bottom
                    # Increment score for all currently active (non-crashed) players
                    for player_id in game_state['player_ids']:
                        if not game_state['players'][player_id]['crashed']:
                            game_state['players'][player_id]['score'] += 1
                    # Add a new obstacle to replace the one that went off-screen
                    new_obstacles.append(create_new_obstacle())
                else:
                    new_obstacles.append(obstacle)
            game_state['obstacles'] = new_obstacles

            # Collision detection (server-authoritative)
            # Iterate over a copy of players to avoid issues if player_data is modified
            for player_id, player_data in list(game_state['players'].items()):
                if player_data['crashed']:
                    continue # Skip collision check for already crashed players

                player_x = player_data['x']
                player_y = player_data['y']

                for obstacle in game_state['obstacles']:
                    obstacle_x = obstacle['x']
                    obstacle_y = obstacle['y']

                    # Simple Axis-Aligned Bounding Box (AABB) collision detection
                    # Check if the bounding boxes of the car and obstacle overlap
                    if (player_x < obstacle_x + THING_WIDTH and
                        player_x + CAR_WIDTH > obstacle_x and
                        player_y < obstacle_y + THING_HEIGHT and
                        player_y + 155 > obstacle_y): # Assuming player car height ~155
                        print(f"Player {player_id} crashed!")
                        player_data['crashed'] = True # Mark player as crashed
                        break # No need to check other obstacles for this player

            # Update road offset for client-side continuous scrolling visual effect
            game_state['road_offset'] = (game_state['road_offset'] + 8) % DISPLAY_H # Road scrolls at speed 8

        # Send the current game state to all connected clients
        current_game_state_copy = None
        with game_state_lock: # Lock game_state while preparing the JSON
            current_game_state_copy = json.dumps(game_state).encode('utf-8')

        # Iterate over a COPY of active_connections to avoid issues if it's modified during iteration
        # Use active_connections_lock for thread-safe access
        connections_to_remove = []
        with active_connections_lock:
            for player_id, client_conn in list(active_connections.items()):
                try:
                    client_conn.sendall(current_game_state_copy)
                except Exception as e:
                    # If sending fails, the client has likely disconnected.
                    print(f"Failed to send state to client {player_id}: {e}")
                    connections_to_remove.append(player_id)
        
        # Remove disconnected clients outside the iteration loop to avoid modifying during iteration
        with active_connections_lock:
            for player_id in connections_to_remove:
                if player_id in active_connections:
                    # The handle_client thread should also remove it, but this acts as a safeguard
                    # and ensures the game_loop_server doesn't keep trying to send to a dead socket.
                    # The handle_client thread will perform the full cleanup of game_state.
                    del active_connections[player_id]


        time.sleep(0.05) # Server game tick rate (e.g., 20 FPS)

# --- Main Server Setup ---
active_connections = {} # Dictionary to store active client connections: {player_id: socket_object}
next_player_id = 1      # Counter for assigning unique player IDs

def start_server():
    """
    Initializes and starts the server, listening for incoming client connections.
    """
    global next_player_id
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allows immediate reuse of the address
    server_socket.bind((HOST, PORT))
    server_socket.listen(MAX_PLAYERS) # Listen for up to MAX_PLAYERS connections
    print(f"Server listening on {HOST}:{PORT}")

    # Start the server-side game logic loop in a separate daemon thread
    # A daemon thread will exit automatically when the main program exits.
    game_logic_thread = threading.Thread(target=game_loop_server)
    game_logic_thread.daemon = True
    game_logic_thread.start()

    while True:
        try:
            conn, addr = server_socket.accept() # Accept a new client connection
            with active_connections_lock: # Lock when checking/modifying active_connections
                if len(active_connections) >= MAX_PLAYERS:
                    # Reject connection if max players reached
                    print(f"Connection from {addr} rejected: Max players reached.")
                    conn.sendall(json.dumps({'status': 'rejected', 'message': 'Max players reached. Please try again later.'}).encode('utf-8'))
                    conn.close()
                    continue

                # Assign a unique player ID
                player_id = f"player_{next_player_id}"
                next_player_id += 1
                active_connections[player_id] = conn # Store the connection

            # Start a new thread to handle this specific client
            client_thread = threading.Thread(target=handle_client, args=(conn, addr, player_id))
            client_thread.daemon = True
            client_thread.start()
        except KeyboardInterrupt:
            print("Server shutting down.")
            break # Exit the loop on Ctrl+C
        except Exception as e:
            print(f"Error accepting connection: {e}")

    server_socket.close() # Close the server socket when done

if __name__ == "__main__":
    start_server()

