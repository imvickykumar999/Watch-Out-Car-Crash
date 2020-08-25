import pygame
import time 
import random
import math

pygame.init()

display_h = 680
display_w = 1320

black = (0,0,0)
grey = (192,192,192)
green = (0,200,0)
red = (200,0,0)
bright_green = (0,255,0)
yellow = (200,200,0)
bright_red = (255,0,0)
white = (255,255,255)

car_width = 77

csound = pygame.mixer.Sound("sound/crash.wav")
pygame.mixer.music.load("sound/jazz.wav")

gameD = pygame.display.set_mode((display_w, display_h))
pygame.display.set_caption('Watch Out')
clock = pygame.time.Clock()

imgroad = pygame.image.load('image/road.jpg').convert_alpha()
carimg = pygame.image.load('image/1.png').convert_alpha()
carimg1 = pygame.image.load('image/2.png').convert_alpha()
carimg2 = pygame.image.load('image/3.png').convert_alpha()
carimg3 = pygame.image.load('image/4.png').convert_alpha()
carimg4 = pygame.image.load('image/5.png').convert_alpha()
carimg5 = pygame.image.load('image/6.png').convert_alpha()

foo = [carimg1, carimg2, carimg3, carimg4, carimg5]

def button(msg, x, y, w, h, ic, ac, action = None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    
    if x+w > mouse[0] > x and y+h > mouse[1] > y:
        pygame.draw.rect(gameD, ac, (x,y,w,h))

        if click[0] == 1 and action != None:
            action()         
    else:
        pygame.draw.rect(gameD, ic, (x,y,w,h))

    smallText = pygame.font.SysFont("comicsansms", 20)
    textSurf, textRect = text_objects(msg, smallText)
    textRect.center = ((x+(w/2)), (y+(h/2)))
    gameD.blit(textSurf, textRect)

def quitgame():
    pygame.quit()

pause = False

def unpause():
    global pause
    pygame.mixer.music.unpause()
    pause=False

def crashed():
   pygame.mixer.music.stop()
   pygame.mixer.Sound.play(csound)
   gameD.fill(yellow)
   
   largeText = pygame.font.SysFont("comicsansms",115)
   TextSurf, TextRect = text_objects("You Crashed", largeText)
   TextRect.center = ((display_w/2),(display_h/2))
   gameD.blit(TextSurf, TextRect)

   while True:
        for event in pygame.event.get():            
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                

        button("Play Again",350,450,100,50,green,bright_green,gameloop)
        button("Quit",900,450,100,50,red,bright_red,quitgame)

        pygame.display.update()
        clock.tick(60)

def paused():
    pygame.mixer.music.pause()
    while pause:
        for event in pygame.event.get():            
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                
        gameD.fill(yellow)
        largeText = pygame.font.SysFont("comicsansms",115)
        TextSurf, TextRect = text_objects("Paused", largeText)
        TextRect.center = ((display_w/2),(display_h/2))
        gameD.blit(TextSurf, TextRect)

        button("Continue",350,450,100,50,green,bright_green,unpause)
        button("Quit",900,450,100,50,red,bright_red,quitgame)

        pygame.display.update()
        clock.tick(60)

def game_intro():
    intro = True

    while intro:
        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                
        gameD.fill(yellow)
        largeText = pygame.font.SysFont("comicsansms",115)
        TextSurf, TextRect = text_objects("Watch Out!", largeText)
        TextRect.center = ((display_w/2),(display_h/2))
        gameD.blit(TextSurf, TextRect)

        button("GO!",350,450,100,50,green,bright_green,gameloop)
        button("Quit",900,450,100,50,red,bright_red,quitgame)

        pygame.display.update()
        clock.tick(60)

def things_dodged(count):
    font=pygame.font.SysFont(None, 25)
    text=font.render("SCORE: "+ str(count), True, black)
    gameD.blit(text, (0,0))

def things(img, img1, img2, thingx, thingx1, thingx2, thingy, thingy1, thingy2):
    if thingx!=thingx1 and thingx!=thingx2 and thingx!=thingx1-2 and thingx!=thingx2+2 and thingx!=thingx1+3 and thingx!=thingx2-1:
        gameD.blit(img, (thingx, thingy))
    if thingx1!=thingx and thingx1!=thingx2 and thingx1!=thingx-2 and thingx1!=thingx2-1 and thingx1!=thingx+2 and thingx1!=thingx2+1:
        gameD.blit(img1, (thingx1, thingy1))
    if thingx2!=thingx and thingx2!=thingx1 and thingx2!=thingx-3 and thingx2!=thingx1-3 and thingx2!=thingx+1 and thingx2!=thingx1+1:
        gameD.blit(img2, (thingx2, thingy2))

def road(roady):
    gameD.blit(imgroad, (0, roady))
        
def car(x,y):
    gameD.blit(carimg,(x,y))

def text_objects(text, font):
    textsurface = font.render(text, True, black)
    return textsurface, textsurface.get_rect()

def message_display(text):
    largetext = pygame.font.Font('freesansbold.ttf', 115)
    textsurf, textrect = text_objects(text, largetext)
    textrect.center  = ((display_w/2), (display_h/2))
    
    gameD.blit(textsurf, textrect)
    pygame.display.update()
    
    time.sleep(2)
    gameloop()

def randimg():
    image=random.choice(foo)
    return image

def gameloop():
    global pause
    x = (display_w * 0.45)
    y = (display_h * 0.7)
    
    pygame.mixer.music.play(-1)
    gameexit = False
    
    x_change, y_change = 0, 0
    
    thing_startx = random.randrange(0, display_w)
    thing_starty = -600   
    thing_startx1 = random.randrange(0, display_w)
    thing_starty1 = -800 
    thing_startx2 = random.randrange(0, display_w)
    thing_starty2 = -900
    
    roady = 0
    roadyo = -680
    thing_speed = 7
    thing_width = 65
    thing_height = 130
    dodged=0
    
    while not gameexit:
        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x_change = -5
                elif event.key == pygame.K_RIGHT:
                    x_change = 5
                elif event.key == pygame.K_UP:
                    y_change = -5
                elif event.key == pygame.K_DOWN:
                    y_change = 5
                elif event.key==pygame.K_p:
                    pause=True
                    paused()
                    
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT or event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    x_change=0
                    y_change=0    
        x += x_change    
        y += y_change
        
        roady += 8
        if roady > display_h:
            roady = 0
            roadyo = -680
        if roady > 0:
            gameD.blit(imgroad, (0,roady))
            roadyo += 8
            road(roadyo)
        
        if thing_starty < -500:
            img = randimg() 

        if thing_starty1 < -600:
            img1 = randimg()

        if thing_starty2 < -700:
            img2 = randimg()

        things(img, img1, img2, thing_startx, thing_startx1, thing_startx2, thing_starty, thing_starty1, thing_starty2)
     
        thing_starty += thing_speed
        thing_starty1 += 10
        thing_starty2 += 13

        if thing_starty > display_h:
            thing_starty = 0 - thing_height
            thing_startx = random.randrange(0, display_w)
            img=random.choice(foo)    
            dodged += 1

        if thing_starty1 > display_h:
            thing_starty1 = 0 - thing_height
            thing_startx1 = random.randrange(0, display_w)
            img1=random.choice(foo)    
            dodged += 1

        if thing_starty2 > display_h:
            thing_starty2 = 0 - thing_height
            thing_startx2 = random.randrange(0, display_w)
            img2=random.choice(foo)    
            dodged += 1

        car(x,y)
        things_dodged(dodged)
        
        if x > display_w - car_width or x < 0 or y < 0 or y > display_h:
            crashed()
        
        if y < thing_starty + thing_height and y+155 > thing_starty:    
            if x >= thing_startx and x <= thing_startx + thing_width or x+car_width>=thing_startx and x+car_width<=thing_startx+thing_width:
                crashed()
        if y < thing_starty1 + thing_height and y+155 > thing_starty1:    
            if x >= thing_startx1 and x <= thing_startx1 + thing_width or x+car_width>=thing_startx1 and x+car_width<=thing_startx1+thing_width:
                crashed()
        if y < thing_starty2 + thing_height and y+155 > thing_starty2:    
            if x >= thing_startx2 and x <= thing_startx2 + thing_width or x+car_width>=thing_startx2 and x+car_width<=thing_startx2+thing_width:
                crashed()
                
        pygame.display.update()
        clock.tick(60)

game_intro()
gameloop()
pygame.quit()
quit()
