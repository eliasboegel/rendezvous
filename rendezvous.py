import os
from rendezvous_class import Rendezvous

# Read available missions from 'missions' subfolder
missions_available = os.listdir('missions')

# Print list of available missions
print('Available missions: ')
for mission in missions_available:
    print(mission.split('.')[0])

# Ask user to select mission to play
selection = input('Please select mission to load: ')

# Run game with selected mission
activemission = Rendezvous(selection + '.txt')