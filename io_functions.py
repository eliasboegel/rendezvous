import os, ast

def read_file(folder, filename):
    """Function to read a file into a python dictionary"""

    # Create path from current working directory, folder name and file name
    path = os.path.join(os.getcwd(), folder, filename)

    # Open file
    file = open(path, 'r')

    # Read file content into variable
    text = file.read()

    # Convert file contents into python dictionary
    dictionary = ast.literal_eval(text)

    # Close file
    file.close()

    #Return the dictionary
    return dictionary
