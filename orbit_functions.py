import math
import orbiter_class



def get_grav_acc(gm, mb_pos, sc_pos):
    """
    Function that determines the current acceleration vector based on position in space
    
    Arguments:
        mb_pos : [float, float] - Main body positon vector [m]
        sc_pos : [float, float] - Orbiter position vector [m]
        
    Return values:
        acc : [float, float] - Current acceleration vector [m/s^2]
    """

    # Declare acc (the current gravitational acceleration vector) to be a list of two items (x -and y-components of the gravitational acceleration vector)
    acc = [0,0]

    # Find coordinate positon difference for both x and y coordinates
    x_diff = sc_pos[0] - mb_pos[0]
    y_diff = sc_pos[1] - mb_pos[1]

    # Determine the distance r from the spacecraft to the center of mass of the object it orbits
    r = (x_diff**2 + y_diff**2)**0.5

    # Determine the magnitude of the gravitational acceleration through the Newtonian gravity equation
    acc_tot = gm / r**2

    # Decompose the magnitude of the acceleration into x- and y-components
    acc[0] = - x_diff / r * acc_tot
    acc[1] = - y_diff / r * acc_tot

    return acc

def get_vel(vel_old, acc, dt):
    """
    Function that determines a new velocity vector based on the old velocity vector, the current acceleration vector and the step in time
    
    Arguments:
        vel_old : [float, float] - Current velocity vector of the orbiter [m/s]
        acc : [float, float] - Current acceleration vector [m/s^2]
        dt : float - Time increment since last simulation step [s]
        
    Return values:
        vel : [float, float] - New veloctiy vector of the orbiter [m/s]
    """

    # Declare vel (new velocity vector) to be a list of two items (x- and y-components of the velocity vector)
    vel = [0,0]

    #Numerical integration of the velocity
    vel[0] = vel_old[0] + acc[0] * dt
    vel[1] = vel_old[1] + acc[1] * dt

    # Return new velocity vector
    return vel

def get_pos(pos_old, vel, dt):
    """
    Function that determines a new velocity vector based on the old velocity vector, the current acceleration vector and the step in time
    
    Arguments:
        pos_old : [float, float] - Current positon vector of the orbiter [m]
        vel : [float, float] - Current velocity vector of the orbiter [m/s]
        dt : float - Time increment since last simulation step [s]
    """

    # Declare pos (new position) to be a list of two items (x- and y-components of the position)
    pos = [0,0]

    #Numerical integration of the position
    pos[0] = pos_old[0] + vel[0] * dt
    pos[1] = pos_old[1] + vel[1] * dt

    # Return the new position
    return pos 

def orbit_params(gm, main_body_pos, pos, vel):
    """
    Function to determine several orbit parameters, used for display of the orbit ellipses
    
    Arguments:
        gm : float - Gravitational parameter
        main_body_pos : [float, float]] - Current position vector of the main body
        pos : [float, float] - Current position vector of the orbiter
        vel : [float, float] - Current velocity vector of the orbiter
        
    Return values:
        [ellipse_length, ellipse_width] : [float, float] - Length and width of orbit ellipse [m]
        angle_periapsis : float - Argument of pericenter with respect to the positive x-axis (angle in rad)
        [r_periapsis, r_apoapsis] : [float, float] - Distances of the periapsis and apoapsis respectively from the main body [m]
    """

    # Determine the positon of the orbiter relative to the main body center for x and y-axis
    rel_pos_x = pos[0] - main_body_pos[0]
    rel_pos_y = pos[1] - main_body_pos[1]

    # Find distance of the orbiter from the main body center
    r = (rel_pos_x**2 + rel_pos_y**2)**0.5

    # Calculation of the angular momentum of the orbiter (result of cross product pos x vel with 3rd component = 0)
    h = rel_pos_x * vel[1] - rel_pos_y * vel[0]

    # Calculation of the eccentricity vector
    ecc = [vel[1] * h / gm - rel_pos_x / r, - vel[0] * h / gm - rel_pos_y / r]

    # Scalar eccentricity value
    e = (ecc[0]**2 + ecc[1]**2)**0.5 

    # Calculation fo the semi-major axis
    a = h**2 / (gm * (1 - e**2))

    # Distance of periapsis and apoapsis from main body
    r_periapsis = a * (1 - e) 
    r_apoapsis = a * (1 + e)

    # Angle at the center of the main body from positive x-axis to periapsis and apoapsis
    angle_periapsis = math.atan2(ecc[1], ecc[0])
    angle_apoapsis = angle_periapsis + math.pi

    # Set orbit bounding ellipse parameters
    ellipse_length = 2 * a
    ellipse_width = 2 * (a**2 * (1 - e**2))**0.5 # Ellipse width = 2 * b, b was determined through basic ellipse eccentricity-major/minor axis relation

    # Return orbit parameters as list
    return [[ellipse_length,ellipse_width], angle_periapsis, [r_periapsis, r_apoapsis]]

def collision_check(orbiter1, orbiter2, coll_dist, safe_vel):
    """
    Function to check for occurance and type of collision between two objects
    
    Arugments:
        orbiter1 : Orbiter instance - Object instance of the first of the two orbiters to check for collision
        orbiter2 : Orbiter instance - Object instance of the second of the two orbiters to check for collision
        coll_dist : float - Distance at and under which a collision occurs [m]
        safe_vel : float - Velocity at and under which a collision is safe and not harmful
        
    Return values:
        Collision mode : int - Integer value representing the collision mode. Possible values: 0 (no collision), 1 (safe 'collison') and 2 (crash)
    """
    
    # Calculation of the distance between the two objects
    d_x = orbiter1.pos[0] - orbiter2.pos[0]
    d_y = orbiter1.pos[1] - orbiter2.pos[1]
    d = (d_x**2 + d_y**2)**0.5

    # Calculation of differential speed between the two objects
    v_x = orbiter1.vel[0] - orbiter2.vel[0]
    v_y = orbiter1.vel[1] - orbiter2.vel[1]
    v = (v_x**2 + v_y**2)**0.5

    if d <= coll_dist:
        if v <= safe_vel:
            return 1 # Safe collision, successful orbital rendezvous, happens if the differential speed is lower than or equal to the safe velocity
        else:
            return 2 # Unsafe/harmful collision/crash, happens if the differential speed is higher than the safe velocity
    else:
        return 0 # No collision at all, happens if the distance between the two objects is bigger than the distance required for collision