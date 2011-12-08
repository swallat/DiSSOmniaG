'''
Created on 07.12.2011

@author: Sebastian Wallat
'''
from random import *
import string

def random_password():
    """ Create a password of random length between 10 and 20
        characters long, made up of numbers and letters.
    """
    chars = string.ascii_letters + string.digits
    return "".join(choice(chars) for x in range(randint(10, 20)))