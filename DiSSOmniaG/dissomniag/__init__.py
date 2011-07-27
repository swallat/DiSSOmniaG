import os, logging, sys



import config

import utils.Logging

log = logging.getLogger("dissomniag.__init__")
"""
Logger
"""

sys.path.insert(0, os.path.abspath(os.curdir))


from dbAccess import Session, Base
from utils import *
import api
import cliApi
import auth
from server import startServer

