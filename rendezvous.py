import os
from rendezvous_class import Rendezvous

# Read available missions from 'missions' subfolder
try:
    missions_available = os.listdir('missions')
    
    # Print list of available missions
    print('Available missions: ')
    for mission in missions_available:
        print(mission.split('.')[0])

    # Ask user to select either random mission generation or a premade mission
    while 1:
        text = input("Please select mission to load or type 'r' to generate a random mission: ")
        
        text_with_extension = text + '.txt'
        
        if text == 'r':
            selection = 'r'
            break
        
        if text_with_extension in missions_available:
            selection = text
            break
        else:
            print('Selected mission not available, please try again.')
    
except FileNotFoundError:
    selection = 'r'


# Run game with selected mission
activemission = Rendezvous(selection)