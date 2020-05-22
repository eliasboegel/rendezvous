import math
import orbit_functions
import pygame
import os
import random
import numpy



class MainBody:

    def __init__(self, mass, radius, atm_thickness, atm_color, img_path):
        """Main body class constructor"""

        # Set attributes
        self.type = -1
        self.pos = [0,0]
        self.mass = mass
        self.radius = radius
        self.atm_thickness = atm_thickness
        self.atm_color = atm_color
        self.img_path = img_path
        self.img = None
        self.scaled_img = None
        self.vel = [0,0]

        # Load the image from file
        self.load_img()

    def load_img(self):
        """Method to load the image file into memory"""
        
        # Create path from folder and image file name
        path = os.path.join('img', self.img_path)

        # Load image into attribute and convert pixel format for performance improvements
        self.img = pygame.image.load(os.path.join(path)).convert_alpha()
        
        
        
        # Specify number of layers out of which to draw the atmosphere
        n_atm_layers = 50
        atm_radius = self.radius + self.atm_thickness * 2

        atm_radius_px = int(atm_radius / self.radius * self.img.get_rect().size[0] / 2)
        atm_thickness_px = int(self.atm_thickness * 2 / self.radius * self.img.get_rect().size[0] / 2)

        body_surface = pygame.Surface([atm_radius_px * 2, atm_radius_px * 2], pygame.SRCALPHA)#.convert_alpha()

        # Draw each atmosphere layer
        for layer in range(n_atm_layers):

            # Set layer radius in pixels, smaller radius for ever layer draw to give effect of different atmosphere layers
            layer_radius = int(atm_radius_px - atm_thickness_px / (n_atm_layers) * layer)

            # Set layer color, the inner-most layer is always white
            atm_color = self.atm_color
            
            # Grade color from white (innermost layer) to atm_color (at half drawn atmosphere thickness), outer half of the layer are atm_color, but alpha changes
            if layer > n_atm_layers / 2:
                red = atm_color[0] + (255 - atm_color[0])/(n_atm_layers/2+1)*(layer - n_atm_layers / 2)
                green = atm_color[1] + (255 - atm_color[1])/(n_atm_layers/2+1)*(layer - n_atm_layers / 2)
                blue = atm_color[2] + (255 - atm_color[2])/(n_atm_layers/2+1)*(layer - n_atm_layers / 2)
            else:
                red = atm_color[0]
                green = atm_color[1]
                blue = atm_color[2]
                
            alpha = 10 + (200 - 10)/(n_atm_layers-1)*layer
            
            layer_color = (red, green, blue, alpha)

            # Draw atmosphere layer
            pygame.draw.circle(body_surface, layer_color, [atm_radius_px, atm_radius_px], layer_radius)


        # Draw black layer below planet itself to avoid shine-through of the atmosphere if texture of the main body has transparent pixels
        #pygame.draw.circle(body_surface, (0,0,0), [atm_radius_px, atm_radius_px], atm_radius_px)
        
        body_surface.blit(self.img, [atm_thickness_px, atm_thickness_px])
        
        self.img = body_surface
        
    def scale_img(self, scale):
        """Method to scale the original image to the needed zoom level"""

        # Determine image scaling factor needed to represent radius accurately with current camera scale
        bodyscale = 2 * self.radius * scale / self.img.get_size()[0]

        # Scale original image and save scaled image in attribute
        self.scaled_img = pygame.transform.rotozoom(self.img, 0, bodyscale)



class Orbiter:

    def __init__(self, m_type, pos_init, vel_init, img_path, bodyscale):
        """Orbiter class contructor"""

        # Set attributes
        self.type = m_type
        self.pos = pos_init
        self.vel = vel_init
        self.acc = 0
        self.img_path = img_path
        self.scaled_img = None
        self.bodyscale = bodyscale

        # Load the image from file
        self.load_img()

    def update_acc(self, gm, main_body):
        """Method to update acceleration vector to new value based on position vector"""

        self.acc = orbit_functions.get_grav_acc(gm, main_body.pos, self.pos)
    
    def update_vel(self, dt):
        """Method to update velocity vector to new value based on old velocity vector and acceleration vector"""

        self.vel = orbit_functions.get_vel(self.vel, self.acc, dt)
    
    def update_pos(self, dt):
        """Method to update position to new value based on old position and velocity vector"""

        self.pos = orbit_functions.get_pos(self.pos, self.vel, dt)
    
    def load_img(self):
        """Method to read image file from disk and save it in attributes"""

        # Create path from folder and image file name
        path = os.path.join('img', self.img_path)

        # Load image into attribute and convert pixel format for performance improvements
        self.img = pygame.image.load(os.path.join(path)).convert_alpha()

        # Scale image down to specified body scale and save scaled image in attribute
        self.scaled_img = pygame.transform.rotozoom(self.img, random.randint(0, 360), self.bodyscale)
        
        


class Player(Orbiter):

    def __init__(self,pos_init, vel_init, mass_dry, mass_prop, i_sp, img_path, bodyscale):
        """Class for the player orbiting body"""

        # Set attributes
        self.type = 1
        self.pos = pos_init
        self.vel = vel_init
        self.angle = 0
        self.angle_lock_mode = 0
        self.m_dry = mass_dry
        self.m_prop_start = mass_prop
        self.m_prop = mass_prop
        self.i_sp = i_sp
        self.acc = 0
        self.img_path = img_path
        self.scaled_img = None
        self.bodyscale = bodyscale
        self.firing = False
        self.thrust = 424

        # Load the image from file
        self.load_img()

    def update_vel(self, dt):
        """Method to update velocity vector to new value based on old velocity vector and acceleration vector, but with added functionality to modify speed through propulsion"""

        self.vel = orbit_functions.get_vel(self.vel, self.acc, dt)
        
        # If propulsion system is firing, add dv vector to velocity
        if self.firing:
            self.propell(dt)

    def propell(self, dt):
        """Method to alter the player velocity vector based on the rocket equation and the thrust direction"""

        # Calculate exhaust velocity
        v_e = 9.80665 * self.i_sp

        # Calculate mass flow
        m_flow = self.thrust / v_e

        # Calculate new mass
        m = self.m_dry + self.m_prop

        # Calculate mass of propellant used for this step in simulation time
        dm = m_flow * dt

        # Use rocket equation to calculate difference in speed caused by firing engines
        dv = v_e * math.log(m / (m - dm))

        # Reduce propellant mass by propellant mass used in this step in simulation time
        self.m_prop = self.m_prop - dm

        # Change velocity vector by difference in speed caused propulsion, considering the thrust angle
        self.vel[0] = self.vel[0] + math.cos(self.angle) * dv
        self.vel[1] = self.vel[1] + math.sin(self.angle) * dv
        
    def rotate_to_angle(self, angle):
        """Member to orient the player object to point into a given angle or prograde/retrograde if locked"""
        
        if not self.angle_lock_mode: # No lock
            self.angle = angle
        elif self.angle_lock_mode == 1: # Prograde lock
            self.angle = math.atan2(self.vel[1], self.vel[0])  
        elif self.angle_lock_mode == -1: # Retrograde lock
            self.angle = math.atan2(self.vel[1], self.vel[0]) + math.pi
        
        self.scaled_img = pygame.transform.rotozoom(self.img, math.degrees(self.angle), self.bodyscale)