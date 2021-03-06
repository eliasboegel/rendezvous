import pygame
import random
import math
import random
import os
from itertools import combinations

import mission_class
import ui_class
import orbiter_class
import io_functions
import orbit_functions



class Rendezvous:

    def __init__(self, mission_file):
        """
        Main game class constructor
        
        Arugments:
            mission_file : string - File name of the mission file to load OR 'r' in case player wants to generate a random mission
        """

        # Set gravitational constant
        self.grav_const = 6.6743015e-11

        # Read config file
        self.read_config()
        
        # Set window icon
        icon = pygame.image.load(os.path.join('img', 'icon.png'))
        pygame.display.set_icon(icon)

        # Spawn pygame window
        self.ui = ui_class.UI(self)
        
        # Set window title
        pygame.display.set_caption('Rendezvous')

        # Read mission from selected mission file
        self.mission =  mission_class.Mission('missions', mission_file, self.planet_res)

        # Find main body in list of bodies and calculate the gravitational parameter from it
        for body in self.mission.bodies:
            if type(body) == orbiter_class.MainBody:
                self.gravparam = body.mass * self.grav_const
                body.scale_img(self.ui.scale)
                break

        # Set the current mission state to mission ongoing
        self.mission_state = 0
        
        # Set collision parameters
        self.collision_dist = 500e3
        self.safe_vel = 1000

        # Run main game loop
        self.game_loop()


    def read_config(self):
        """
        Method to read several attributes from config file
        """

        # Read config file into a config dictionary
        cfg = io_functions.read_file('cfg', 'config.txt')

        # Read resultion from config file
        self.res = cfg['resolution']
        
        # Read fullscreen mode from config file
        self.fullscreen = cfg['fullscreen']
        
        # Read target fps from config file
        self.target_fps = cfg['fps']
        
        # Read HUD color from config file
        self.hud_color = cfg['hud_color']

        # Read default simulation time speed from config
        self.timefactor = cfg['default_timefactor']

        # Read simulation time multiplier for simulation speed increase/decrease from config
        self.timefactor_mult = cfg['timefactor_mult']

        # Read zoom speed for camera zoom in/out from config
        self.zoom_speed = cfg['zoom_speed']
        
        # Read desired planet resolution
        self.planet_res = cfg['planet_res']
        
        # Read whether or not nebulae should be generated for the background
        self.generate_nebulae = cfg['generate_nebulae']


    def game_loop(self):
        """
        Main loop of the game; Updates simulation of all bodies, draws every frame and handles user input
        """

        # Initialize pygame
        pygame.init()

        # Inititalize main game clock
        clock = pygame.time.Clock()

        # Loop until program is ended
        running = 1
        while running:
            # Get time elapsed in seconds since last frame was drawn, consider target FPS count
            dt_frame = clock.tick(self.target_fps) / 1000

            # Get elapsed time in physics simulation speed
            dt = dt_frame * self.timefactor # Multiply with timefactor

            # Pass simulation time elapsed since last frame to UI object so that an FPS counter can be drawn
            self.ui.dt = dt_frame

            player_body = None
            # Find player body for later use
            for body in self.mission.bodies:
                if body.type == 1: # Player body type = 1
                    player_body = body
                    

            # Handle user input
            for event in pygame.event.get():

                # Stay in main loop until pygame.quit event is sent
                if event.type == pygame.QUIT:
                    running = 0

                # If the viewport is resized, forward this resize to the UI object
                elif event.type == pygame.VIDEORESIZE:
                    self.ui.resize_screen(event.size)
                    
                # If current song ends, start new song
                elif event.type == (pygame.USEREVENT + 1):
                    self.ui.play_music()

                # If a mouse button is pressed
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # LMB, move camera with mouse pointer
                    if event.button == 1:
                        self.ui.moving = 1
                    
                    # RMB, start firing player propulsion system
                    elif event.button == 3 and player_body is not None:
                        if player_body.m_prop > 0:
                            player_body.firing = 1
                            player_body.prop_sound.play(-1, 0, 500)

                    # Scroll wheel scrolled upwards, zoom in camera
                    elif event.button == 4:
                        self.ui.zoom_camera(-1)

                    # Scroll wheel scrolled downwards, zoom out camera
                    elif event.button == 5:
                        self.ui.zoom_camera(1)

                # If a mouse button is released
                elif event.type == pygame.MOUSEBUTTONUP:

                    # LMB, stop moving camera with mouse pointer
                    if event.button == 1:
                        self.ui.moving = 0

                    # RMB, stop firing player propulsion system
                    elif event.button == 3 and player_body is not None:
                        player_body.firing = 0
                        player_body.prop_sound.fadeout(500)

                # If a key on the keyboard is pressed
                elif event.type == pygame.KEYDOWN:

                    # Escape key, end game
                    if event.key == pygame.K_ESCAPE:
                        running = 0
                    
                    # Return/Enter key, if mission is over then end game
                    elif event.key == pygame.K_RETURN:
                        if self.mission_state > 0:
                            running = 0
                    
                    # Toggle orbit ellipses     
                    elif event.key == pygame.K_SPACE:
                        self.ui.draw_orbits_toggle = not self.ui.draw_orbits_toggle
                    
                    # Left arrow key, slow down simulation time to a maximum of 0.1x real time
                    elif event.key == pygame.K_LEFT:
                        if self.timefactor / self.timefactor_mult >= 1:
                            self.timefactor = self.timefactor / self.timefactor_mult

                    # Right arrow key, speed up simulation time to a maximum of 10000x real time
                    elif event.key == pygame.K_RIGHT:
                        if self.timefactor * self.timefactor_mult <= 1000:
                            self.timefactor = self.timefactor * self.timefactor_mult

                    # Up arrow key, switch lock mode up
                    elif event.key == pygame.K_UP:
                        if player_body is not None and player_body.angle_lock_mode < 1:
                            player_body.angle_lock_mode += 1
                    
                    # Down arrow key, switch lock mode down
                    elif event.key == pygame.K_DOWN:
                        if player_body is not None and player_body.angle_lock_mode > -1:
                            player_body.angle_lock_mode -= 1

            # If frame rate is below a certain threshold (example: frame drawing stops when window is moved), stop simulation to avoid grossly wrong orbit updates
            if dt / self.timefactor <= 1/20:
                
                # Find main body object in list of bodies for future orbiting body member call (gravitational acceleration update requires main body position)
                main_body = None
                for body in self.mission.bodies:
                    if body.type == -1: # Main body type = -1
                        main_body = body
                        break

                # Orbit state vector updates for all bodies
                for body in self.mission.bodies:
                    # Only update for all orbiting bodies, not for main body
                    if body.type >= 0:

                        # Update current acceleration vector
                        body.update_acc(self.gravparam, main_body)

                        # If body is the player body, rotate craft into correct position first
                        if body.type == 1:
                            body.rotate_to_angle(self.ui.get_mouse_angle(body))
                        
                        # Update body velocity vector
                        body.update_vel(dt)

                        # Update current body position vector based on current body velocity vector
                        body.update_pos(dt)


                #Collision check between all bodies 
                for body_combo in combinations(self.mission.bodies, 2):
                    
                    # Check for collisions between certain body types
                    if not (body_combo[0].type or body_combo[1].type): # Do not consider debris-debris collisions, debris type value is 0, not(A or B) yields 1 only if A and B are False
                        continue
                    elif body_combo[0].type == -1: # If first body in combo is main body
                        collision_mode = orbit_functions.collision_check(body_combo[0], body_combo[1], body_combo[0].radius + body_combo[0].atm_thickness * 1.5, 0)
                        if collision_mode > 0:
                            if body_combo[1].type == 1: # If second body is the player, set mission to failed by deorbit
                                #Update mission state, but only if mission is still ongoing
                                if not self.mission_state:
                                    self.mission_state = 2
                            
                            try: # Delete original body if it hasn't been removed by another collision
                                self.mission.bodies.remove(body_combo[1])
                            except ValueError:
                                pass
                    elif body_combo[1].type == -1: # If second body in combo is main body
                        collision_mode = orbit_functions.collision_check(body_combo[1], body_combo[0], body_combo[1].radius + body_combo[1].atm_thickness * 1.5, 0)
                        if collision_mode > 0:
                            if body_combo[0].type == 1: # If first body is the player, set mission to failed by deorbit
                                #Update mission state, but only if mission is still ongoing
                                if not self.mission_state:
                                    self.mission_state = 2
                            try: # Delete original body if it hasn't been removed by another collision
                                self.mission.bodies.remove(body_combo[0])
                            except ValueError:
                                pass
                    else:
                        collision_mode = orbit_functions.collision_check(body_combo[0], body_combo[1], self.collision_dist, self.safe_vel)
                        
                        if collision_mode == 2: # Crash
                            
                            #Update mission state, but only if mission is still ongoing
                            if not self.mission_state:
                                # If crash is with target
                                if (body_combo[0].type == 1 and body_combo[1].type == 2) or (body_combo[1].type == 1 and body_combo[0].type == 2):
                                    self.mission_state = 3
                                
                                # If crash is with another orbiting body
                                elif (body_combo[0].type == 1 and body_combo[1].type == 3) or (body_combo[1].type == 1 and body_combo[0].type == 3):
                                    self.mission_state = 4
                                    
                                # If crash is with debris
                                elif (body_combo[0].type == 1 and body_combo[1].type == 0) or (body_combo[1].type == 1 and body_combo[0].type == 0):
                                    self.mission_state = 5
                                    
                                # If target crashed with another orbiting body
                                elif (body_combo[0].type == 2 and body_combo[1].type == 3) or (body_combo[1].type == 2 and body_combo[0].type == 3):
                                    self.mission_state = 6
                                    
                                # If target crashed with debris
                                elif (body_combo[0].type == 2 and body_combo[1].type == 0) or (body_combo[1].type == 2 and body_combo[0].type == 0):
                                    self.mission_state = 7
                            
                            
                            debris_spawn_count = 7 # Number of debris objects to spawn on crash. Only exact for odd numbers!
                            debris_spawn_range = debris_spawn_count // 2
                            
                            
                            for i in range(-debris_spawn_range, debris_spawn_range):
                                #Debris scaling
                                debris_scale_0 = body_combo[0].bodyscale * (1 - 1/(debris_spawn_count) * abs(i)) * 0.5
                                debris_scale_1 = body_combo[0].bodyscale * (1 - 1/(debris_spawn_count) * abs(i)) * 0.5
                                
                                #Debris orbit variation
                                debris_pos_0 = [body_combo[0].pos[0] + 5000 * i, body_combo[0].pos[1] + 5000 * i]
                                debris_pos_1 = [body_combo[1].pos[0] + 5000 * i, body_combo[1].pos[1] + 5000 * i]
                                debris_vel_0 = [body_combo[0].vel[0] + 100 * i, body_combo[0].vel[1] + 100 * i]
                                debris_vel_1 = [body_combo[1].vel[0] + 100 * i, body_combo[1].vel[1] + 100 * i]
                                
                                self.mission.bodies.append(orbiter_class.Orbiter(0, debris_pos_0, body_combo[0].vel, 'debris.png', debris_scale_0))
                                self.mission.bodies.append(orbiter_class.Orbiter(0, debris_pos_1, body_combo[1].vel, 'debris.png', debris_scale_1))
                            
                            try: # Delete both original bodies if they haven't been removed by another collision
                                self.mission.bodies.remove(body_combo[0])
                                self.mission.bodies.remove(body_combo[1])
                                
                            # Catching potential errors, I was not able to weed out all errors and the only unexpected error that occurs is a value error, so ValueErrors are passed
                            except ValueError:
                                pass
                          
                        elif collision_mode == 1: # Rendezvous
                            if ((body_combo[0].type == 1 and body_combo[1].type == 2) or #If the two bodies are player and target
                                (body_combo[1].type == 1 and body_combo[0].type == 2)):
                                self.mission_state = 1 # Mission successful
                        
            # Call to function that handles several non-rendering tasks that have to be executed every frame
            self.ui.frame_routine()

            # Render screen
            self.ui.render()

        pygame.quit() #End game