import os
import io_functions
import orbiter_class
import math
import random



class Mission:

    def __init__(self, mission_folder, mission_file):
        """
        Mission class constructor
        
        Arguments:
            mission_folder : string - The name of the subfolder in the programs root folder that the mission file is located in
            mission_file : string - The name of the mission file in the mission folder
        """
        

        # Initialize a list of all bodies
        self.bodies = []
        
        # If the user selected a randomly generated mission, generate mission
        # If the user selected a premade mission, load that mission
        if mission_file == 'r':
            # Ask for number of hazards to spawn and generate a random mission based on that
            hazards = int(input('How many hazards would like to play with/against? '))
            self.generate_mission(hazards)
        else:
            # Read mission file into a dictionary
            mission = io_functions.read_file(mission_folder, (mission_file + '.txt'))

            # Loop through all bodies in the mission dictionary
            for o, o_data in mission.items():

                # If the body is the player body, create new player object and append list of bodies
                if o_data['type'] == 'player':
                    self.bodies.append(    orbiter_class.Player(o_data['pos_init'],
                                                                o_data['vel_init'],
                                                                o_data['mass_dry'],
                                                                o_data['mass_prop'],
                                                                o_data['i_sp'],
                                                                o_data['thrust'],
                                                                o_data['img'],
                                                                o_data['bodyscale']))

                # If the body is the main body, create a new main body object and append list of bodies
                elif o_data['type'] == 'mainbody':
                    self.bodies.append(  orbiter_class.MainBody(o_data['mass'],
                                                                o_data['radius'],
                                                                o_data['atm_thickness']))

                # If body is of another type such as 'debris' or 'hazard', create new orbiter object and append list of bodies
                else:
                    self.bodies.append(   orbiter_class.Orbiter(o_data['type'],
                                                                o_data['pos_init'],
                                                                o_data['vel_init'],
                                                                o_data['img'],
                                                                o_data['bodyscale']))
                
        
        
    def generate_mission(self, n_hazards):
        """
        Method to generate a random mission
        
        Arguments:
            n_hazards : int - The number of hazard orbiters to spawn
            
        Comments:
            - This method adds the generated bodies directly to the mission object
            - Every body is spawned in its pericenter
        """
        
        # Gravitational constant, for later use in determining useful orbits
        G = 6.67408e-11
        
        
        # Generate main body
        # Randomize main body density between 4000kg/m^3 and 6000kg/m^3, used for mass calculation with the radius
        mb_density = 4e3 + random.random() * 2e3
        
        # Randomize main body radius between 3000km and 13000km
        mb_radius = 3000e3 + random.random() * 10000e3
        
        # Calculation of the mass, done through the planet density and the spherical volume of the planet
        mb_mass = 4/3 * math.pi * mb_radius**3 * mb_density
        
        # Randomize the atmosphere thickness between 5% and 10% of the planet radius
        mb_atm_thickness = mb_radius * (0.05 + random.random() * 0.05)
        
        # Calculate gravitational parameter
        gm = G * mb_mass
        
        # Spawn main body based on mass, radius and atmosphere thickness
        self.bodies.append(  orbiter_class.MainBody(mb_mass,
                                                    mb_radius,
                                                    mb_atm_thickness))
                            
                            
                        
                        
        
        
        # Generate target body
        # Randomize the initial pericenter radius from an altitude of 1.5x the end of the atmosphere to 3000km above the end of the atmosphere
        tg_r_init = mb_radius + mb_atm_thickness * 1.5 + random.random() * 3000e3
        
        # Randomize the inital velocity by assuming the circular velocity and adding between 0% and 20% of the speed
        tg_v_init = (gm/tg_r_init)**0.5 * (1 + 0.2 * random.random())
        
        # Randomize the argument of pericenter (angle in rad from positive x-axis)
        tg_pos_angle = random.random() * math.pi * 2
        
        # Calculate the direction (angle in rad from positive x-axis) of the initial velocity vector based on the argument of pericenter
        tg_vel_angle = tg_pos_angle + math.pi / 2
        
        # Form the initial position vector from the pericenter radius and the argument of pericenter
        tg_pos_init = [tg_r_init * math.cos(tg_pos_angle), tg_r_init * math.sin(tg_pos_angle)]
        
        # Form the initial velocity vector from the initial speed calculated and the initial velocity direction angle
        tg_vel_init = [tg_v_init * math.cos(tg_vel_angle), tg_v_init * math.sin(tg_vel_angle)]
        
        # Spawn target orbiter based on initial position and velocity
        self.bodies.append(   orbiter_class.Orbiter(    2,
                                                        tg_pos_init,
                                                        tg_vel_init,
                                                        'sat2.png',
                                                        0.15))
        
        
        
        
        
                            
        # Generate player body
        # Set distance measure to target body initial position to zero
        dt = 0
        
        # Generate initial conditions for player until intial position that is at least 1000km from the target is found
        while dt < 1000e3:
            # Set player body pericenter radius to one atmosphere above the end of the planet's atmosphere
            pl_r_init = mb_radius + 2 * mb_atm_thickness
            
            # Calculate velocity needed for a circular orbit
            pl_v_init = (gm/pl_r_init)**0.5
            
            # Randomize starting position direction (angle in rad from positive x-axis) (= argument of pericenter)
            pl_pos_angle = random.random() * math.pi * 2
            
            # Calculate initial velocity direction (angle in rad from positive x-axis)
            pl_vel_angle = pl_pos_angle + math.pi / 2
            
            # Form the initial position vector from the pericenter radius and the argument of pericenter
            pl_pos_init = [pl_r_init * math.cos(pl_pos_angle), pl_r_init * math.sin(pl_pos_angle)]
            
            # Form the initial velocity vector from the initial speed calculated and the initial velocity direction angle
            pl_vel_init = [pl_v_init * math.cos(pl_vel_angle), pl_v_init * math.sin(pl_vel_angle)]
            
            # Calculate distance to the target body from the generated player intial position, used in the loop condition to place player sufficiently far away from target
            dt = ((pl_pos_init[0] - tg_pos_init[0])**2 + (pl_pos_init[1] - tg_pos_init[1])**2)**0.5
            
        # Randomize dry mass from 100kg to 1100kg
        pl_mass_dry = 100 + random.random() * 1000
        
        # Determine if spacecraft will use a chemical or electric propulsion system, 75% chance for chemical, 25% for electric
        if random.random() < 0.75:
            # Chemical propulsion
            # Set a fuel mass taking into account the dry mass and pericenter altitudes of player and target
            pl_mass_fuel = pl_mass_dry * (0.5 + tg_r_init / pl_r_init)
            
            # Randomize specific impulse between 200s and 450s
            pl_i_sp = 200 + random.random() * 250
            
            # Randomize thrust [N] between dry 0.4x and 0.6x the player dry mass
            pl_thrust = pl_mass_dry * (0.8 + random.random() * 0.4) / 2
            
        else:
            # Electric propulsion
            # Set a fuel mass taking into account the dry mass and pericenter altitudes of player and target
            pl_mass_fuel = pl_mass_dry * (0.2 + 0.4 * tg_r_init / pl_r_init)
            
            # Randomize specific impulse between 1000s and 2000s
            pl_i_sp = 1000 + random.random() * 1000
            
            # Randomize thrust [N] between dry 0.08x and 0.12x the player dry mass
            pl_thrust = pl_mass_dry * (0.8 + random.random() * 0.4) / 10
                
            
        # Spawn player body based on inital position and velocity as well as dry mass, propellant mass, thrust and specific impulse
        self.bodies.append(orbiter_class.Player(pl_pos_init,
                                                pl_vel_init,
                                                pl_mass_dry,
                                                pl_mass_fuel,
                                                pl_i_sp,
                                                pl_thrust,
                                                'player.png',
                                                0.1))
        
        
        
        
        
        # Generate n_hazards hazard orbiters
        for i in range(n_hazards):
            # Set distance measure to both player body and target body to 0
            dp = 0
            dt = 0
            
            # Generate initial conditions for hazard body while ensuring that the distance from either target or player body is at least 1000km
            while dp < 1000e3 or dt < 1000e3:
                # Randomize hazard body pericenter radius between an altitude of 3 atmospheres and 5000km higher
                hz_r_init = mb_radius + mb_atm_thickness * 3 + random.random() * 5000e3
                
                # Randomize inital velocity by finding circular velocity and adding between 0% and 40%
                hz_v_init = (gm/hz_r_init)**0.5 * (1 + 0.4 * random.random())
                
                # Randomize argument of pericenter (angle in rad from positive x-axis)
                hz_pos_angle = random.random() * math.pi * 2
                
                # Calculate velocity from argument of pericenter (angle in rad from positive x-axis)
                hz_vel_angle = hz_pos_angle + math.pi / 2
                
                # Form the initial position vector from the pericenter radius and the argument of pericenter
                hz_pos_init = [hz_r_init * math.cos(hz_pos_angle), hz_r_init * math.sin(hz_pos_angle)]
                
                # Form the initial velocity vector from the initial speed calculated and the initial velocity direction angle
                hz_vel_init = [hz_v_init * math.cos(hz_vel_angle), hz_v_init * math.sin(hz_vel_angle)]
                
                # Calculate distance to the player body from the generated player intial position, used in the loop condition to place player sufficiently far away from player
                dp = ((pl_pos_init[0] - hz_pos_init[0])**2 + (pl_pos_init[1] - hz_pos_init[1])**2)**0.5
                
                # Calculate distance to the target body from the generated target intial position, used in the loop condition to place hazard sufficiently far away from target
                dt = ((tg_pos_init[0] - hz_pos_init[0])**2 + (tg_pos_init[1] - hz_pos_init[1])**2)**0.5
            
            # Spawn hazard based on initial position and velocity
            self.bodies.append(   orbiter_class.Orbiter(3,
                                                        hz_pos_init,
                                                        hz_vel_init,
                                                        'sat1.png',
                                                        0.1))