# -*- coding: utf-8 -*-
"""
Created on 11.09.2011

@author: Sebastian Wallat
"""

import logging, argparse, os
from colorama import Fore, Style, Back
import sys, time
import getpass
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import dissomniag
from dissomniag.utils import CliMethodABCClass

log = logging.getLogger("cliApi.ManageVms")

class vms(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
class addVm(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
class delVm(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
class vmAddInterface(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
class startVM(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
class stopVM(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
