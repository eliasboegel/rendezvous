# Description
Rendezvous is a game made to learn the very basics of 2D orbital dynamics. You find yourself in control of a spacecraft in orbit around a planet. Your mission is to perform an orbital rendezvous with a target spacecraft. To perform an orbital rendezvous, you need to meet the target on its orbit, but watch out that you are not too fast and crash into the target! During some missions, there may be other spacecraft orbiting the planet, which you need to avoid to stop yourself from crashing your spacecraft before the rendezvous with the target is performed. The mission is successful once the rendezvous was performed at a safe velocity. The mission is failed if the player deorbits, crashes into another object at high velocities, or if the target is hit by other objects.

Since this game can be a bit difficult to start off, here are a few tips: If you burn forwards or backwards, the opposite side of the orbit will either be raised or lowered. Generally you want to roughly align your orbit with the target object's orbit, but to sync up the orbits you have two options. Having an orbit smaller than the target orbit means that you will catch up to the target, having an orbit larger than the target orbit means that you will drop off the target, meaning that the target can catch up to you in a few revolutions of the orbit. This is generally the method to get the rendezvous done. Of course, you should use as little as possible propellant for this.

# Notes
The game is run by running rendezvous.py

The game takes several seconds to load. This is because of per-pixel texture generation for planet and background. Because of imperfections in the noise algorithm, every pixel has to be processed twice (noise's perlin-simplex noise functions do not return a normalized result, the values range approximately between 0.3 and 0.7 instead of a clean 0 and 1, meaning that after noise generation the values need to be normalized before per-pixel color processing can begin. For the planet texture, color is determined by 3 different noise maps: elevation, temperature and humidity. To assign a color to each occuring combination of the 3 noise maps, a 3D colorspace, built from predefined vertices (coordinates: elevation, temperature, humidity; value: associated color) is generated and linearly interpolated in 3D to produce a smooth gradient between colors. This whole generation process is why the game takes a moment to load. While loading, a splash screen is displayed to let the player know that the program hasn't crashed and is loading.

The visuals and sound effect of the propulsion system depends on the specific impulse that the player spacecraft has. If the specific impulse is over 500s, the propulsion is assumed to be electric, if it is below 500s it is assumed to be a chemical system.

# Configuration
The game has a config file with some limited options:
resolution : [width,height] The desired resolution at which the game is run, this has to be smaller or equal to your screen resolution, otherwise the game will not run
- fullscreen : 0 = Window mode, 1 = Fullscreen mode
- fps : Target frame rate, the higher the framerate, the better the simulation quality
- hud_color' : [r,g,b] The color of the HUD in RGB format
- default_timefactor : The simulation speed that the game starts with
- timefactor_mult' : The multiplier with which the simulation speed is modified using the controls
- zoom_speed : A setting of how fast the camera zooms in and out
- planet_res : Resolution of the planet texture, low values significantly reduce loading time but also significantly reduce visual quality, 500 should be a good balance between loading time and quality and 1000 has great quality with acceptable load times
- generate_nebulae : Flag of whether or not nebulae should be randomly generated for the background. Disabling this gives a faster load time with reduced visual fidelity. 0 = don't generate nebulae; 1 = generate nebulae

# Missions
The game can run either predefined missions, each in their individual file in the subfolder 'missions' (4 preset missions are provided as examples) or a completely random mission scenario can be generated. Which option the player would like to chose is determined when running the game. The player can either enter the name of one of the missions in the 'mission' subfolder, or enter 'r' to generate a randomized mission scenario. The mission files that the preset missions are defined in follow the syntax of python dictionaries (see example missions).

# Controls
- Left mouse button: Drag around the camera while holding LMB
- Scroll wheel: Zoom the camera in and out
- Right mouse button: Fire spacecraft thrusters
- Escape: Quits the game
- Up/Down arrows: Switches between direction lock modes:
		Prograde lock: Thrust accelerates in current flight path direction
		No lock: Thrust accelerates spacecraft towards current mouse position
		Retrograde lock: Thrust decelerates the spacecraft in current flight path direction
- Left/Right arrows: Increase or decrease simulation time scale: 1 = real time. The higher the number, the faster the simulation time. (Increased simulation time yields less accurate numerical integration results, however a maximum simulation time scale of 1000x has been set to prevent gross inaccuracies.

# Dependencies
- Python 3.x
- Pygame
- SciPy (for n-dimensional (here: 3D) linear interpolation, used for color gradient space)
- NumPy (for arrays)
- noise (for planet texture / nebulae generation)
	- https://pypi.org/project/noise/
	- If build fails (happens on windows occasionally due to VSC++ dependencies missing, binaries can be acquired from https://www.lfd.uci.edu/~gohlke/pythonlibs/#noise and installed via pip

# Credits
The 3 background tracks are published by NASA and originate from instrument data that has been converted to audio from NASA's Voyager mission.
