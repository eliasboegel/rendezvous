import pygame
import random
import noise
import math
import scipy.interpolate as interp
import numpy as np
import matplotlib.pyplot as plt

def gen_planet(planet_res, planet_radius, planet_atm_thickness, roughness):
    """
    Function to generate a random planet texture
    
    Arguments:
        planet_res : [int, int] - Desired resolution of the planet image
        planet_radius: float - Planet radius [m]
        planet_atm_thickness: float - Planet atmosphere thickness [m]
        roughness : int - Roughness of the planet texture
        
    Return values:
        body_surface : pygame.Surface - Complete texture of the planet
    """
    
    # Create several helpful variables
    # Radius of the outmost part of the atmosphwere [m]
    atm_radius = planet_radius + planet_atm_thickness * 2
    
    # Planet radius in px on the screen
    planet_radius_px = int(planet_res / 2)
    
    # Atmosphere radius in pixels on the screen
    atm_radius_px = int(atm_radius / planet_radius * planet_res / 2)
    
    # Atmosphere thickness in pixels on the screen
    atm_thickness_px = int(planet_atm_thickness * 2 / planet_radius * planet_res / 2)
    
    
    
    ### PLANET SURFACE GENERATION
    
    # Set step sized for elevation, temperature and humidity map; is a measure of how accurate and how smooth the color gradients will be
    n_elevation_steps = 25
    n_temperature_steps = 8
    n_humidity_steps = 3
    
    # Generate either earth-like planet with earth-like color scheme, or a randomly colored planet, may look like Mars or a gas planet, both options have 50% probability
    # Earth-like planet
    if random.random() < (1/2):
        # Set the base color to the colorspace default
        base_color = [-1, -1, -1]
        
        # Set the water color to the colorspace default
        water_color = [-1, -1, -1]
        
        # Set the water color to blue with a slightly green hue
        atm_color = [0, 96, 255]
        
        # Enable forest effect generation
        trees = 1
        
        # Randomize ice_transition temperature between 0 and 0.1, temperature at which land starts transitioning to arctic climate
        ice_temperature = random.random() * 0.1
        
        # Randomize fraction of the planet is covered with clouds between 0% and 50%
        cloud_amt = random.random() * 0.5
        
    # Randomly colored planet
    else:
        # Generate random planet color
        base_color = [random.randint(32,255), random.randint(32,255), random.randint(32,255)]
        
        # Vary water and atmosphere color slightly from base color
        bcolor = pygame.Color(base_color[0], base_color[1], base_color[2])
        h, s, l, a = bcolor.hsla
        h_water = h + 15
        h_atm = h - 15
        
        # Set water color
        bcolor.hsla = h_water, s, l, a
        water_color = [bcolor.r, bcolor.g, bcolor.b]
        
        # Set atmosphere color
        bcolor.hsla = h_atm, s, l, a
        atm_color = [bcolor.r, bcolor.g, bcolor.b]
        
        # Disable forestation effect (due to bad-looking results with randomized colors)
        trees = 0
        
        # Randomize if poles have ice caps or not, 50% chance for each case
        # No ice caps on poles
        if random.random() < 0.5:
            ice_temperature = 0
            
        # Ice caps on poles
        else:
            ice_temperature = random.random() * 0.1
            
        # Randomize fraction of the planet is covered with clouds between 0% and 80%
        cloud_amt = random.random() * 0.8
    
    
    # Water elevation, elevation at which the water-land transition happens, randomize between 0 and 1, 0 means no water, 1 means only water
    water_level = random.random()
    
    # Set elevation above which land transitions to mountainous, summit environment
    mountain_level = 0.8
    
    # Randomize threshold temperature after which desert colors may be present, values range from 0.4 to 0.7
    desert_temperature = 0.4 + 0.3 * random.random()
    
    
    # Create new (alpha-enabled) planet surface with the size of the planet radius [px] on the screen and create PixelArray for pixel-wise access
    planet_surface = pygame.Surface([planet_radius_px * 2, planet_radius_px * 2], pygame.SRCALPHA)
    planet_pxarr = pygame.PixelArray(planet_surface)
    
    # Generate 3D colorspace that contains all used colors
    cspace = colorspace_3d_linear_interp(n_elevation_steps, n_temperature_steps, n_humidity_steps, base_color, water_color, water_level, ice_temperature, mountain_level, desert_temperature)
    
    # Display slice of 3D colorspace for debugging or color point set adjustments
    #show_grad(cspace, 0)
    
    
    # Generate different seeds for elevation, temperature, humidity, tree and cloud noise maps
    elevation_seed = random.randint(0,1000)
    temperature_seed = random.randint(0,1000)
    humidity_seed = random.randint(0,1000)
    tree_seed = random.randint(0,1000)
    cloud_seed = random.randint(0,1000)
    
    # Declare noise map lists
    screen_coords_lst = []
    elevation_lst = []
    temperature_lst = []
    humidity_lst = []
    tree_lst = []
    cloud_lst = []
    
    # Loop through all pixels contained in planet
    for i in range(1,planet_res): # X-axis
        for j in range(1,planet_res): # Y-axis
            
            # Draw round shape, generate perlin noise only for pixels contained in planet shape
            d = ((planet_radius_px - i)**2 + (planet_radius_px - j)**2)**0.5
            if d < planet_radius_px:
                
                # Create normalized value for distance of current pixel from center of the planet, Value limits: 1 (Pixel is on the edge), 0 (Pixel is in the center)
                d_norm = d/planet_radius_px
                
                # Create gradient variable, taken from circle function x^2 + y^2 = z^2, but for unit circle
                grad = (1-d_norm**2)**0.5
                
                # Set center coordinates for noise generation function
                noise_center_coord_x = (- 2 * roughness + i*roughness/planet_res)
                noise_center_coord_y = (- 2 * roughness + j*roughness/planet_res)
                
                
                # Generate elevation, temperature and humidity from 3D perlin-simplex noise. Only 2D needed, 3rd dimension used for randomization
                elevation = (noise.pnoise3(noise_center_coord_x, noise_center_coord_y, elevation_seed, 20) + 1) / 2
                temperature = ((noise.pnoise3(noise_center_coord_x, noise_center_coord_y, temperature_seed, 8) + 1) / 2) * (- math.cos(2 * math.pi * j / planet_res) + 1) / 2
                humidity = (noise.pnoise3(noise_center_coord_x, noise_center_coord_y, humidity_seed, 20) + 1) / 2
                tree = (noise.pnoise3(noise_center_coord_x, noise_center_coord_y, tree_seed, 20) + 1) / 2
                cloud = (noise.pnoise3(noise_center_coord_x / 2, noise_center_coord_y * 2, cloud_seed, 20) + 1) / 2
                
                # append noise map lists
                screen_coords_lst.append([i,j])
                elevation_lst.append(elevation)
                temperature_lst.append(temperature)
                humidity_lst.append(humidity)
                tree_lst.append(tree)
                cloud_lst.append(cloud)
                
    
    # Convert noise map lists to numpy arrays to enable batch processing of the data (needed for normalization of values)
    elevation_arr = np.array(elevation_lst)
    temperature_arr = np.array(temperature_lst)
    humidity_arr = np.array(humidity_lst)
    tree_arr = np.array(tree_lst)
    cloud_arr = np.array(cloud_lst)
    
    
    # Normalize perlin noise values, necessary since the noise output never really gets close to 0 and 1 but stays between around 0.3 and 0.7 if not normalized, 0.99999 added since perfectly normalized values caused errors that I did not have time to fix
    elevation_arr_norm = (elevation_arr - elevation_arr.min()) / (elevation_arr.max() - elevation_arr.min()) * 0.99999
    temperature_arr_norm = (temperature_arr - temperature_arr.min()) / (temperature_arr.max() - temperature_arr.min()) * 0.99999
    humidity_arr_norm = (humidity_arr - humidity_arr.min()) / (humidity_arr.max() - humidity_arr.min()) * 0.99999
    tree_arr_norm = (tree_arr - tree_arr.min()) / (tree_arr.max() - tree_arr.min()) * 0.99999
    cloud_arr_norm = (cloud_arr - cloud_arr.min()) / (cloud_arr.max() - cloud_arr.min()) * 0.99999
         
    
    # Loop through all points in the noise map lists        
    for point in range(len(screen_coords_lst)):
        
        # Get pixel color from 3D color space and create pygame color from it
        px_color = cspace[int(elevation_arr_norm[point]*n_elevation_steps)][int(temperature_arr_norm[point]*n_temperature_steps)][int(humidity_arr_norm[point]*n_humidity_steps)]
        color = pygame.Color(px_color[0], px_color[1], px_color[2])
        
        # Get HSLA color values to make forestation effect generation easier
        h, s, l, a = color.hsla
        
        # COLOR POSTPROCESSING
        # Forestation effect, works through lowering lightness of a pixel if it meets several conditions
        if (trees and # Forestation effect enabled?
            tree_arr_norm[point] > 0.5 and # Only generate forestation if tree noise map value is over 0.5
            (water_level + 0.02) < elevation_arr_norm[point] < mountain_level and # Only generate forestation if elevation is between water and mountain level, with some margin
            (ice_temperature + 0.1) < temperature_arr_norm[point] and # Only generate forestation if temperature is over the ice temperature, with some margin
            humidity_arr_norm[point] > 0.5): # Only generate forestation if humidity is over 0.5
            
            # Lower lightness to create forestation effect
            l = l / 2
            
            # Update color with new HSLA values
            color.hsla = h, s, l, a
        
        # Cloud generation
        # Generate clouds if cloud noise map value is lower than the cloud fraction that was randomized
        if cloud_arr_norm[point] < cloud_amt:
            # Get color rgb values from current pixel color
            r = color.r
            g = color.g
            b = color.b
            
            # Blend current pixel color with white to create cloud effect
            color_with_cloud = blend_to_white([r,g,b], 1-cloud_arr_norm[point])
            
            # Update color with new RGB values
            color.r = color_with_cloud[0]
            color.g = color_with_cloud[1]
            color.b = color_with_cloud[2]
            
            
        # Generate atmospheric glow from increasing view angles to the side of the planet
        # Get distance of pixel from center of planet
        d = ((planet_radius_px - screen_coords_lst[point][0])**2 + (planet_radius_px - screen_coords_lst[point][1])**2)**0.5
        
        # Produce normalized distance value
        d_norm = d/planet_radius_px
        
        # Create gradient variable that is 1 in the center and 0 at the edges of the planet
        grad = (1-d_norm**2)**0.5
        
        # Apply atmospheric tint
        # Get RGB values from current pixel color
        r = color.r
        g = color.g
        b = color.b
        
        # Find atmosphere color at current pixel
        atm_color_curr_r = atm_color[0] + (255-atm_color[0]) * grad
        atm_color_curr_g = atm_color[1] + (255-atm_color[1]) * grad
        atm_color_curr_b = atm_color[2] + (255-atm_color[2]) * grad
        
        # Blend atmosphere color with current pixel color using blend mode Multiply to create atmospheric glow effect
        color_with_atm = blend_multiply([r,g,b], [atm_color_curr_r, atm_color_curr_g, atm_color_curr_b])
        
        # Update color with new RGB values
        color.r = color_with_atm[0]
        color.g = color_with_atm[1]
        color.b = color_with_atm[2]
        
        # Apply atmosphere glow on texture (to replicate bight light scattering when looking through the atmosphere at a shallow angle)
        h, s, l, a = color.hsla
        l = l + (100 - l) * (1 - grad)**1.5 * 0.75
        s = s * grad
        
        # Update color with new HSLA values
        color.hsla = h, s, l, a
        
        # Set pixel to new color
        planet_pxarr[screen_coords_lst[point][0],screen_coords_lst[point][1]] = color

    # Close pixel array to enable blitting
    planet_pxarr.close()
    
    

    ### PLANET ATMOSPHERE GRADIENT GENERATION
    
    # Create new alpha-enabled surface to draw atmosphere layers and finall the planet texture on
    body_surface = pygame.Surface([atm_radius_px * 2, atm_radius_px * 2], pygame.SRCALPHA)
    
    # Specify number of layers out of which to draw the atmosphere
    n_atm_layers = 50

    # Draw each atmosphere layer
    for layer in range(n_atm_layers):

        # Set layer radius in pixels, smaller radius for ever layer draw to give effect of different atmosphere layers
        layer_radius = int(atm_radius_px - atm_thickness_px / (n_atm_layers) * layer)
        
        # Grade color from white (innermost layer) to atm_color (at half drawn atmosphere thickness), outer half of the layer are atm_color, but alpha changes
        # Inner layers
        if layer > n_atm_layers / 2:
            red = atm_color[0] + (255 - atm_color[0])/(n_atm_layers/2+1)*(layer - n_atm_layers / 2)
            green = atm_color[1] + (255 - atm_color[1])/(n_atm_layers/2+1)*(layer - n_atm_layers / 2)
            blue = atm_color[2] + (255 - atm_color[2])/(n_atm_layers/2+1)*(layer - n_atm_layers / 2)
            
        # Outer layers
        else:
            red = atm_color[0]
            green = atm_color[1]
            blue = atm_color[2]
            
        # Use alpha values to create a smooth gradient
        alpha = 10 + (200 - 10)/(n_atm_layers-1)*layer
        
        # Build new layer color from RGBA values
        layer_color = (red, green, blue, alpha)

        # Draw atmosphere layer
        pygame.draw.circle(body_surface, layer_color, [atm_radius_px, atm_radius_px], layer_radius)

    # Blit atmosphere layer onto surface
    body_surface.blit(planet_surface, [atm_thickness_px, atm_thickness_px])         
    
    # Return surface   
    return body_surface
            


def colorspace_3d_linear_interp(e_res, t_res, h_res, base_color, water_color, wl, it, ml, dt):
    """
    Function to build a 3D color space using 3D linear interpolation in an unstructured grid of points
    
    Arguments:
        e_res : int - Resolution of the color space in the elevation axis
        t_res : int - Resolution of the color space in the temperature axis
        h_res : int - Resolution of the color space in the humidity axis
        base_color : [float, float, float] - RGB values of the base color to be used if a randomly colored planet is generated
        water_color : [float, float, float] - RGB values of the water color to be used if a randomly colored planet is generated
        wl : float - Water elevation threshold value
        it : float - Ice temperature threshold value
        ml : float - Mountain elevation threshold value
        dt : float - Desert temperature threshold value
    
    Return values:
        colorspace : [ [ [int, int, int], ... ], ... ] - A 3 dimensional list of color values, dimension 1: elevation, dimension 2: temperature, dimension 3: humidity
        
    Comments:
        This function has a fixed unstructured grid of elevation/temperature/humidity points defined where each of the points has an associated color value
        The space between those points will be filled with interpolaed colors, done through linear interpolation of the RGB values of the colors
        The function uses different spaces for water, land and arctic environments to avoid blending between those three different environments as they require a sharp contrast
    """
    
    # Fixed unstructured grid of color points/vertices
    water_points = [ # [[elevation, temperature, moisture], color]
        # Deep water
        [[0,0,0], [255,255,255]],
        [[0,0,1], [255,255,255]],
        [[0,it,0], [0,0,10]],
        [[0,it,1], [0,0,10]],
        [[0,1,0], [0,0,10]],
        [[0,1,1], [0,0,10]],
        
        # 20% of water depth
        [[0.8*wl, 0, 0], [255,255,255]],
        [[0.8*wl, 0, 1], [255,255,255]],
        [[0.8*wl, it, 0], [0,70,110]],
        [[0.8*wl, it, 1], [0,70,110]],
        [[0.8*wl, 1, 0], [0,80,110]],
        [[0.8*wl, 1, 1], [0,80,110]],
        
        # Shallow water
        [[wl, 0, 0], [255,255,255]],
        [[wl, 0, 1], [255,255,255]],
        [[wl, it, 0], [10,140,190]],
        [[wl, it, 1], [10,140,190]],
        [[wl, 1, 0], [0,175,225]],
        [[wl, 1, 1], [0,175,225]]
    ]
    
    land_points = [
        # Land
        [[wl, 0.0, 0], [255,255,255]],
        [[wl, 0.0, 1], [255,255,255]],
        [[wl, it, 0], [110,160,125]],
        [[wl, it, 1], [50,160,90]],
        [[wl, 1.0, 0], [200,200,0]],
        [[wl, 1.0, 1], [160,190,0]],
        
        [[ml, 0.0, 0], [255,255,255]],
        [[ml, 0.0, 1], [255,255,255]],
        [[ml, it, 0], [140,175,150]],
        [[ml, it, 1], [80,140,100]],
        
        [[ml, dt, 0], [140,175,150]],
        [[ml, dt, 0.2], [140,175,150]],
        [[ml, dt, 0.25], [80,140,100]],
        [[ml, dt, 1], [80,140,100]],
        [[ml, dt+0.1, 0], [240,130,0]],
        [[ml, dt+0.1, 0.2], [240,130,0]],
        [[ml, dt+0.1, 0.25], [150,160,100]],
        [[ml, dt+0.1, 1], [150,160,100]],
        
        
        
        [[ml, 1.0, 0], [240,130,0]],
        [[ml, 1.0, 1], [150,160,100]],
        
        # Mountain
        [[ml+(1-ml)*1/5, 0, 0],[140,140,140]],
        [[ml+(1-ml)*1/5, 0, 1],[140,140,140]],
        [[ml+(1-ml)*1/5, 1, 0],[50,50,50]],
        [[ml+(1-ml)*1/5, 1, 1],[50,50,50]],
        
        # Summit
        [[1.0, 0, 0],[255,255,255]],
        [[1.0, 0, 1],[255,255,255]],
        [[1.0, 1, 0],[100,100,100]],
        [[1.0, 1, 1],[100,100,100]]
    ]
    
    arctic_points = [
        [[0, 0, 0],[200,200,255]],
        [[0, 0, 1],[200,200,255]],
        [[0, it, 0],[150,150,255]],
        [[0, it, 1],[150,150,255]],
        [[1, 0, 0],[200,225,255]],
        [[1, 0, 1],[200,225,255]],
        [[1, it, 0],[130,160,255]],
        [[1, it, 1],[130,160,255]]
    ]
    
    
    # Build list for each RGB value of the water color vertices
    tmp_water = []
    water_r = []
    water_g = []
    water_b = []
    for point_index in range(len(water_points)):
        tmp_water.append(water_points[point_index][0])
        water_r.append(water_points[point_index][1][0])
        water_g.append(water_points[point_index][1][1])
        water_b.append(water_points[point_index][1][2])
    
    # Build list for each RGB value of the land color vertices  
    tmp_land = []
    land_r = []
    land_g = []
    land_b = []
    for point_index in range(len(land_points)):
        tmp_land.append(land_points[point_index][0])
        land_r.append(land_points[point_index][1][0])
        land_g.append(land_points[point_index][1][1])
        land_b.append(land_points[point_index][1][2])
        
    # Build list for each RGB value of the arctic color vertices 
    tmp_arctic = []
    arctic_r = []
    arctic_g = []
    arctic_b = []
    for point_index in range(len(arctic_points)):
        tmp_arctic.append(arctic_points[point_index][0])
        arctic_r.append(arctic_points[point_index][1][0])
        arctic_g.append(arctic_points[point_index][1][1])
        arctic_b.append(arctic_points[point_index][1][2])
    

    
    
    # Declare color space list
    colorspace = []

    # Loop through all possible elevation/temperature/humidity combination given with respect to their resolutions
    # Loop through elevation levels
    for e in range(e_res):
        # Add plane for elevation level
        colorspace.append([])
        
        # Normalize elevation value to between 0 and 1
        e_val = e / e_res
        
        # Loop through temperature levels
        for t in range(t_res):
            # Add row of values for elevation/temperature combination
            colorspace[e].append([])
            
            # Normalize temperature value to between 0 and 1
            t_val = t / t_res
            
            # Loop through humidity levels
            for h in range(h_res):
                # Normalize humididty value to between 0 and 1
                h_val = h / h_res
                
                # interpolate each of the water, land and arctic subspaces
                
                # If the temperature value is below the ice threshold, interpolate arctic list and use color values from actic list
                if t_val < it:
                    # Interpolate arctic color subspace
                    r = interp.griddata(tmp_arctic, arctic_r, [e_val, t_val, h_val], method='linear')[0]
                    g = interp.griddata(tmp_arctic, arctic_g, [e_val, t_val, h_val], method='linear')[0]
                    b = interp.griddata(tmp_arctic, arctic_b, [e_val, t_val, h_val], method='linear')[0]
                    
                # If the elevation value is below the water level threshold, interpolate water list and use color values from water list
                elif e_val < wl:
                    # Interpolate water color subspace
                    r = interp.griddata(tmp_water, water_r, [e_val, t_val, h_val], method='linear')[0]
                    g = interp.griddata(tmp_water, water_g, [e_val, t_val, h_val], method='linear')[0]
                    b = interp.griddata(tmp_water, water_b, [e_val, t_val, h_val], method='linear')[0]
                    
                    # Apply water color modification to change hue, but only if generating a randomly colored planet
                    if not water_color == [-1,-1,-1]:
                        # Blend current native water color with desired water color using luminosity blend mode
                        color_with_base = blend_luminosity([r,g,b], water_color)
                        
                        # Update color values to reflect color blending
                        r = color_with_base[0]
                        g = color_with_base[1]
                        b = color_with_base[2]
                
                # For all other cases use the land color subspace
                else:
                    # Interpolate land color subspace
                    r = interp.griddata(tmp_land, land_r, [e_val, t_val, h_val], method='linear')[0]
                    g = interp.griddata(tmp_land, land_g, [e_val, t_val, h_val], method='linear')[0]
                    b = interp.griddata(tmp_land, land_b, [e_val, t_val, h_val], method='linear')[0]
                    
                    # Apply base color modification to change hue, but only if generating a randomly colored planet
                    if not base_color == [-1,-1,-1]:
                        # Blend current native land color with desired base color using soft light blend mode
                        color_with_base = blend_softlight([r,g,b], base_color)
                        
                        # Update color values to reflect color blending
                        r = color_with_base[0]
                        g = color_with_base[1]
                        b = color_with_base[2]
                
                # Add generated/interpolated color to color space
                colorspace[e][t].append([int(r),int(g),int(b)])
    
    # Return color space
    return colorspace
    
    
    
def show_grad(colorspace, h):
    """
    Function for debugging and tweaking colorspace parameters
    
    Arguments:
        colorspace : [ [ [int, int, int], ... ], ... ] - A color space as produced by colorspace_3d_linear_interp()
        h : int - Humidity value at which to slice the color space and display values in 2D plot
    """

    # Declare img (2D list of colors)
    img = []

    # Set step counts to 3D color space dimensions
    e_steps = len(colorspace)
    t_steps = len(colorspace[0])
    h_steps = len(colorspace[0][0])
    h_coord = h * (h_steps-1)

    # Loop through elevation levels
    for elev in range(e_steps):
        # Add row for elevation level
        img.append([])
        
        # Loop through temperature levels
        for temp in range(t_steps):
            # Add color for current elevation/temperature combination
            img[elev].append(colorspace[elev][temp][h_coord])

    # Draw plot of the slide of the color space
    plt.imshow(img, origin='lower', extent=[0,t_steps,0,e_steps])
    #plt.xticks(np.linspace(0,e_steps,11), np.around(np.linspace(0,1,11),1))
    #plt.yticks(np.linspace(0,t_steps,11), np.around(np.linspace(0,1,11),1))
    plt.xlabel('Temperature')
    plt.ylabel('Elevation')
    plt.show()

def blend_multiply(color1, color2):
    """
    Function to blend two colors using the Multiply blend mode
    
    Arugments:
        color1 : [float, float, float] - First color as a list of the 3 RGB values (0-255)
        color2 : [float, float, float] - Second color as a list of the 3 RGB values (0-255)
        
    Return values:
        color : [int, int, int] - Blended color as list of the 3 RGB values (0-255)
    """
    
    # Unpack and normalize RGB values
    r1 = color1[0] / 255
    g1 = color1[1] / 255
    b1 = color1[2] / 255
    r2 = color2[0] / 255
    g2 = color2[1] / 255
    b2 = color2[2] / 255
    
    # Perform Multiply blending
    r = r1 * r2
    g = g1 * g2
    b = b1 * b2
    
    # Return blended color as list of RGB values (integers from 0-255)
    return [int(r*255),int(g*255),int(b*255)]

def blend_softlight(color1, color2):
    """
    Function to blend two colors using the Soft Light blend mode
    
    Arugments:
        color1 : [float, float, float] - First color as a list of the 3 RGB values (0-255)
        color2 : [float, float, float] - Second color as a list of the 3 RGB values (0-255)
     
    Return values:
        color : [int, int, int] - Blended color as list of the 3 RGB values (0-255)
    """
    
    # Unpack and normalize RGB values
    r1 = color1[0] / 255
    g1 = color1[1] / 255
    b1 = color1[2] / 255
    r2 = color2[0] / 255
    g2 = color2[1] / 255
    b2 = color2[2] / 255
    
    # Perform Soft Light blending
    r = ((1-2*r1)*r2**2+2*r1*r2)
    g = ((1-2*g1)*g2**2+2*g1*g2)
    b = ((1-2*b1)*b2**2+2*b1*b2)
    
    # Return blended color as list of RGB values (integers from 0-255)
    return [int(r*255),int(g*255),int(b*255)]

def blend_luminosity(color1, color2):
    """
    Function to blend two colors using the Luminosity blend mode
    
    Arugments:
        color1 : [float, float, float] - First color as a list of the 3 RGB values (0-255)
        color2 : [float, float, float] - Second color as a list of the 3 RGB values (0-255)
     
    Return values:
        color : [int, int, int] - Blended color as list of the 3 RGB values (0-255)
    """
    
    # Create pygame.Color objects from color values in order to use HSLA conversion functions
    c1 = pygame.Color(int(color1[0]), int(color1[1]), int(color1[2]))
    c2 = pygame.Color(int(color2[0]), int(color2[1]), int(color2[2]))
    
    # Get HSLA values
    h1, s1, l1, a1 = c1.hsla
    h2, s2, l2, a2 = c2.hsla
    
    # Perform Luminosity blending
    h = h2
    s = s2
    l = l1
    
    # Update first color to blended color
    c1.hsla = h, s, l, a1
    
    # Return blended color as list of RGB values (integers from 0-255)
    return [c1.r,c1.g,c1.b]

def blend_to_white(color1, alpha):
    """
    Function to blend one color to white using alpha blending
    
    Arugments:
        color1 : [float, float, float] - First color as a list of the 3 RGB values (0-255)
        alpha : float - Alpha value from 0 to 1
     
    Return values:
        color : [int, int, int] - Blended color as list of the 3 RGB values (0-255)
    """
    
    # Get RGB values from color
    r1 = color1[0]
    g1 = color1[1]
    b1 = color1[2]
    
    # Perform alpha blending with white
    r = r1 + (255-r1) * alpha
    g = g1 + (255-g1) * alpha
    b = b1 + (255-b1) * alpha
    
    # Return blended color as list of RGB values (integers from 0-255)
    return [int(r),int(g),int(b)]