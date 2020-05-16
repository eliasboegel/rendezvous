import os
import io_functions
import orbiter_class



class Mission:

    def __init__(self, mission_folder, mission_file):
        """Mission class constructor"""

        # Read mission file into a dictionary
        mission = io_functions.read_file(mission_folder, mission_file)

        # Initialize a list of all bodies
        self.bodies = []

        # Loop through all bodies in the mission dictionary
        for o, o_data in mission.items():

            # If the body is the player body, create new player object and append list of bodies
            if o_data['type'] == 'player':
                self.bodies.append(    orbiter_class.Player(o_data['pos_init'],
                                                            o_data['vel_init'],
                                                            o_data['mass_dry'],
                                                            o_data['mass_prop'],
                                                            o_data['i_sp'],
                                                            o_data['img'],
                                                            o_data['bodyscale']))

            # If the body is the main body, create a new main body object and append list of bodies
            elif o_data['type'] == 'mainbody':
                self.bodies.append(  orbiter_class.MainBody(o_data['mass'],
                                                            o_data['radius'],
                                                            o_data['atm_thickness'],
                                                            o_data['atm_color'],
                                                            o_data['img']))

            # If body is of another type such as 'debris' or 'hazard', create new orbiter object and append list of bodies
            else:
                self.bodies.append(   orbiter_class.Orbiter(o_data['type'],
                                                            o_data['pos_init'],
                                                            o_data['vel_init'],
                                                            o_data['img'],
                                                            o_data['bodyscale']))
