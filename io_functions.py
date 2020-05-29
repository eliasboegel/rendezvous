import os, ast

def read_file(folder, filename):
    """
    Function to read a file into a python dictionary
    
    Arguments:
        folder : (String) - The name of the subfolder under the programs root directory containing the (mission) file
        filename : (String) - The file name of the (mission) file to be read into the dictionary
        
    Return:
        dictionary : A python dictionary containing all differen bodies with their properties that were read from the file
    """

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
