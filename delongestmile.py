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

# The Y value (pixels) of newly spawned projectiles will be between these values
INITIAL_PROJECTILE_Y_LOW  = 100
INITIAL_PROJECTILE_Y_HIGH = 500

# How heavy projectiles are at the beginning of the game
PROJECTILE_MASS_INITIAL = 5
# How much each additional level adds to the mass
PROJECTILE_MASS_INCREMENT = 5

# controls bouncieness of projectiles (between 0 and .99)
PROJECTILE_ELASTICITY = .5

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
        
        game.space.add(self.body, self.shape)
        
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
        game.space.remove(self.body, self.shape)
        game.objects.remove(self)
        
    
class RenderHandler():
    def render_all(self):
        ## Render background screen
        screen.blit(bg, (0, 0) )
        ## Draw objects and lines
        self.draw_objects()
        self.draw_lines()
        

        # display level
        label = font.render("Level " + str(game.current_level), 1, (255, 255, 255))
        dlabel = font.render("Dodged %i Delongs so far"%game.dodged_objects, 1, (255, 255, 255))
        
        #### controls
        clabel1 = font.render("Left arrow (keep tapping): move left", 1, (255, 255, 255))
        clabel2 = font.render("Up / down arrows: awkwardly rotate", 1, (255, 255, 255))
        clabel3 = font.render("Space: Jump", 1, (255, 255, 255))
        clabel4 = font.render("Escape: Admit defeat / return to main menu", 1, (255, 255, 255))
        
        # Blitting
        screen.blit(label, (25, 50))
        screen.blit(dlabel, (25, 70))
        #screen.blit(tlabel, (int(SCREEN_WIDTH/2), 65))
        
        screen.blit(clabel1, (25, 130))
        screen.blit(clabel2, (25, 150))
        screen.blit(clabel3, (25, 170))
        screen.blit(clabel4, (25, 190))
            
        
        pygame.display.flip()    
    
    def draw_lines(self):
        ''' Draw any lines in the "lines" list '''
        for line in game.lines:
            body = line.body
            pv1 = body.position + line.a.rotated(body.angle)
            pv2 = body.position + line.b.rotated(body.angle)
            p1 = to_pygame(pv1.x, pv1.y)
            p2 = to_pygame(pv2.x, pv2.y)
            pygame.draw.lines(screen, THECOLORS["gray"], False, [p1, p2])

        
    def draw_objects(self):
        objects_to_remove = []
        for obj in game.objects:
            if obj.body.position.y < -500:
                objects_to_remove.append(obj)
            
            obj.draw()
        
        for obj in objects_to_remove:
            obj.remove()
            game.dodged_objects += 1
        
    
class InputHandler():
    
    def handle_keys(self):
        ''' Handle keypresses during game '''
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_LEFT:				
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
                
    def handle_level_begin(self):
        ''' Shorter function to wait on some basic user input'''
        while 1:
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_LEFT or K_SPACE:
                        return
                elif event.type == QUIT:
                    return
    
    
class GameWorld:
    def __init__(self):        
        self.objects = []
        self.lines = []
        
        self.current_level = 1
        self.dodged_objects = 0
        
        
    def start_level(self):
        global player
        
        self.lines = [] 
        self.objects = []
        
        self.space = None
        self.space = pymunk.Space()
        self.space._set_gravity((GRAV_DOWN, GRAV_RIGHT))
        
        # Horizontal
        self.add_line(-100, -15, SCREEN_WIDTH+100, -15, visible=1)
        # Vertical
        #add_line(25, 250, 25, SCREEN_HEIGHT * 2, visible=1)
        
        player = self.add_object(x=1000, y=100, mass=100, sprite='josh_and_body.png')
        player.body.velocity[0] = -150        
        
        render_handler.render_all()
        if self.current_level == 1:
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
        
        input_handler.handle_level_begin()
            
        
        
    def spawn_projectile(self, image):
        ''' Handles spawning a projectile (in this case, Delong) '''
        y = random.randint(INITIAL_PROJECTILE_Y_LOW, INITIAL_PROJECTILE_Y_HIGH)

        mass = PROJECTILE_MASS_INITIAL + (PROJECTILE_MASS_INCREMENT * (game.current_level-1))
        
        sprite_size = 1
        
        projectile = self.add_object(x=-50, y=y, mass=mass, sprite=image, sprite_size=sprite_size)
        projectile.body.velocity[0] = random.randint(400, 550)
        projectile.body.velocity[1] = random.randint(15, 150)
        projectile.body.angular_velocity = ( random.choice([-10, -9, -8, -7, -6, -5, 5, 6, 7, 8, 9, 10]) )
        
        projectile.shape._set_elasticity(PROJECTILE_ELASTICITY)
            
        return projectile
        
    def add_object(self, x, y, mass, sprite, sprite_size=None):
        ''' Adds an object to the game space '''
        obj = GObject(self.space, x, y, mass,  sprite, sprite_size)
        self.objects.append(obj)
    
        return obj
    
    def add_line(self, x1, y1, x2, y2, visible=1):
        ''' Adds a solid line to the game space. Used to set the floor in the current version '''
        body = pymunk.Body()
        line = pymunk.Segment(body, (x1, y1), (x2, y2), 10)
        line.radius = 20
        line.friction = .6
        
        # Hack to prevent lines from rendering if they're not marked as visible
        if visible:
            self.lines.append(line)
            
        self.space.add(line)

    def check_for_spawn_based_on_level(self):
        if random.randint(1, 1000) <= 75 + ((self.current_level+4)**2):
            obj = 'delong.png'
            self.spawn_projectile(obj)
        
    
    
def main():
    global clock, bg, player
    global screen, font, game, input_handler, render_handler
    
    pygame.init()
    font = pygame.font.Font("freesansbold.ttf", 16) 
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("DeLongest Mile")
    
    bg = pygame.image.load(os.path.join('assets', 'tyemill.jpg'))
    bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT) )

    input_handler = InputHandler()
    render_handler = RenderHandler()
    game = GameWorld()
    
    
    bg = pygame.image.load(os.path.join('assets', 'tyemill.jpg'))
    bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT) )
    
    clock = pygame.time.Clock()
    
    
    game.start_level()
    
    exit_game = False
    while not exit_game:
        
        #spawn stuff
        game.check_for_spawn_based_on_level()
        # Handle keys and check for exit
        exit_game = input_handler.handle_keys()
        # Render the screen
        render_handler.render_all()
        
        # Advance game pace
        game.space.step(1/50.0)
        clock.tick(50)	

        # Level is won!
        if player.body.position[0] < 200:
            for obj in game.objects[:]:
                if obj != player:
                    game.dodged_objects += 1

            # Display win text
            label = font.render('Level {0} complete'.format(game.current_level), 1, (255, 255, 255))
            screen.blit(label, (SCREEN_WIDTH/2, 100))
            pygame.display.flip()
            time.sleep(1.5)
            
            # Clear the event buffer
            for event in pygame.event.get():
                pass
            
            llabel = font.render('Press left arrow to begin next level', 1, (255, 255, 255))
            screen.blit(llabel, (SCREEN_WIDTH/2, 120))
            pygame.display.flip()

            game.current_level += 1
            game.start_level()
            
        # Level is lost!
        elif player.body.position[0] > SCREEN_WIDTH + GRACE_ZONE:
            label = font.render('Delong got the better of you.', 1, (255, 255, 255))
            label2 = font.render('Press Left arrow to restart from Level 1', 1, (255, 255, 255))
            screen.blit(label, (SCREEN_WIDTH/2, 100))
            screen.blit(label2, (SCREEN_WIDTH/2, 150))
            pygame.display.flip()
            
            game.current_level = 1
            game.dodged_objects = 0
            game.start_level()
    
if __name__ == '__main__':
    #sys.exit(main())
    sys.exit(main())
