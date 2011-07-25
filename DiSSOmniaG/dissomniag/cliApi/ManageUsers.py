# -*- coding: utf-8 -*-
"""
Created on 23.07.2011

@author: Sebastian Wallat
"""
import argparse
from colorama import Fore, Style, Back
import sys

import dissomniag
from dissomniag.auth import User, PublicKey
from dissomniag.utils import CliMethodABCClass

class listUsers(CliMethodABCClass.CliMethodABCClass):

    def implementation(self, *args, **kwargs):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        dir(self.terminal)
        
        parser = argparse.ArgumentParser(description = 'Print out all users.')
        
        parser.add_argument("-k", action = "store_true", dest = "printKeys", default = False)
        options = parser.parse_args(list(args))
        session = dissomniag.Session()
        
        for user in session.query(User).all():
            print(self.colorString(str("User: %s" % user.username), style = Style.BRIGHT))
            print(self.colorString(str("\t isAdmin: %s" % user.isAdmin), style = Style.BRIGHT))
            
            if options.printKeys:
                print(self.colorString(str("\t Public Keys: %s" % user.isAdmin), style = Style.BRIGHT))
                for key in user.publicKeys:
                    print(self.colorString(str("\t \t%s" % key.publicKey), style = Style.BRIGHT))
            print("\n")

class addUser(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        if not self.user.isAdmin:
			print(self.colorString("Permission denied: Only Admin users are allowed to add a users!", color = Fore.RED, style = Style.BRIGHT))
			return
		
        print(self.colorString("SUCCESS", color = Fore.GREEN, style = Style.BRIGHT))


class addKey(CliMethodABCClass.CliMethodABCClass):
    pass

class delUser(CliMethodABCClass.CliMethodABCClass):
	pass

class delKey(CliMethodABCClass.CliMethodABCClass):
	pass

class passwd(CliMethodABCClass.CliMethodABCClass):
	pass

