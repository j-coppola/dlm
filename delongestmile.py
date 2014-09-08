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
import ConfigParser


TEXT_COLOR_MAIN = (255, 255, 255)


config = ConfigParser.ConfigParser()
config.read('delongestmile.ini')

################## BASIC GAME PARAMETERS ######################
SCREEN_WIDTH = int(config.get('game', 'SCREEN_WIDTH'))
SCREEN_HEIGHT = int(config.get('game', 'SCREEN_HEIGHT'))

PLAY_MUSIC = config.getboolean('game', 'PLAY_MUSIC')

# How far off to the right of the screen you can go before losing (in pixels)
GRACE_ZONE = int(config.get('game', 'GRACE_ZONE'))

# Default friction for objects
DEFAULT_FRICTION_AMT = float(config.get('game', 'DEFAULT_FRICTION_AMT'))

# Downward gravity (negative will cause things to drop upwards)
GRAV_VERT = int(config.get('game', 'GRAV_VERT'))
# Left / right gravity (negative is right)
GRAV_HORIZ = int(config.get('game', 'GRAV_HORIZ'))

############## PROJECTILE PARAMETERS ###########################
# Every tick, the game rolls a number between 1 and 1000. 
# If the number is less than (PROJECTILE_SPAWN_CHANCE_BASE + (<current level> * PROJECTILE_SPAWN_CHANCE_LEVEL),
# a projectile is spawned. 
PROJECTILE_SPAWN_CHANCE_BASE  = int(config.get('projectile', 'PROJECTILE_SPAWN_CHANCE_BASE'))
PROJECTILE_SPAWN_CHANCE_LEVEL = int(config.get('projectile', 'PROJECTILE_SPAWN_CHANCE_LEVEL'))

# The Y value (pixels) of newly spawned projectiles will be between these values
PROJECTILE_INITIAL_Y_LOW  = int(config.get('projectile', 'PROJECTILE_INITIAL_Y_LOW'))
PROJECTILE_INITIAL_Y_HIGH = int(config.get('projectile', 'PROJECTILE_INITIAL_Y_HIGH'))

# How heavy projectiles are at the beginning of the game
PROJECTILE_MASS_INITIAL = float(config.get('projectile', 'PROJECTILE_MASS_INITIAL'))
# How much each additional level adds to the mass
PROJECTILE_MASS_INCREMENT = float(config.get('projectile', 'PROJECTILE_MASS_INCREMENT'))

# controls bouncieness of projectiles (between 0 and .99)
PROJECTILE_ELASTICITY = float(config.get('projectile', 'PROJECTILE_ELASTICITY'))

# Base size of projectile
PROJECTILE_SIZE_BASE = float(config.get('projectile', 'PROJECTILE_SIZE_BASE'))
# How much each additional level adds onto the base projectile size (decimals OK)
PROJECTILE_SIZE_LEVEL_MODIFIER = float(config.get('projectile', 'PROJECTILE_SIZE_LEVEL_MODIFIER'))

# Controls the starting velocity of projectiles (picks a random integer between the high and low values)
PROJECTILE_X_VELOCITY_LOW  = int(config.get('projectile', 'PROJECTILE_X_VELOCITY_LOW'))
PROJECTILE_X_VELOCITY_HIGH = int(config.get('projectile', 'PROJECTILE_X_VELOCITY_HIGH'))

PROJECTILE_Y_VELOCITY_LOW  = int(config.get('projectile', 'PROJECTILE_Y_VELOCITY_LOW'))
PROJECTILE_Y_VELOCITY_HIGH = int(config.get('projectile', 'PROJECTILE_Y_VELOCITY_HIGH'))

############# PLAYER PARAMETERS ###################################
# Starting X velocity of the player (negative is left)
PLAYER_STARTING_VELOCITY = int(config.get('player', 'PLAYER_STARTING_VELOCITY'))

PLAYER_VELOCITY_SIDEWAYS_MAX = int(config.get('player', 'PLAYER_VELOCITY_SIDEWAYS_MAX'))
# Max angular velocity
PLAYER_VELOCITY_ANGULAR_MAX = int(config.get('player', 'PLAYER_VELOCITY_ANGULAR_MAX'))
# How much angular velocity each click of the rotate buttons will cause
PLAYER_VELOCITY_ANGULAR_AMT = int(config.get('player', 'PLAYER_VELOCITY_ANGULAR_AMT'))

# Velocity of dashing (ignores the sideways max velocity)
PLAYER_VELOCITY_DASH_X = -700
PLAYER_VELOCITY_DASH_Y = 100

# How close to the ground your feet have to be to jump (pixels)
PLAYER_JUMP_THRESHHOLD = int(config.get('player', 'PLAYER_JUMP_THRESHHOLD'))
# How much verticle velocity a jump adds
PLAYER_VELOCITY_JUMP_AMT = int(config.get('player', 'PLAYER_VELOCITY_JUMP_AMT'))

PLAYER_MASS = int(config.get('player', 'PLAYER_MASS'))

# Amount of energy player starts with
PLAYER_ENERGY_START = float(config.get('player', 'PLAYER_ENERGY_START'))

# How much energy the player gets each tick
PLAYER_ENERGY_PER_TICK = float(config.get('player', 'PLAYER_ENERGY_PER_TICK'))

# Maximum amount of energy the player is allowed
PLAYER_ENERGY_MAX = float(config.get('player', 'PLAYER_ENERGY_MAX'))

# How much energy it costs to move
PLAYER_ENERGY_MOVE_COST = float(config.get('player', 'PLAYER_ENERGY_MOVE_COST'))

# How much energy it costs to rotate
PLAYER_ENERGY_SPIN_COST = float(config.get('player', 'PLAYER_ENERGY_SPIN_COST'))

# How much energy it costs to rotate
PLAYER_ENERGY_JUMP_COST = float(config.get('player', 'PLAYER_ENERGY_JUMP_COST'))

# How much energy the "dash" move costs
PLAYER_ENERGY_DASH_COST = float(config.get('player', 'PLAYER_ENERGY_DASH_COST'))


def pymunk_to_pygame(x, y):
    """Small hack to convert pymunk to pygame coordinates"""
    return x, -y + SCREEN_HEIGHT

    
def load_image(path):
    # Adapted from http://www.pygame.org/docs/tut/chimp/ChimpLineByLine.html
    try:
        image = pygame.image.load(path)
        
    except pygame.error, message:
        print 'Cannot load image:', path
        raise SystemExit, message
        
    image = image.convert_alpha()
    
    return image, image.get_rect()
    
        
class GameObject(pygame.sprite.Sprite):
    ''' An object in the game '''
    def __init__(self, space, x, y, mass, sprite, sprite_size=1):
        pygame.sprite.Sprite.__init__(self)
    
        self.image, self.rect = load_image(sprite)
        
        # This is not exactly an ideal way to figure this out
        self.width = self.rect[2]
        self.height = self.rect[3]
        
        # This will resize the sprite if we've resized it
        self.image = pygame.transform.scale(self.image, (int(self.width * sprite_size), int(self.height * sprite_size) ))
    
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
        p = Vec2d(pymunk_to_pygame(p.x, p.y))
        
        angle_degrees = math.degrees(self.body.angle)
        rotated_img = pygame.transform.rotate(self.image, angle_degrees)
        
        offset = Vec2d(rotated_img.get_size() ) / 2
        p = p - offset
        
        screen.blit(rotated_img, p)
        
    def remove(self):
        game.space.remove(self.body, self.shape)
        game.objects.remove(self)
        
    
class RenderHandler():
    ''' Handles rendering-related functions '''
    def render_all(self):
        ## Render background screen
        screen.blit(bg, (0, 0) )
        ## Draw objects and lines
        self.draw_objects()
        self.draw_lines()
        
        
        # display level
        label = font.render("Level " + str(game.current_level), 1, TEXT_COLOR_MAIN)
        dlabel = font.render("Dodged %i Delongs so far"%game.dodged_objects, 1, TEXT_COLOR_MAIN)
        
        # controls
        clabel1 = font.render("Left arrow (mash): move left", 1, TEXT_COLOR_MAIN)
        clabel2 = font.render("Up / down arrows: rotate", 1, TEXT_COLOR_MAIN)
        clabel3 = font.render("Space: Jump", 1, TEXT_COLOR_MAIN)
        if game.player_energy >= PLAYER_ENERGY_DASH_COST:
            clabel4 = font.render("Energy: {0} CTRL to dash!".format(int(game.player_energy)), 1, (180, 180, 255) )
        else:
            clabel4 = font.render("Energy: {0}".format(int(game.player_energy)), 1, (180, 180, 180) )
            
        
        clabel5 = font.render("Escape: Quit!", 1, TEXT_COLOR_MAIN)
        
        # Blitting
        screen.blit(label, (int(SCREEN_WIDTH/2), 10))
        screen.blit(dlabel, (30, 30))
        
        screen.blit(clabel1, (30, 70))
        screen.blit(clabel2, (30, 95))
        screen.blit(clabel3, (30, 120))
        screen.blit(clabel4, (30, 150))
        screen.blit(clabel5, (SCREEN_WIDTH-200, 10))
            
        
        pygame.display.flip()    
    
    def draw_lines(self):
        ''' Draw any lines in the "lines" list '''
        for line in game.lines:
            body = line.body
            pv1 = body.position + line.a.rotated(body.angle)
            pv2 = body.position + line.b.rotated(body.angle)
            p1 = pymunk_to_pygame(pv1.x, pv1.y)
            p2 = pymunk_to_pygame(pv2.x, pv2.y)
            pygame.draw.lines(screen, THECOLORS["gray"], False, [p1, p2])

        
    def draw_objects(self):
        objects_to_remove = []
        for obj in game.objects:
            # Remove objs who get too far offscreen
            if obj.body.position.y < -500:
                objects_to_remove.append(obj)
            
            obj.draw()
        
        for obj in objects_to_remove:
            obj.remove()
            game.dodged_objects += 1
        
        
    def flash_text(self, text):
        # Display win text - make it flash in a few different colors
        for color in ( TEXT_COLOR_MAIN, (200, 50, 50), (200, 200, 50), TEXT_COLOR_MAIN, (200, 50, 50), (200, 200, 50), TEXT_COLOR_MAIN, (200, 50, 50), (200, 200, 50)  ):
            label = font.render(text, 1, color)
            screen.blit(label, (int(SCREEN_WIDTH/2)-100, 100))
            pygame.display.flip()
            time.sleep(.075)
    
class InputHandler():
    
    def handle_keys(self):
        ''' Handle keypresses during game '''
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_LEFT:
                game.adjust_player_energy(-PLAYER_ENERGY_MOVE_COST)
                if player.body.velocity[0] > -PLAYER_VELOCITY_SIDEWAYS_MAX:
                    player.body.velocity[0] -= PLAYER_VELOCITY_SIDEWAYS_MAX
                
            elif event.type == KEYDOWN and event.key == K_RIGHT:
                game.adjust_player_energy(-PLAYER_ENERGY_MOVE_COST)
                if player.body.velocity[0] < PLAYER_VELOCITY_SIDEWAYS_MAX:
                    player.body.velocity[0] += PLAYER_VELOCITY_SIDEWAYS_MAX
                    
            elif event.type == KEYDOWN and event.key == K_UP:
                game.adjust_player_energy(-PLAYER_ENERGY_SPIN_COST)
                if player.body.angular_velocity > -PLAYER_VELOCITY_ANGULAR_MAX:
                    player.body.angular_velocity -= PLAYER_VELOCITY_ANGULAR_AMT
                
            elif event.type == KEYDOWN and event.key == K_DOWN:
                game.adjust_player_energy(-PLAYER_ENERGY_SPIN_COST)
                if player.body.angular_velocity < PLAYER_VELOCITY_ANGULAR_MAX:
                    player.body.angular_velocity += PLAYER_VELOCITY_ANGULAR_AMT
            
            elif event.type == KEYDOWN and event.key == K_SPACE:
                points = player.shape.get_points()
                if points[2][1] <= 100 and points[3][1] <= PLAYER_JUMP_THRESHHOLD:
                    game.adjust_player_energy(-PLAYER_ENERGY_JUMP_COST)
                    player.body.velocity[1] += PLAYER_VELOCITY_JUMP_AMT
                    
                    
            if event.type == KEYDOWN and (event.key == K_LCTRL or event.key == K_RCTRL) and game.player_energy >= PLAYER_ENERGY_DASH_COST:
                game.adjust_player_energy(-PLAYER_ENERGY_DASH_COST)
                player.body.velocity[0] = PLAYER_VELOCITY_DASH_X
                player.body.velocity[1] = PLAYER_VELOCITY_DASH_Y
                
                
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
        
        self.player_energy = PLAYER_ENERGY_START
        
        # Find all files in the projectiles folder (non-images would cause a crash for now). These will be randomly chosen from
        self.projectiles = [os.path.join('assets', 'projectiles', img) for img in os.listdir(os.path.join('assets', 'projectiles'))]
        # Same for music files
        self.music_files = [os.path.join('assets', 'music', music_file) for music_file in os.listdir(os.path.join('assets', 'music'))]
        
        
    def start_level(self):
        global player
        
        # Make sure the event buffer is clear
        for event in pygame.event.get():
            pass
        
        
        self.lines = [] 
        self.objects = []
        
        self.space = None
        self.space = pymunk.Space()
        self.space._set_gravity((GRAV_VERT, GRAV_HORIZ))
        
        # Horizontal
        self.add_line(-100, -15, SCREEN_WIDTH+100, -15, visible=1)
        # Vertical
        #add_line(25, 250, 25, SCREEN_HEIGHT * 2, visible=1)
        
        player = self.add_object(x=SCREEN_WIDTH-200, y=100, mass=PLAYER_MASS, sprite=os.path.join('assets', 'player.png'))
        player.body.velocity[0] = PLAYER_STARTING_VELOCITY        
        
        render_handler.render_all()
        if self.current_level == 1:
            # Start music
            if PLAY_MUSIC:
                pygame.mixer.music.load(random.choice(self.music_files))
                pygame.mixer.music.play(-1)
            
            # Black background rectangle - first tuple is color, second is (x y width height), last argument is rect border (0 for totally filled in)
            pygame.draw.rect(screen, (0, 0, 0), (325, 40, 625, 300), 0)
            # Render some descriptive text on the first level
            des1 = 'Oh no! I just realized I forgot to lock my computer!'
            des2 = 'Move towards my desk by mashing the left arrow key!'
            des3 = 'Awkwardly spin me by pressing up or down arrow keys!'
            des4 = 'Press the spacebar to jump when you are near the ground!'
            descs = [des1, des2, des3, des4, '', 'Beware: Delongs increase in number and mass each level!',  '', 'Press left arrow to begin! (Escape to exit)']
            for i, line in enumerate(descs):
                label = font.render(line, 1, (200, 50, 50))
                screen.blit(label, (350, 60+(i*30)))
        
            pygame.display.flip()
        
        else:
            # Black background rectangle - first tuple is color, second is (x y width height), last argument is rect border (0 for totally filled in)
            pygame.draw.rect(screen, (0, 0, 0), (int(SCREEN_WIDTH/2)-225, 95, 475, 100), 0)
            llabel = font.render('Press left arrow to begin next level', 1, TEXT_COLOR_MAIN)
            screen.blit(llabel, (int(SCREEN_WIDTH/2)-200, 120))
            pygame.display.flip()
        # Wait for user input to begin the level    
        input_handler.handle_level_begin()
            
            
    def end_level(self):
        for obj in self.objects[:]:
            if obj != player:
                self.dodged_objects += 1
        
        # Will cause the Delongs dodged count to go up
        render_handler.render_all()
            
        
    def spawn_projectile(self, image):
        ''' Handles spawning a projectile (in this case, Delong) '''
        y = random.randint(PROJECTILE_INITIAL_Y_LOW, PROJECTILE_INITIAL_Y_HIGH)

        mass = PROJECTILE_MASS_INITIAL + (PROJECTILE_MASS_INCREMENT * (game.current_level-1))
        
        sprite_size = PROJECTILE_SIZE_BASE + (PROJECTILE_SIZE_LEVEL_MODIFIER * game.current_level)
        
        projectile = self.add_object(x=-50, y=y, mass=mass, sprite=image, sprite_size=sprite_size)
        # Set initial projectile velocity
        velocity = (random.randint(PROJECTILE_X_VELOCITY_LOW, PROJECTILE_X_VELOCITY_HIGH), random.randint(PROJECTILE_Y_VELOCITY_LOW, PROJECTILE_Y_VELOCITY_HIGH))
        projectile.body._set_velocity(velocity)
        
        projectile.body.angular_velocity = ( random.choice([-10, -9, -8, -7, -6, -5, 5, 6, 7, 8, 9, 10]) )
        
        projectile.shape._set_elasticity(PROJECTILE_ELASTICITY)
            
        return projectile
        
    def add_object(self, x, y, mass, sprite, sprite_size=1):
        ''' Adds an object to the game space '''
        obj = GameObject(self.space, x, y, mass,  sprite, sprite_size)
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
        if random.randint(1, 1000) <= PROJECTILE_SPAWN_CHANCE_BASE + ((self.current_level-1) * PROJECTILE_SPAWN_CHANCE_LEVEL):
            image = random.choice(self.projectiles)
            self.spawn_projectile(image=image)
        
    def adjust_player_energy(self, amount):
        self.player_energy = min(PLAYER_ENERGY_MAX, self.player_energy + amount)
    
    
    
def main():
    global clock, bg, screen, font, game, input_handler, render_handler
    
    pygame.init()
    font = pygame.font.Font("freesansbold.ttf", 20) 
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("DeLongest Mile")
    
    bg = pygame.image.load(os.path.join('assets', 'background.jpg'))
    bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT) )
    
    input_handler = InputHandler()
    render_handler = RenderHandler()
    game = GameWorld()
    
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
        game.adjust_player_energy(PLAYER_ENERGY_PER_TICK)
    
        # Level is won!
        if player.body.position[0] < 200:        
            game.end_level()
            
            pygame.draw.rect(screen, (0, 0, 0), (int(SCREEN_WIDTH/2)-225, 95, 475, 100), 0)
            render_handler.flash_text('Level {0} complete'.format(game.current_level))
            
            game.current_level += 1
            game.start_level()
            
        # Level is lost!
        elif player.body.position[0] > SCREEN_WIDTH + GRACE_ZONE:
            game.end_level()
            
            pygame.draw.rect(screen, (0, 0, 0), (int(SCREEN_WIDTH/2)-225, 95, 475, 150), 0)
            label = font.render('You cannot overcome the power of Delong.', 1, TEXT_COLOR_MAIN)
            label2 = font.render('(You dodged {0} Delongs in {1} levels)'.format(game.dodged_objects, game.current_level), 1, TEXT_COLOR_MAIN)
            label3 = font.render('Press left arrow to start from level 1', 1, TEXT_COLOR_MAIN)
            screen.blit(label, (int(SCREEN_WIDTH/2)-200, 110))
            screen.blit(label2, (int(SCREEN_WIDTH/2)-200, 145))
            screen.blit(label3, (int(SCREEN_WIDTH/2)-200, 180))
            pygame.display.flip()
            
            input_handler.handle_level_begin()
            
            game.current_level = 1
            game.dodged_objects = 0
            game.start_level()
    
if __name__ == '__main__':
    sys.exit(main())
