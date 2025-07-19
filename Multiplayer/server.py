import socket
import threading
import json
import random
import time

# Server config
HOST = '0.0.0.0'
PORT = 5555

# Game state
players = {
    1: {'x': 660, 'y': 500, 'score': 0},
    2: {'x': 660, 'y': 500, 'score': 0}
}

things = []  # List of obstacles: dicts with x,y

thing_width = 65
thing_height = 130
display_w = 1320
display_h = 680
thing_speed = 7

lock = threading.Lock()

def create_obstacle():
    return {'x': random.randint(0, display_w - thing_width), 'y': -thing_height}

# Initialize some obstacles
for _ in range(3):
    things.append(create_obstacle())

def handle_client(conn, player_id):
    global players, things
    print(f"Player {player_id} connected.")
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            input_data = json.loads(data)
            # input_data: {'left': bool, 'right': bool, 'up': bool, 'down': bool}

            with lock:
                # Update player position based on input
                speed = 5
                if input_data.get('left'):
                    players[player_id]['x'] -= speed
                if input_data.get('right'):
                    players[player_id]['x'] += speed
                if input_data.get('up'):
                    players[player_id]['y'] -= speed
                if input_data.get('down'):
                    players[player_id]['y'] += speed

                # Clamp player inside screen
                players[player_id]['x'] = max(0, min(display_w - 77, players[player_id]['x']))
                players[player_id]['y'] = max(0, min(display_h - 155, players[player_id]['y']))

            # Send updated state back to client
            with lock:
                game_state = {
                    'players': players,
                    'things': things
                }
            conn.sendall(json.dumps(game_state).encode())

    except Exception as e:
        print(f"Player {player_id} disconnected: {e}")

    finally:
        conn.close()
        with lock:
            players.pop(player_id, None)
        print(f"Player {player_id} connection closed.")

def game_loop():
    global things, players
    while True:
        with lock:
            # Move obstacles down
            for thing in things:
                thing['y'] += thing_speed
                if thing['y'] > display_h:
                    thing['y'] = -thing_height
                    thing['x'] = random.randint(0, display_w - thing_width)
                    # Increase score of all players dodging successfully
                    for p in players.values():
                        p['score'] += 1

            # Check collisions
            for pid, player in players.items():
                px, py = player['x'], player['y']
                for thing in things:
                    if (px < thing['x'] + thing_width and
                        px + 77 > thing['x'] and
                        py < thing['y'] + thing_height and
                        py + 155 > thing['y']):
                        # Collision detected - reset player position and score
                        player['x'] = 660
                        player['y'] = 500
                        player['score'] = 0
                        print(f"Player {pid} crashed!")

        time.sleep(1/60)  # 60 FPS game loop

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server listening on {HOST}:{PORT}")

    threading.Thread(target=game_loop, daemon=True).start()

    player_id = 1
    while True:
        conn, addr = server.accept()
        if player_id > 2:
            # Support only 2 players
            conn.close()
            continue
        threading.Thread(target=handle_client, args=(conn, player_id), daemon=True).start()
        player_id += 1

if __name__ == "__main__":
    main()
