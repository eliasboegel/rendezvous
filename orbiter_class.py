import math
import orbit_functions
import pygame
import os
import random
import numpy
import worldgen



class MainBody:

    def __init__(self, mass, radius, atm_thickness):
        """
        Main body class constructor
        
        Arguments:
            mass : float - Mass of the main body [kg]
            radius : float - Radius of the main body from center to surface [m]
            atm_thickness : float - Thickness of the planet atmosphere [m]
        """

        # Set type
        self.type = -1
        
        # Set intial positon
        self.pos = [0,0]
         
        # Assign attributes from arguments
        self.mass = mass
        self.radius = radius
        self.atm_thickness = atm_thickness
        
        # Generate planet texture
        self.img = worldgen.gen_planet(1000, self.radius, self.atm_thickness, 6)
        self.scaled_img = None
        
        # Set velocity to 0
        self.vel = [0,0]
            
    def scale_img(self, scale):
        """
        Method to scale the original image to the needed zoom level
        
        Arguments:
            scale : float - Current scale of the viewport
        """

        # Determine image scaling factor needed to represent radius accurately with current camera scale
        bodyscale = 2 * (self.radius + 2 * self.atm_thickness) * scale / self.img.get_size()[0]

        # Scale original image and save scaled image in attribute
        self.scaled_img = pygame.transform.rotozoom(self.img, 0, bodyscale)
        


class Orbiter:

    def __init__(self, m_type, pos_init, vel_init, img_path, bodyscale):
        """
        Orbiter class contructor
        
        Arguments:
            m_type : int - Type of the orbiter to be created
            pos_init : [float, float] - Initial position of the orbiter to be created [m]
            vel_ init : [float, float] - Initial velocity of the orbiter to be created [m/s]
            img_path : string - File name of the image to represent the orbiter
            bodyscale : float - Scale factor for the image
        """

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
        """
        Method to update acceleration vector to new value based on position vector
        
        Arguments:
            gm : float - Gravitational parameter
            main_body : MainBody instance - Instance of the main body
        """

        #Calculate new gravitational acceleration
        self.acc = orbit_functions.get_grav_acc(gm, main_body.pos, self.pos)
    
    def update_vel(self, dt):
        """
        Method to update velocity vector to new value based on old velocity vector and acceleration vector
        
        Arugments:
            dt : float - Time increment since last simulation step [s]
        """

        # Calculate new velocity
        self.vel = orbit_functions.get_vel(self.vel, self.acc, dt)
    
    def update_pos(self, dt):
        """
        Method to update position to new value based on old position and velocity vector
        
        Arguments:
            dt : float - Time increment since last simulation step [s]
        """

        # Calculate new position
        self.pos = orbit_functions.get_pos(self.pos, self.vel, dt)
    
    def load_img(self):
        """
        Method to read image file from disk and save it in attributes
        """

        # Create path from folder and image file name
        path = os.path.join('img', self.img_path)

        # Load image into attribute and convert pixel format for performance improvements
        self.img = pygame.image.load(path).convert_alpha()

        # Scale image down to specified body scale and save scaled image in attribute
        self.scaled_img = pygame.transform.rotozoom(self.img, random.randint(0, 360), self.bodyscale)
        
        

class Player(Orbiter):

    def __init__(self,pos_init, vel_init, mass_dry, mass_prop, i_sp, thrust, img_path, bodyscale):
        """
        Class for the player orbiting body
        
        Arguments:
            pos_init : [float, float] - Initial positon vector for the player [m]
            vel_init : [float, float] - Initial velocity vector for the player [m/s]
            mass_dry : float - Dry mass of the player orbiter
            mass_prop : float - Initial propellant mass of the player orbiter
            i_sp : float - Specific impulse of the propulsion system
            thrust : float - Thrust of the propulsion system
            img_path : string - File name of the image to represent the player orbiter
            bodyscale : float - Scaling factor to size the orbiter image
        """

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
        self.firing = 0
        self.thrust = thrust
        self.exhaust_img = None

        # Load the image from file
        self.load_img()
        
        # Load the exhaust image from file
        self.load_exhaust()
        
        # Set engine sound
        # If specific impulse is above 500, assume electric propulsion system, otherwise chemical propulsion system
        if self.i_sp > 500:
            soundpath = os.path.join('snd', 'ElectricPropulsion.ogg')
        else:
            soundpath = os.path.join('snd', 'ChemicalPropulsion.ogg')
            
        # Initialize propulsion sound 
        self.prop_sound = pygame.mixer.Sound(soundpath)
        self.prop_sound.set_volume(0.1)
            
    def update_vel(self, dt):
        """
        Method to update velocity vector to new value based on old velocity vector and acceleration vector, but with added functionality to modify speed through propulsion
        
        Arguments:
            dt : float - Time increment since last simulation step [s]
            
        Comments:
            This method is needed as the Orbiter parent class does not provide thrust functionality
        """

        # Calculate new velocity
        self.vel = orbit_functions.get_vel(self.vel, self.acc, dt)
        
        # If propulsion system is firing, add dv vector to velocity
        if self.firing and self.m_prop > 0:
            self.propell(dt)

    def propell(self, dt):
        """
        Method to alter the player velocity vector based on the rocket equation and the thrust direction
        
        Arguments:
            dt : float - Time increment since last simulation step [s]
        """

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
        
        # If propellant ran out in the last simulation step, stop thruster and thruster sound
        if not self.m_prop > 0:
            self.firing = 0
            self.prop_sound.fadeout(500)

        # Change velocity vector by difference in speed caused propulsion, considering the thrust angle
        self.vel[0] = self.vel[0] + math.cos(self.angle) * dv
        self.vel[1] = self.vel[1] + math.sin(self.angle) * dv
        
    def rotate_to_angle(self, angle):
        """
        Method to orient the player object to point into a given angle or prograde/retrograde if locked
        
        Arguments:
            angle : float - Current player angle from positive x-axis [rad]
        """
        
        # Set angle attribute based on lock mode and argument
        if not self.angle_lock_mode: # No lock
            self.angle = angle
        elif self.angle_lock_mode == 1: # Prograde lock
            self.angle = math.atan2(self.vel[1], self.vel[0])  
        elif self.angle_lock_mode == -1: # Retrograde lock
            self.angle = math.atan2(self.vel[1], self.vel[0]) + math.pi
        
        # Rotate player image based on angle attribute
        self.scaled_img = pygame.transform.rotozoom(self.img, math.degrees(self.angle), self.bodyscale)
        
        # Rotate exhaust image if thruster is firing
        if self.firing:
            self.scaled_exhaust_img = pygame.transform.rotozoom(self.exhaust_img, math.degrees(self.angle), self.bodyscale)
        
    def load_exhaust(self):
        """
        Method to load the exhaust image
        """
        
        # If the specific impulse is over 500, assume electric propulsion, otherwise chemical propulsion
        if self.i_sp > 500:
            path = os.path.join('img', 'electricexhaust.png')
        else:
            path = os.path.join('img', 'chemicalexhaust.png')

        # Scale image down to specified body scale and save scaled image in attribute
        self.exhaust_img = pygame.image.load(path).convert_alpha()
        
        # Scale the exhaust image down to correct scale
        self.scaled_exhaust_img = pygame.transform.rotozoom(self.exhaust_img, math.degrees(self.angle), self.bodyscale)
        
