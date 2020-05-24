import pygame, pygame.freetype
import os
import math
import random

import orbiter_class
import orbit_functions

class UI:

    def __init__(self, game_instance):
        """User interface class constructor"""

        # Save reference to main game object for access to the mission body list
        self.game_instance = game_instance

        # Initialize the main pygame surface and save reference
        if self.game_instance.fullscreen:
            self.screen = pygame.display.set_mode(self.game_instance.res, pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        else:
            self.screen = pygame.display.set_mode(self.game_instance.res, pygame.RESIZABLE | pygame.DOUBLEBUF)

        # Set default camera scale and target scale
        self.scale = 0.00001

        # Initialize camera move state
        self.moving = 0

        # Initialize time elapsed since last frame
        self.dt = 0

        # Initialize scene center position of the screen in pixels with reference at the center of window
        self.center = [0,0]

        # Initialize mouse position variables to keep track of mouse movement
        self.mouse_pos_old = [0,0]
        self.mouse_pos = [0,0]
        
        # Initialize draw-orbits flag
        self.draw_orbits_toggle = 1
        
        # Create and save background surface
        self.bg = self.create_background(self.game_instance.res)
        
        # Initialize current music track variable
        self.currtrack = ''
        
        # Initialize mixer
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.mixer.init()
        pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)
        
        # Start playing music
        self.play_music()


    def draw_scene(self):
        """Method to draw the 2D game scene (only bodies, not HUD!)"""

        # Loop through all bodies in order to draw each one
        for body in self.game_instance.mission.bodies:

            # If the body is the main body, draw the body as well as an atmosphere
            if body.type == -1:

                # Get radius of the outermost part of the atmosphere
                atm_radius = body.radius + body.atm_thickness

                # Draw body only if main body AND its atmosphere are visible on the screen
                if self.is_on_screen(self.center_to_topleft(self.pos_to_center_coord(body.pos)), [2 * atm_radius * self.scale, 2 * atm_radius * self.scale]):
                    self.draw_img(body.scaled_img, self.center_to_topleft(self.pos_to_center_coord(body.pos)))


            # Draw orbiting bodies, but only if they are visible on the screen
            elif self.is_on_screen(self.center_to_topleft(self.pos_to_center_coord(body.pos)), body.scaled_img.get_size()):
                
                if body.type == 1:
                    
                    player_pos = self.center_to_topleft(self.pos_to_center_coord(body.pos))
                    
                    # Draw exhaust if firing
                    if body.firing:
                        exhaust_pos_x = player_pos[0] - math.cos(body.angle) * body.img.get_size()[0] * body.bodyscale
                        exhaust_pos_y = player_pos[1] + math.sin(body.angle) * body.img.get_size()[1] * body.bodyscale
                        
                        self.draw_img(body.scaled_exhaust_img, [exhaust_pos_x, exhaust_pos_y])
                    
                    # Draw body
                    self.draw_img(body.scaled_img, self.center_to_topleft(self.pos_to_center_coord(body.pos)))
                    
                else:
                    # Draw body
                    self.draw_img(body.scaled_img, self.center_to_topleft(self.pos_to_center_coord(body.pos)))


    def pos_to_center_coord(self, pos):
        """Method to scale the values of the position to a coordinate on the screen"""
        # Declare coord (coordinates of the object on the screen) to be a list of two items (x- and y-coordinates)
        coord = [0,0] 

        # Scale both components of the spacecraft position vector down to an integer coordinate (in pixels) on the screen
        coord[0] = int(pos[0] * self.scale)
        coord[1] = int(pos[1] * self.scale)

        # Return position in pixels with reference to the center of the screen
        return coord
    

    def draw_img(self, img, pos):
        """Method to draw an image onto the screen"""

        # Get image bounding rectangle, centered at the position on the screen (in top-left reference)
        img_rect = img.get_rect(center=pos)
        
        # Draw image on the screen
        self.screen.blit(img, img_rect)


    def update_zooming_imgs(self):
        """Method to update the image scale of all bodies whose images need to scale up or down when zooming the camera"""

        # Find the main body in the list of bodies
        for body in self.game_instance.mission.bodies:
            if body.type == -1:
                if self.is_on_screen(self.center_to_topleft(self.pos_to_center_coord(body.pos)), body.scaled_img.get_size()):
                    # Update the image scale of the body
                    body.scale_img(self.scale)
                    break


    def center_to_topleft(self, center_coord):
        """Method to translate coordinates centered in the middle of the screen to usual coordinates with top-left reference point"""
        
        # Declare the coordinates with top-left reference to be a list of two items (x- and y-coordinate)
        topleft_coord = [0,0]

        # Determine the centered coordinates from coordinates with top-left reference and the resolution
        topleft_coord[0] = center_coord[0] + self.game_instance.res[0] // 2 # Determine integer x-coordinate in top-left reference
        topleft_coord[1] = - center_coord[1] + self.game_instance.res[1] // 2 # Determine integer y-coordinate in top-left reference

        # Return coordinates with a top-left reference
        return topleft_coord


    def resize_screen(self, newres):
        """Method to update the resolution, called from resize event"""

        # Save new resolution
        self.game_instance.res = newres

        # Create new main game surface with new resolution
        self.screen = pygame.display.set_mode(newres, pygame.RESIZABLE)
        
        # Create and save new background surface that was generated for the new resolution
        self.bg = self.create_background(self.game_instance.res)


    def get_mouse_angle(self, sc_body):
        """Method to determine the angle that the mouse pointer makes to the positive x-axis at the position of the player object"""

        # Get on screen location of the player object in pixels with a top-left reference
        x_sc = self.center_to_topleft(self.pos_to_center_coord(sc_body.pos))[0]
        y_sc = self.center_to_topleft(self.pos_to_center_coord(sc_body.pos))[1]

        # Determine relative position from player body to mouse pointer, y-axis is now positive UPWARDS
        x_rel = self.mouse_pos[0] - x_sc
        y_rel = y_sc - self.mouse_pos[1]

        # Determine and return the angle, taking quadrants into account (-pi < angle < pi)
        return math.atan2(y_rel, x_rel)


    def frame_routine(self):
        """Method to handle all frame-by-frame operations not related to rendering the screen contents"""

        # Update mouse position attributes
        self.mouse_pos_old = self.mouse_pos
        self.mouse_pos = pygame.mouse.get_pos()

        # Move camera if camera needs to move with mouse pointer
        if self.moving:
            self.move_camera()


    def render(self):
        """Method to render all screen contents"""

        # Draw the background texture
        self.screen.blit(self.bg, [0,0])

        # Draw the orbit ellipses for the player and target objects
        if self.draw_orbits_toggle:
            self.draw_orbits()

        # Draw the game scene (all bodies)
        self.draw_scene()

        # Draw the HUD on top of the scene
        self.draw_hud()

        # Update window contents to draw changes
        pygame.display.update()


    def draw_hud(self):
        """Method to draw all HUD elements besides orbits"""

        # Draw an FPS counter in the top right corner of the window
        #self.draw_text(f"{1/self.dt:.0f} FPS", 30, self.game_instance.hud_color, (self.game_instance.res[0] - 10, 10), 'right')

        # Draw the current simulation time factor in the bottom left corner of the window
        self.draw_text(f"x{self.game_instance.timefactor:.0f}", 30, self.game_instance.hud_color, (10, self.game_instance.res[1]-40), 'left')

        # Draw player object related HUD elements only when mission is ongoing
        if self.game_instance.mission_state == 0:

            # Draw the orbit ellipses for the player and target objects
            if self.draw_orbits_toggle:
                self.draw_orbits()

            # Find player object in list of bodies and determine remaining propellant fraction
            prop_fraction = 0
            player_body = None
            target_body = None
            for body in self.game_instance.mission.bodies:
                if body.type == 1:
                    player_body = body
                    
                    prop_fraction = body.m_prop / body.m_prop_start
                    
                    # Draw thrust direction lock mode
                    if not body.angle_lock_mode: # No lock
                        self.draw_text("No direction lock", 30, self.game_instance.hud_color, [self.game_instance.res[0] - 10, self.game_instance.res[1] - 40], 'right')
                    elif body.angle_lock_mode == 1: # Prograde lock
                        self.draw_text("Prograde lock", 30, self.game_instance.hud_color, [self.game_instance.res[0] - 10, self.game_instance.res[1] - 40], 'right')
                    elif body.angle_lock_mode == -1: # Retrograde lock
                        self.draw_text("Retrograde lock", 30, self.game_instance.hud_color, [self.game_instance.res[0] - 10, self.game_instance.res[1] - 40], 'right')
                
                if body.type == 2: # If body is target body
                    target_body = body
                    
                    # Draw target icon caption
                    self.draw_text("Target", 30, self.game_instance.hud_color, [self.game_instance.res[0] / 2, 25], 'center')
                    
                    # Draw target icon
                    img = pygame.transform.rotozoom(body.img, 0, 0.25)
                    img_size = img.get_size()
                    
                    self.draw_img(img, [self.game_instance.res[0] / 2, 45 + img_size[1] / 2])

            # Draw propellant bar only when propellant is left
            if prop_fraction > 0:
                self.draw_text("Propellant left:", 30, self.game_instance.hud_color, (10,10), 'left')

                barcolor = (255 - prop_fraction * 255, prop_fraction * 255, 0)
                pygame.draw.line(self.screen, barcolor, (10,55), (10 + 220 * prop_fraction, 55), 30)

            # Draw differential velocity between player and target
            player_target_dist = ((player_body.pos[0] - target_body.pos[0])**2 + (player_body.pos[1] - target_body.pos[1])**2)**0.5
            if player_target_dist < self.game_instance.collision_dist * 10:
                player_target_diff_vel = ((player_body.vel[0] - target_body.vel[0])**2 + (player_body.vel[1] - target_body.vel[1])**2)**0.5
                
                if player_target_diff_vel <= self.game_instance.safe_vel:
                    self.draw_text(f"\u0394V to target  {player_target_diff_vel:.0f} m/s", 30, (0,255,0), (10,100), 'left')
                else:
                    self.draw_text(f"\u0394V to target {player_target_diff_vel:.0f} m/s", 30, (255,0,0), (10,100), 'left')
            
        # If mission has ended, draw endscreen instead of player object HUD
        else:
            self.draw_endscreen()


    def draw_text(self, text, size, color, coord, align):
        """Method to draw text on the screen"""
        
        # Set font to be used to the system default font
        font = pygame.freetype.SysFont(None, size, bold=0, italic=0)

        # Consider left, center and right text alignment
        if align == 'center':
            textobj, textrect = font.render(text, color)
            rect = textobj.get_rect(centerx = coord[0], centery = coord[1])

        elif align == 'right':
            textobj, textrect = font.render(text, color)
            rect = textobj.get_rect(right = coord[0] - 1, top = coord[1])

        else:
            textobj, textrect = font.render(text, color)
            rect = textobj.get_rect(left = coord[0], top = coord[1])

        # Blit text to the screen
        self.screen.blit(textobj, rect)
    

    def zoom_camera(self, mode):
        """Method to start the zoom process"""

        self.scale = self.scale * (1 - self.game_instance.zoom_speed * mode)
        self.update_zooming_imgs()
        
        d_x = - mode * ((self.game_instance.res[0] / 2 - self.mouse_pos[0]) * self.game_instance.zoom_speed / self.scale)
        d_y = mode * ((self.game_instance.res[1] / 2 - self.mouse_pos[1]) * self.game_instance.zoom_speed / self.scale)
        
        # Move bodies to mimic zoom towards mouse position, cannot tell why the factor 10 is needed but it seemed necessary
        for body in self.game_instance.mission.bodies:
            body.pos[0] = body.pos[0] + d_x
            body.pos[1] = body.pos[1] + d_y
            
        self.center[0] = self.center[0] + d_x
        self.center[1] = self.center[1] + d_y


    def move_camera(self):
        """Method to move the camera, however actually all bodies are moves giving the effect of a moving camera"""

        # Determine the difference in mouse position since last frame
        d_x = self.mouse_pos[0] - self.mouse_pos_old[0]
        d_y = self.mouse_pos_old[1] - self.mouse_pos[1]

        # Move ever body to its new position, adding the difference in mouse position
        for body in self.game_instance.mission.bodies:
            body.pos[0] = body.pos[0] + d_x / self.scale
            body.pos[1] = body.pos[1] + d_y / self.scale

        # Update camera center attribute
        self.center[0] = self.center[0] + d_x / self.scale
        self.center[1] = self.center[1] + d_y / self.scale


    def is_on_screen(self, body_center_topleft, body_img_size):
        """Method to determine whether or not an object is visible on screen"""

        # Determine bounds of the objects image with top-left reference
        l_bound = body_center_topleft[0] - body_img_size[0] / 2
        r_bound = body_center_topleft[0] + body_img_size[0] / 2
        b_bound = body_center_topleft[1] + body_img_size[1] / 2
        t_bound = body_center_topleft[1] - body_img_size[1] / 2

        # Determine whether or not any part of the body is in the screen space for both directions separately
        in_screen_x = (0 <= r_bound <= self.game_instance.res[0]) or (0 <= l_bound <= self.game_instance.res[0]) or (l_bound <= 0 and r_bound >= self.game_instance.res[0])
        in_screen_y = (0 <= b_bound <= self.game_instance.res[1]) or (0 <= t_bound <= self.game_instance.res[1]) or (t_bound <= 0 and b_bound >= self.game_instance.res[1])
        
        
        
        # Return true if any part of the object is visible on the screen, false if not   
        return in_screen_x and in_screen_y


    def draw_endscreen(self):
        """Method to draw the end screen once mission is over"""

        # If the mission is successful, show text that the mission was successful
        if self.game_instance.mission_state == 1:
            self.draw_text('Mission successful!', 50, (0,255,0), [self.game_instance.res[0] / 2, 100], 'center')

        # If mission was not successful, show text that the mission failed
        elif self.game_instance.mission_state > 1:
            self.draw_text('Mission failed.', 50, (255,0,0), [self.game_instance.res[0] / 2, 100], 'center')

            # If the failure reason was atmospheric reentry, draw text showing this reason
            if self.game_instance.mission_state == 2:
                self.draw_text('You deorbited.', 20, (255,255,255), [self.game_instance.res[0] / 2, 160], 'center')

            # If the failure reason was a crash with the target
            elif self.game_instance.mission_state == 3:
                self.draw_text('You collided with the target at high velocity.', 20, (255,255,255), [self.game_instance.res[0] / 2, 160], 'center')

            # If the failure reason was a crash with another orbiting body
            elif self.game_instance.mission_state == 4:
                self.draw_text('You collided with another orbiting body at high velocity.', 20, (255,255,255), [self.game_instance.res[0] / 2, 160], 'center')

            # If the failure reason was a crash with debris, draw text showing this reason
            elif self.game_instance.mission_state == 5:
                self.draw_text('You collided with debris.', 20, (255,255,255), [self.game_instance.res[0] / 2, 160], 'center')
                
            # If target has crashed with another orbiting body
            elif self.game_instance.mission_state == 6:
                self.draw_text('The target has been hit by another orbiting body.', 20, (255,255,255), [self.game_instance.res[0] / 2, 160], 'center')
                
            # If target has crashed with another orbiting body
            elif self.game_instance.mission_state == 8:
                self.draw_text('The target has been hit by debris.', 20, (255,255,255), [self.game_instance.res[0] / 2, 160], 'center')
                
            

        # Show text that ENTER key now quits the game
        self.draw_text('Press ENTER to quit.', 30, (255,255,255), [self.game_instance.res[0] / 2, self.game_instance.res[1] / 2 - 15], 'center')


    def draw_orbits(self):

        if self.game_instance.mission_state == 0:

            main_body = None

            for body in self.game_instance.mission.bodies:
                if body.type == -1:
                    main_body = body
                    break

            for body in self.game_instance.mission.bodies:
                if body.type == 1 or body.type == 2 or body.type == 3:
                    orbit_params = orbit_functions.orbit_params(self.game_instance.gravparam, main_body.pos, body.pos, body.vel)

                    ellipse_size_x = orbit_params[0][0] * self.scale
                    ellipse_size_y = orbit_params[0][1] * self.scale
                    rot_angle_rad = orbit_params[1]
                    
                    # Draw orbit ellipses only if they aren't bigger than a certain level
                    if ellipse_size_x < self.game_instance.res[1]:
                        # Draw basic orbit ellipse in horizontal orientation onto surface
                        orbit_bounding_rect = pygame.Rect(0, 0, ellipse_size_x, ellipse_size_y)
                        orbit_surface = pygame.Surface([ellipse_size_x, ellipse_size_y], pygame.SRCALPHA).convert_alpha()
                        
                        if body.type == 1:
                            color = self.game_instance.hud_color
                        elif body.type == 2:
                            color = (0,255,0)
                        elif body.type == 3:
                            color = (255,0,0)
                        
                        pygame.draw.ellipse(orbit_surface, color, orbit_bounding_rect, 2)
                        center_before_rot = orbit_surface.get_rect().center
                        
                        # Center to ellipse focus vector before rotation
                        center_to_focus_vector = pygame.math.Vector2(ellipse_size_x / 2 - orbit_params[2][0] * self.scale, 0)

                        # Center to ellipse focus vector after rotation
                        rot_center_to_focus_vector = center_to_focus_vector.rotate(math.degrees(rot_angle_rad))
                        
                        # Rotate surface that contains the ellipse
                        rot_orbit_surface = pygame.transform.rotate(orbit_surface, math.degrees(rot_angle_rad))
                        
                        # Set center of new rotated ellipse to center of old ellipse
                        rot_orbit_surface.get_rect().center = center_before_rot
                        
                        # Build blitting coordinates
                        x_pos = self.center_to_topleft(self.pos_to_center_coord(self.center))[0] - rot_center_to_focus_vector[0]
                        y_pos = self.center_to_topleft(self.pos_to_center_coord(self.center))[1] + rot_center_to_focus_vector[1]
                        
                        # Create new rectangle from rotated orbit ellipse and center it at the position calculated
                        newrect = rot_orbit_surface.get_rect(center = [x_pos, y_pos])
                        
                        self.screen.blit(rot_orbit_surface, newrect)
    
    def create_background(self, res):
        bg_surf = pygame.Surface(res)
        bg_px_arr = pygame.PixelArray(bg_surf)
        bg_surf.fill((0,0,0))
        
        for bgstars in range(1000):
            x = random.randint(0,res[0]-1)
            y = random.randint(0,res[1]-1)
            
            bg_px_arr[x,y] = (255,255,255)
        
        
        # Draw larger, colored stars
        for fgstars in range(100):
            color_index = random.randint(0,255)
            
            b = color_index
            if b > 200:
                r = int(b * 0.75)
                g = random.randint(int(0.75*b),b)
            else:
                r = 255-b
                g = random.randint(0,int(0.75*r))
            
            
            
            x = random.randint(0,res[0]-1)
            y = random.randint(0,res[1]-1)
            
            radius = random.randint(1,5) // 2
            
            pygame.draw.circle(bg_surf, (r,g,b), (x,y), radius)
        
        return bg_surf
    
    
    def play_music(self): 
        tracklist = os.listdir('music')
        
        newtrack = random.choice(tracklist)
        while newtrack == self.currtrack:
            newtrack = random.choice(tracklist)
        
        self.currtrack = newtrack
        
        trackpath = os.path.join('music', newtrack)
        
        pygame.mixer.music.load(trackpath)
        pygame.mixer.music.play()
        pygame.mixer.music.set_volume(0.05)