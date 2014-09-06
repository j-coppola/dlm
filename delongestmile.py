from __future__ import division
import sys, random
import pygame
from pygame.locals import *
from pygame.color import *
import pymunk 
from pymunk import Vec2d
import math
import os
import time


SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700

PYMUNK_Y_OFFSET = SCREEN_HEIGHT # No idea 

# How far off to the right of the screen you can go before losing (in pixels)
GRACE_ZONE = 250

# Default friction for objects
DEFAULT_FRICTION_AMT = .5

# Downward gravity (negative will cause things to drop upwards)
GRAV_DOWN = 200
# Left / right gravity (negative is right)
GRAV_RIGHT = -300

# Gravity on the menu screen
MENU_GRAV = -50

# Determines the size of my face on the title screen
MIN_STAREJOSH_FACTOR = 5
MAX_STAREJOSH_FACTOR = 40


def to_pygame(x, y):
    """Small hack to convert pymunk to pygame coordinates"""
    return x, -y + PYMUNK_Y_OFFSET

    
def load_image(name):
    # From http://www.pygame.org/docs/tut/chimp/ChimpLineByLine.html
    fullname = os.path.join('assets', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error, message:
        print 'Cannot load image:', name
        raise SystemExit, message
    image = image.convert_alpha()
    return image, image.get_rect()
    
        
class GObject(pygame.sprite.Sprite):
    ''' An object in the game '''
    def __init__(self, space, x, y, mass, sprite, sprite_size=None):
        pygame.sprite.Sprite.__init__(self)
    
        self.image, self.rect = load_image(sprite)
        
        # This is not exactly an ideal way to figure this out
        self.width = self.rect[2]
        self.height = self.rect[3]
        
        # This will resize the sprite if we've resized it
        if sprite_size:
            self.image = pygame.transform.scale(self.image, (self.width * sprite_size, self.height * sprite_size) )
    
        self.space = space
        self.mass = mass
        
        ## Need to offset the points of the shape so that the center of the image is at (0, 0)		
        offset = Vec2d(self.width/2, self.height/2)
        
        bounds = self.rect
        points = [Vec2d(bounds.topleft) - offset, Vec2d(bounds.topright) - offset, Vec2d(bounds.bottomright) - offset, Vec2d(bounds.bottomleft) - offset] 
        #### End of shape offset code - we can now pass the points to the body/shape creation ####

        inertia = pymunk.moment_for_poly(mass, points, (0,0))
        self.body = pymunk.Body(mass, inertia)
        self.body.position = x, y
    
        self.shape = pymunk.Poly(self.body, points, (0, 0) )
        self.shape.friction = DEFAULT_FRICTION_AMT
        
        space.add(self.body, self.shape)
        
    def draw(self):	
        ''' Took me 6 goddamn days to get this code correct... '''		
        p = self.body.position
        p = Vec2d(to_pygame(p.x, p.y))
        
        angle_degrees = math.degrees(self.body.angle)
        rotated_img = pygame.transform.rotate(self.image, angle_degrees)
        
        offset = Vec2d(rotated_img.get_size() ) / 2
        p = p - offset
        
        screen.blit(rotated_img, p)
        
    def remove(self):
        space.remove(self.body, self.shape)
        objects.remove(self)


def add_line(space, x1, y1, x2, y2, visible=1):
    ''' Adds a solid line to the game space. Used to set the floor in the current version '''
    body = pymunk.Body()
    line = pymunk.Segment(body, (x1, y1), (x2, y2), 10)
    line.radius = 20
    line.friction = .6
    
    # Hack to prevent lines from rendering if they're not marked as visible
    if visible:
        lines.append(line)
        
    space.add(line)
    
    
def add_object(space, x, y, mass, sprite, sprite_size=None):
    ''' Adds an object to the game space '''
    obj = GObject(space, x, y, mass,  sprite, sprite_size)
    objects.append( obj )
    
    return obj
    
    
def draw_lines(screen, lines):
    ''' Draw any lines in the "lines" list '''
    for line in lines:
        body = line.body
        pv1 = body.position + line.a.rotated(body.angle)
        pv2 = body.position + line.b.rotated(body.angle)
        p1 = to_pygame(pv1.x, pv1.y)
        p2 = to_pygame(pv2.x, pv2.y)
        pygame.draw.lines(screen, THECOLORS["gray"], False, [p1, p2])

        
def draw_objects():
    global dodged_objects
    objects_to_remove = []
    for obj in objects:
        if obj.body.position.y < -500:
            objects_to_remove.append(obj)
        
        obj.draw()
    
    for obj in objects_to_remove:
        obj.remove()
        if game_state == 'mri':
            dodged_objects += 1
        

def figure_out_taunt_message():
    
    posx = player.body.position[0]
    
    xmsg = ''
    
    if posx < -95:
        xmsg = ''
    elif posx < 0:
        xmsg = 'Amost...'
    elif posx < 200:
        xmsg = 'So close!'
    elif posx < 400:
        xmsg = 'You can do it!'
    elif posx < 1000:
        xmsg = 'Keep moving towards the computer!'
    elif posx > 1000:
        xmsg = 'Too close for comfort...'
    elif posx > 800:
        xmsg = 'Oh no!'
    elif posx > 1150:
        xmsg = ''
    
    return xmsg
        
def render_all():
    ## Render background screen
    screen.blit(bg, (0, 0) )
    ## Draw objects and lines
    draw_objects()
    draw_lines(screen, lines)
    
    if game_state == 'mri':
        # display level
        label = font.render("Level " + str(current_level), 1, (255, 255, 255))
        dlabel = font.render("Dodged %i Delongs so far"%dodged_objects, 1, (255, 255, 255))
        
        xmsg = figure_out_taunt_message()
        tlabel = font.render(xmsg, 1, (255, 255, 255))
        
        #### controls
        clabel1 = font.render("Left arrow (keep tapping): move left", 1, (255, 255, 255))
        clabel2 = font.render("Up / down arrows: awkwardly rotate", 1, (255, 255, 255))
        clabel3 = font.render("Space: Jump", 1, (255, 255, 255))
        clabel4 = font.render("Escape: Admit defeat / return to main menu", 1, (255, 255, 255))
        
        # Blitting
        screen.blit(label, (25, 50))
        screen.blit(dlabel, (25, 70))
        screen.blit(tlabel, (int(SCREEN_WIDTH/2), 65))
        
        screen.blit(clabel1, (25, 130))
        screen.blit(clabel2, (25, 150))
        screen.blit(clabel3, (25, 170))
        screen.blit(clabel4, (25, 190))
        
        
    elif game_state == 'main menu':
        label = font.render("Press g to play the game!", 1, (255, 255, 255))
        screen.blit(label, (700, 550))
        
        label2 = font.render("(Or click and drag and see what happens)", 1, (255, 255, 255))
        screen.blit(label2, (700, 600))
    
    pygame.display.flip()
    
def handle_keys():
    global spawn_objects, game_state
    
    if game_state == 'main menu':
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                spawn_objects = True
            elif event.type == pygame.MOUSEBUTTONUP:
                spawn_objects = False			
            
            elif event.type == KEYDOWN and event.key == K_g:
                game_state == 'mri'
                play_mri()
            
            
            if spawn_objects:
                mx, my = pygame.mouse.get_pos()
                mx, my = to_pygame(mx, my)
                ## Add obj
                mass = 1
                #radius = 64
                sprite = random.choice(['josh.png', 'delong.png'])
                add_object(space, mx, my, mass, sprite)			
            # Huh?
            elif event.type == QUIT:
                return True
            # Exit on escape
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                return True
                
    ##############################################################
    elif game_state == 'mri':
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                spawn_objects = True
            elif event.type == pygame.MOUSEBUTTONUP:
                spawn_objects = False			
                
            elif event.type == KEYDOWN and event.key == K_LEFT:				
                if player.body.velocity[0] > -125:
                    player.body.velocity[0] -= 150
                
            elif event.type == KEYDOWN and event.key == K_RIGHT:
                if player.body.velocity[0] < 125:
                    player.body.velocity[0] += 150
                    
            elif event.type == KEYDOWN and event.key == K_UP:
                if player.body.angular_velocity > -8:
                    player.body.angular_velocity -= 3		
                
            elif event.type == KEYDOWN and event.key == K_DOWN:
                if player.body.angular_velocity < 8:
                    player.body.angular_velocity += 3
            
            elif event.type == KEYDOWN and event.key == K_SPACE:
                points = player.shape.get_points()
                if points[2][1] <= 100 and points[3][1] <= 100:
                    player.body.velocity[1] += 250
                
            # Huh?
            elif event.type == QUIT:
                return True
            # Exit on escape
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                return True
                
               
        
def play_mri():
    global objects, lines, space, clock, spawn_objects, game_state, mri_mach, bg, player, current_level, dodged_objects
    game_state = 'mri'
    current_level = 1
    dodged_objects = 0
    
    bg = pygame.image.load(os.path.join('assets', 'tyemill.jpg'))
    bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT) )
    
    clock = pygame.time.Clock()
    
    start_level()
    
    render_all()
    ## Text
    des1 = 'Oh no! I just realized I forgot to lock my computer!'
    des2 = 'Move towards my desk by repeatedly tapping the left arrow key!'
    des3 = 'Awkwardly spin me by pressing up or down arrow keys!'
    des4 = 'Press the spacebar to dodge incoming Delongs when you are near the ground!'
    descs = [des1, des2, des3, des4, '', 'Press left arrow to begin! (Escape will exit to menu)']
    for i, line in enumerate(descs):
        label = font.render(line, 1, (200, 50, 50))
        screen.blit(label, (400, 100+(i*50)))
    
    pygame.display.flip()
    
    exit_loop = False
    while not exit_loop:	
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_LEFT:
                exit_loop = True
            elif event.type == QUIT:
                exit_loop = True
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                exit_loop = True
                
        time.sleep(.1)
    ##################################	
    
    spawn_objects = False
    exit_game = False
    while not exit_game:
        #spawn stuff
        check_for_spawn_based_on_level(current_level)
        # Handle keys and check for exit
        exit_game = handle_keys()
        # Render the screen
        render_all()
        
        # Advance game pace
        space.step(1/50.0)
        #pygame.display.flip()
        clock.tick(50)	

        # Level is won!
        if player.body.position[0] < 200:
            for obj in objects[:]:
                if obj != player:
                    dodged_objects += 1

            # Display win text
            label = font.render('Level ' + str(current_level) + ' complete', 1, (255, 255, 255))
            screen.blit(label, (SCREEN_WIDTH/2, 100))
            pygame.display.flip()
            time.sleep(1.5)
            
            # Clear the event buffer
            for event in pygame.event.get():
                pass
            
            
            llabel = font.render('Press left arrow to begin next level', 1, (255, 255, 255))
            screen.blit(llabel, (SCREEN_WIDTH/2, 120))
            pygame.display.flip()
            # Wait for user input to continue
            break_out = 0
            while not break_out:
                for event in pygame.event.get():
                    if event.type == KEYDOWN and event.key == K_LEFT:
                        break_out = 1
                        break
            
            
            current_level += 1
            start_level()
            
        # Level is lost!
        elif player.body.position[0] > SCREEN_WIDTH + GRACE_ZONE:
            label = font.render('Delong got the better of you. Press Left arrow to restart from Level 1', 1, (255, 255, 255))
            screen.blit(label, (SCREEN_WIDTH/2, 100))
            pygame.display.flip()
            
            # Wait for user input to continue
            break_out = 0
            while not break_out:
                for event in pygame.event.get():
                    if event.type == KEYDOWN and event.key == K_LEFT:
                        break_out = 1
                        break
            
            current_level = 1
            dodged_objects = 0
            start_level()
            
    setup_main()
    
def start_level():
    global space, lines, objects, player
    
    
    space = pymunk.Space()
    space.gravity = (GRAV_DOWN, GRAV_RIGHT)
    
    lines = []
    # Horizontal
    add_line(space, -100, -15, SCREEN_WIDTH+100, -15, visible=1)
    # Vertical
    #add_line(space, 25, 250, 25, SCREEN_HEIGHT * 2, visible=1)
    
    objects = []
    player = add_object(space=space, x=1000, y=100, mass=100, sprite='josh_and_body.png')
    player.body.velocity[0] = -150
    
            
def check_for_spawn_based_on_level(level):
    if random.randint(1, 1000) <= 75 + ((level+4)**2):
        #####
        obj = 'delong.png'
        spawn_projectile(obj)
    
def spawn_projectile(image):
    y = random.randint(100, 500)

    mass = 15 + (10 * current_level)
    
    sprite_size = 1
    
    projectile = add_object(space=space, x=-50, y=y, mass=mass, sprite=image, sprite_size=sprite_size)
    projectile.body.velocity[0] = random.randint(400, 550)
    projectile.body.velocity[1] = random.randint(15, 150)
    projectile.body.angular_velocity = ( random.choice([-10, -9, -8, -7, -6, -5, 5, 6, 7, 8, 9, 10]) )
    
    projectile.shape._set_elasticity(random.randint(1, 99)/100)
        
    return projectile
    
def spawn_menu_josh(x, y):
    mass = random.randint(20, 75)
    
    sprite_size = random.randint(MIN_STAREJOSH_FACTOR, MAX_STAREJOSH_FACTOR)
    sprite_size = int(sprite_size/10)

    sprite = 'josh.png'
    add_object(space, x, y, mass, sprite, sprite_size)

def setup_main():
    global screen, bg, objects, lines, space, clock, spawn_objects, game_state, font
    
    game_state = 'main menu'
    
    bg = pygame.image.load(os.path.join('assets', 'tyemill.jpg'))
    bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT) )
    
    ## For menu background ##
    clock = pygame.time.Clock()
    
    space = pymunk.Space()
    space.gravity = (0.0, MENU_GRAV)
    
    lines = []
    objects = []
    
    spawn_objects = False
    ## Add some copies of my face to stare at you and fall down the menu screen
    for i in xrange(5):
        x, y = ( random.randint(0, SCREEN_WIDTH), random.randint(100, SCREEN_HEIGHT-100) )
        x, y = to_pygame(x, y)
        spawn_menu_josh(x, y)
    
def main():
    global screen, bg, objects, lines, space, clock, spawn_objects, game_state, font
    
    pygame.init()
    font = pygame.font.Font("freesansbold.ttf", 16) 
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Delongestmile")
    
    setup_main()
    
    exit_game = False
    
    while not exit_game:
        # Spawn some joshes
        if random.randint(0, 100) > 95:
            x, y = ( random.randint(0, SCREEN_WIDTH), -300 )
            x, y = to_pygame(x, y)
            ## Add obj
            spawn_menu_josh(x, y)
    
        # Handle keys and check for exit
        exit_game = handle_keys()
        # Render the screen
        render_all()
        
        # Advance game pace
        space.step(1/50.0)
        #pygame.display.flip()
        clock.tick(50)
    
        
if __name__ == '__main__':
    sys.exit(main())
