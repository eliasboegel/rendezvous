import os
from rendezvous_class import Rendezvous

# Read available missions from 'missions' subfolder
missions_available = os.listdir('missions')

# Print list of available missions
print('Available missions: ')
for mission in missions_available:
    print(mission.split('.')[0])

# Ask user to select either random mission generation or a premade mission
selection = input("Please select mission to load or type 'r' to generate a random mission: ")

# Run game with selected mission
activemission = Rendezvous(selection)