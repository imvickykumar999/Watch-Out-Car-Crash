import pygame
import socket
import json
import threading

pygame.init()

display_w = 1320
display_h = 680
car_width = 77
car_height = 155

black = (0,0,0)
yellow = (200, 200, 0)

gameD = pygame.display.set_mode((display_w, display_h))
pygame.display.set_caption('Watch Out Multiplayer')

clock = pygame.time.Clock()

carimg = pygame.image.load('image/1.png').convert_alpha()
carimg2 = pygame.image.load('image/2.png').convert_alpha()

foo = [pygame.image.load(f'image/{i}.png').convert_alpha() for i in range(2,7)]

thing_width = 65
thing_height = 130

# Networking setup
SERVER_IP = input("Enter server IP: ")  # put your playit.gg address here
PORT = 5555

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, PORT))

player_id = None

game_state = {}

input_state = {'left': False, 'right': False, 'up': False, 'down': False}

def send_inputs():
    while True:
        try:
            client.sendall(json.dumps(input_state).encode())
            data = client.recv(4096).decode()
            if not data:
                break
            global game_state
            game_state = json.loads(data)
        except:
            break

# Start network thread
threading.Thread(target=send_inputs, daemon=True).start()

def draw_text(text, x, y):
    font=pygame.font.SysFont(None, 25)
    text_surface = font.render(text, True, black)
    gameD.blit(text_surface, (x, y))

def draw_car(x, y, image):
    gameD.blit(image, (x, y))

def draw_thing(x, y, image):
    gameD.blit(image, (x, y))

def main():
    running = True
    while running:
        gameD.fill(yellow)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    input_state['left'] = True
                if event.key == pygame.K_RIGHT:
                    input_state['right'] = True
                if event.key == pygame.K_UP:
                    input_state['up'] = True
                if event.key == pygame.K_DOWN:
                    input_state['down'] = True

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    input_state['left'] = False
                if event.key == pygame.K_RIGHT:
                    input_state['right'] = False
                if event.key == pygame.K_UP:
                    input_state['up'] = False
                if event.key == pygame.K_DOWN:
                    input_state['down'] = False

        # Draw players
        players = game_state.get('players', {})
        for pid, pdata in players.items():
            x, y, score = pdata['x'], pdata['y'], pdata['score']
            car_img_to_use = carimg if int(pid) == 1 else carimg2
            draw_car(x, y, car_img_to_use)
            draw_text(f"P{pid} Score: {score}", 10, 30 * int(pid))

        # Draw obstacles
        things = game_state.get('things', [])
        for idx, thing in enumerate(things):
            # Cycle images for obstacles
            img = foo[idx % len(foo)]
            draw_thing(thing['x'], thing['y'], img)

        pygame.display.update()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
