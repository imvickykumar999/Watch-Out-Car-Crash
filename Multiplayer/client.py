import pygame
import time
import random
import json
import socket
import threading
import sys # Import sys for a cleaner exit

# --- Client Configuration ---
HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

# --- Pygame Initialization ---
pygame.init()

# --- Display Settings ---
DISPLAY_H = 680
DISPLAY_W = 1320
gameD = pygame.display.set_mode((DISPLAY_W, DISPLAY_H))
pygame.display.set_caption('Watch Out - Multiplayer')
clock = pygame.time.Clock()

# --- Colors ---
BLACK = (0, 0, 0)
GREY = (192, 192, 192)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BRIGHT_GREEN = (0, 255, 0)
YELLOW = (200, 200, 0)
BRIGHT_RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255) # Added for placeholder

# --- Game Assets (User must provide these files in 'image/' and 'sound/' directories) ---
# IMPORTANT: The user needs to ensure these files exist in the specified paths.
# If they don't exist, Pygame will raise an error, and placeholders will be used.
try:
    IMG_ROAD = pygame.image.load('image/road.jpg').convert_alpha()
    PLAYER_CAR_IMG = pygame.image.load('image/1.png').convert_alpha() # Image for this client's car
    # Images for other players' cars and obstacles
    OTHER_CAR_IMGS = [
        pygame.image.load('image/2.png').convert_alpha(),
        pygame.image.load('image/3.png').convert_alpha(),
        pygame.image.load('image/4.png').convert_alpha(),
        pygame.image.load('image/5.png').convert_alpha(),
        pygame.image.load('image/6.png').convert_alpha()
    ]

    CRASH_SOUND = pygame.mixer.Sound("sound/crash.wav")
    pygame.mixer.music.load("sound/jazz.wav")
    SOUNDS_LOADED = True
except pygame.error as e:
    print(f"Warning: Could not load game assets. Please ensure 'image/' and 'sound/' directories exist with the required files. Error: {e}")
    SOUNDS_LOADED = False
    # Create placeholder surfaces if images fail to load
    IMG_ROAD = pygame.Surface((DISPLAY_W, DISPLAY_H))
    IMG_ROAD.fill(GREY)
    PLAYER_CAR_IMG = pygame.Surface((77, 155)) # Approximate car dimensions
    PLAYER_CAR_IMG.fill(WHITE)
    OTHER_CAR_IMGS = [pygame.Surface((65, 130)) for _ in range(5)] # Approximate obstacle dimensions
    for img in OTHER_CAR_IMGS: img.fill(WHITE)

# --- Game State (Client-side) ---
# This dictionary will be updated by the `receive_data` thread with the latest server state.
current_game_state = {
    'players': {},
    'obstacles': [],
    'road_offset': 0,
    'game_active': False
}
client_player_id = None # This client's unique ID assigned by the server
game_running = True     # Flag to control the main game loop
pause = False           # Flag for pausing the game

# --- Network Communication ---
client_socket = None    # Socket object for communication with the server
state_lock = threading.Lock() # Lock for thread-safe access to current_game_state

def receive_data():
    """
    Receives game state updates from the server in a separate thread.
    Parses JSON data and updates the client's `current_game_state`.
    """
    global current_game_state, game_running, client_player_id
    while game_running:
        try:
            # Receive data (up to 4096 bytes)
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                print("Server disconnected.")
                game_running = False
                break
            
            with state_lock:
                current_game_state = json.loads(data)
                # Note: client_player_id is set in the main block after initial connection.
                # This thread just continuously updates the game state.

        except socket.error as e:
            print(f"Socket error during receive: {e}")
            game_running = False
            break
        except json.JSONDecodeError as e:
            # This can happen if multiple JSONs are concatenated or a partial JSON is received.
            # In a real game, you'd use a more robust message framing protocol (e.g., prefixing with length).
            print(f"JSON decode error: {e}, Data: {data[:200]}...")
        except Exception as e:
            print(f"Unexpected error in receive_data: {e}")
            game_running = False
            break

def send_input(x_change=0, y_change=0, command=None):
    """
    Sends player movement input or commands to the server.
    Args:
        x_change (int): Change in X-coordinate.
        y_change (int): Change in Y-coordinate.
        command (str, optional): A specific command string (e.g., 'reset_player').
    """
    if client_socket and client_player_id: # Ensure we have a socket and our ID before sending
        try:
            message_data = {}
            if command:
                message_data['command'] = command
            else:
                message_data['x_change'] = x_change
                message_data['y_change'] = y_change
            client_socket.sendall(json.dumps(message_data).encode('utf-8'))
        except socket.error as e:
            print(f"Socket error during send: {e}")
            global game_running
            game_running = False
        except Exception as e:
            print(f"Error sending input/command: {e}")

# --- Pygame Utility Functions ---
def text_objects(text, font, color=BLACK):
    """Renders text into a surface and its rectangle."""
    textsurface = font.render(text, True, color)
    return textsurface, textsurface.get_rect()

def message_display(text, color=BLACK):
    """Displays a large message in the center of the screen."""
    largetext = pygame.font.Font('freesansbold.ttf', 115)
    textsurf, textrect = text_objects(text, largetext, color)
    textrect.center = ((DISPLAY_W / 2), (DISPLAY_H / 2))
    gameD.blit(textsurf, textrect)
    pygame.display.update()
    time.sleep(2)

def button(msg, x, y, w, h, ic, ac, action=None):
    """
    Creates a clickable button.
    Args:
        msg (str): Text displayed on the button.
        x, y (int): Top-left coordinates of the button.
        w, h (int): Width and height of the button.
        ic (tuple): Inactive color of the button.
        ac (tuple): Active (hover) color of the button.
        action (callable, optional): Function to call when the button is clicked.
    """
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    if x + w > mouse[0] > x and y + h > mouse[1] > y:
        pygame.draw.rect(gameD, ac, (x, y, w, h))
        if click[0] == 1 and action is not None:
            action()
    else:
        pygame.draw.rect(gameD, ic, (x, y, w, h))

    smallText = pygame.font.SysFont("comicsansms", 20)
    textSurf, textRect = text_objects(msg, smallText)
    textRect.center = ((x + (w / 2)), (y + (h / 2)))
    gameD.blit(textSurf, textRect)

def quit_game():
    """Exits the game cleanly."""
    global game_running
    game_running = False # Signal other threads to stop
    if client_socket:
        client_socket.close() # Close the socket
    pygame.quit()
    sys.exit() # Use sys.exit() for a clean exit

def unpause():
    """Unpauses the game and resumes music."""
    global pause
    if SOUNDS_LOADED:
        pygame.mixer.music.unpause()
    pause = False

def crashed_screen():
    """Displays the 'You Crashed' screen and handles play/quit options."""
    global game_running, pause
    
    if SOUNDS_LOADED:
        pygame.mixer.music.stop()
        pygame.mixer.Sound.play(CRASH_SOUND)
    gameD.fill(YELLOW)

    largeText = pygame.font.SysFont("comicsansms", 115)
    TextSurf, TextRect = text_objects("You Crashed", largeText)
    TextRect.center = ((DISPLAY_W / 2), (DISPLAY_H / 2))
    gameD.blit(TextSurf, TextRect)

    exit_crashed_screen = False # Flag to exit this screen's loop

    while not exit_crashed_screen:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            
        # Action for the "Play Again" button
        def play_again_action():
            nonlocal exit_crashed_screen
            send_input(command='reset_player') # Tell server to reset our player
            pause = False # Ensure game is not paused when resuming
            exit_crashed_screen = True # Set flag to exit this screen

        button("Play Again", 350, 450, 100, 50, GREEN, BRIGHT_GREEN, play_again_action)
        button("Quit", 900, 450, 100, 50, RED, BRIGHT_RED, quit_game)

        pygame.display.update()
        clock.tick(60)

    # After exiting this loop, control returns to the main game_loop

def paused_screen():
    """Displays the 'Paused' screen and handles continue/quit options."""
    global pause
    if SOUNDS_LOADED:
        pygame.mixer.music.pause()
    while pause:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()

        gameD.fill(YELLOW)
        largeText = pygame.font.SysFont("comicsansms", 115)
        TextSurf, TextRect = text_objects("Paused", largeText)
        TextRect.center = ((DISPLAY_W / 2), (DISPLAY_H / 2))
        gameD.blit(TextSurf, TextRect)

        button("Continue", 350, 450, 100, 50, GREEN, BRIGHT_GREEN, unpause)
        button("Quit", 900, 450, 100, 50, RED, BRIGHT_RED, quit_game)

        pygame.display.update()
        clock.tick(60)

def game_intro():
    """Displays the game introduction screen with 'GO!' and 'Quit' buttons."""
    intro = True
    while intro:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            
        gameD.fill(YELLOW)
        largeText = pygame.font.SysFont("comicsansms", 115)
        TextSurf, TextRect = text_objects("Watch Out!", largeText)
        TextRect.center = ((DISPLAY_W / 2), (DISPLAY_H / 2))
        gameD.blit(TextSurf, TextRect)

        # Lambda function to set intro to False when "GO!" is clicked
        button("GO!", 350, 450, 100, 50, GREEN, BRIGHT_GREEN, lambda: setattr(sys.modules[__name__], 'intro', False))
        button("Quit", 900, 450, 100, 50, RED, BRIGHT_RED, quit_game)

        pygame.display.update()
        clock.tick(60)

# --- Game Rendering Functions ---
def draw_road(roady):
    """Draws the road background, creating a continuous scrolling effect."""
    gameD.blit(IMG_ROAD, (0, roady))
    gameD.blit(IMG_ROAD, (0, roady - DISPLAY_H)) # Draw a second image above for seamless scrolling

def draw_player_car(x, y):
    """Draws this client's player car."""
    gameD.blit(PLAYER_CAR_IMG, (x, y))

def draw_other_car(img_index, x, y):
    """
    Draws other players' cars or obstacles based on an image index.
    Args:
        img_index (int): Index of the image in OTHER_CAR_IMGS list.
        x, y (int): Coordinates to draw the car/obstacle.
    """
    if 0 <= img_index < len(OTHER_CAR_IMGS):
        gameD.blit(OTHER_CAR_IMGS[img_index], (x, y))
    else:
        # Fallback if img_index is out of bounds (should not happen if server sends valid indices)
        pygame.draw.rect(gameD, BLUE, (x, y, 65, 130)) # Placeholder blue rectangle

def display_scores(players_data):
    """
    Displays the scores and status of all players.
    Args:
        players_data (dict): Dictionary of all players' data from the server state.
    """
    font = pygame.font.SysFont(None, 25)
    y_offset = 0
    for player_id, data in players_data.items():
        color = BLACK
        if player_id == client_player_id:
            color = GREEN # Highlight this client's score
        
        # Display player ID and score
        score_text = font.render(f"{player_id}: SCORE {data['score']}", True, color)
        gameD.blit(score_text, (0, y_offset))
        
        # Display "CRASHED!" if the player has crashed
        if data['crashed']:
            crashed_text = font.render("CRASHED!", True, RED)
            gameD.blit(crashed_text, (score_text.get_width() + 10, y_offset)) # Position next to score
        
        y_offset += 30 # Move down for the next player's score

# --- Main Game Loop (Client-side) ---
def game_loop():
    """
    The main game loop for the client.
    Handles user input, receives server state, and renders the game.
    """
    global pause, game_running

    if SOUNDS_LOADED:
        pygame.mixer.music.play(-1) # Loop background music indefinitely

    # Variables to track player input changes (sent to server)
    x_change, y_change = 0, 0

    while game_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x_change = -5
                elif event.key == pygame.K_RIGHT:
                    x_change = 5
                elif event.key == pygame.K_UP:
                    y_change = -5
                elif event.key == pygame.K_DOWN:
                    y_change = 5
                elif event.key == pygame.K_p:
                    pause = True
                    paused_screen() # Call paused_screen, which blocks until unpaused
                send_input(x_change, y_change) # Send input immediately on key down

            if event.type == pygame.KEYUP:
                # Stop movement when key is released
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    x_change = 0
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    y_change = 0
                send_input(x_change, y_change) # Send input to stop movement

        # Acquire lock to safely read the game state updated by the receive_data thread
        with state_lock:
            # Draw road
            road_offset = current_game_state.get('road_offset', 0)
            draw_road(road_offset)

            # Draw all players' cars
            players_data = current_game_state.get('players', {})
            for p_id, p_data in players_data.items():
                if p_id == client_player_id:
                    # Draw this client's car
                    draw_player_car(p_data['x'], p_data['y'])
                    # If this client's player has crashed, display the crashed screen
                    if p_data['crashed'] and not pause:
                        crashed_screen() # This function will block until "Play Again" or "Quit"
                else:
                    # Draw other players' cars using their assigned image index
                    draw_other_car(p_data.get('car_img_index', 0), p_data['x'], p_data['y'])

            # Draw obstacles
            obstacles_data = current_game_state.get('obstacles', [])
            for obstacle in obstacles_data:
                draw_other_car(obstacle['img_index'], obstacle['x'], obstacle['y'])

            # Display scores for all players
            display_scores(players_data)

        pygame.display.update() # Update the entire screen
        clock.tick(60) # Limit client-side FPS to 60

    # Cleanup on game exit (will be handled by quit_game() if called)
    if client_socket:
        client_socket.close()
    pygame.quit()
    sys.exit()

# --- Main Client Logic ---
if __name__ == "__main__":
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Attempting to connect to server at {HOST}:{PORT}...")
        client_socket.connect((HOST, PORT))
        
        # First, receive the assigned player ID from the server
        # The server sends a JSON message like {'your_id': 'player_1'}
        initial_response_data = client_socket.recv(1024).decode('utf-8')
        initial_response = json.loads(initial_response_data)

        if 'your_id' in initial_response:
            client_player_id = initial_response['your_id']
            print(f"Successfully connected. Assigned player ID: {client_player_id}")

            # Start a separate thread to continuously receive game state updates from the server
            receive_thread = threading.Thread(target=receive_data)
            receive_thread.daemon = True # Daemon thread exits when main program exits
            receive_thread.start()

            # Start the game introduction screen, then the main game loop
            game_intro()
            game_loop()

        elif 'status' in initial_response and initial_response['status'] == 'rejected':
            # Handle server rejection (e.g., max players reached)
            print(f"Connection rejected by server: {initial_response.get('message', 'Unknown reason')}")
            game_running = False # Prevent game from starting
        else:
            # Handle unexpected initial response from the server
            print(f"Unexpected initial response from server: {initial_response_data}")
            game_running = False

    except ConnectionRefusedError:
        print(f"ERROR: Could not connect to server at {HOST}:{PORT}. Make sure the server is running.")
        game_running = False
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to decode initial server response as JSON: {e}. Data: {initial_response_data[:100]}...")
        game_running = False
    except Exception as e:
        print(f"An unexpected error occurred during client setup: {e}")
        game_running = False
    finally:
        # Ensure Pygame and socket are properly closed if game_running becomes False
        if not game_running:
            if client_socket:
                client_socket.close()
            pygame.quit()
            sys.exit()
