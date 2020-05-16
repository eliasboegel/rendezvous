import math
import orbiter_class



def get_grav_acc(gm, mb_pos, sc_pos):
    """Function that determines the current acceleration vector based on position in space"""

    acc = [0,0] # Declare acc (the current gravitational acceleration vector) to be a list of two items (x -and y-components of the gravitational acceleration vector)

    x_diff = sc_pos[0] - mb_pos[0]
    y_diff = sc_pos[1] - mb_pos[1]

    r = (x_diff**2 + y_diff**2)**0.5 # Determine the distance r from the spacecraft to the center of mass of the object it orbits

    acc_tot = gm / r**2 # Determine the magnitude of the gravitational acceleration through the Newtonian gravity equation

    # Decompose the magnitude of the acceleration into x- and y-components
    acc[0] = - x_diff / r * acc_tot # Determine x-component of the current gravitational acceleration
    acc[1] = - y_diff / r * acc_tot # Determine y-component of the current gravitational acceleration

    return acc

def get_vel(vel_old, acc, dt):
    """Function that determines a new velocity vector based on the old velocity vector, the current acceleration vector and the step in time"""

    vel = [0,0] # Declare vel (new velocity vector) to be a list of two items (x- and y-components of the velocity vector)

    #Numerical integration of the velocity
    vel[0] = vel_old[0] + acc[0] * dt # Determine the x-component of the new velocity vector
    vel[1] = vel_old[1] + acc[1] * dt # Determine the y-component of the new velocity vector

    return vel # Return new velocity vector

def get_pos(pos_old, vel, dt):
    """Function that determines a new velocity vector based on the old velocity vector, the current acceleration vector and the step in time"""

    pos = [0,0] # Declare pos (new position) to be a list of two items (x- and y-components of the position)

    #Numerical integration of the position
    pos[0] = pos_old[0] + vel[0] * dt # Determine the x-component of the new position
    pos[1] = pos_old[1] + vel[1] * dt # Determine the y-component of the new position

    return pos # Return the new position

def orbit_params(gm, main_body_pos, pos, vel):

    rel_pos_x = pos[0] - main_body_pos[0]
    rel_pos_y = pos[1] - main_body_pos[1]

    r = (rel_pos_x**2 + rel_pos_y**2)**0.5

    # Angular momentum calculation (result of cross product pos x vel with 3rd component = 0)
    h = rel_pos_x * vel[1] - rel_pos_y * vel[0]

    # Calculation of the eccentricity vector
    ecc = [vel[1] * h / gm - rel_pos_x / r, - vel[0] * h / gm - rel_pos_y / r]

    # Scalar eccentricity value
    e = (ecc[0]**2 + ecc[1]**2)**0.5 

    # Semi-major axis
    a = h**2 / (gm * (1 - e**2))

    # Distance of periapsis and apoapsis from main body
    r_periapsis = a * (1 - e) 
    r_apoapsis = a * (1 + e)

    # Angle at the center of the main body from positive x-axis to periapsis and apoapsis
    angle_periapsis = math.atan2(ecc[1], ecc[0])
    angle_apoapsis = angle_periapsis + math.pi

    # Set orbit bounding ellipse parameters
    ellipse_length = 2 * a
    ellipse_width = 2 * (a**2 * (1 - e**2))**0.5 # Ellipse width = 2 * b
    ellipse_angle = angle_periapsis

    # Return orbit parameters as list
    return [[ellipse_length,ellipse_width], ellipse_angle, [r_periapsis, r_apoapsis]]

def collision_check(orbiter1, orbiter2, coll_dist, safe_vel):
    # Calculation of the distance between the two objects, if one of them is the main body then the radius is subtracted
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