# -*- coding: utf-8 -*-
"""
Created on 23.07.2011

@author: Sebastian Wallat
"""
import logging
import argparse
from colorama import Fore, Style, Back
import sys
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import dissomniag
from dissomniag.auth import User, PublicKey
from dissomniag.utils import CliMethodABCClass

log = logging.getLogger("cliApi.ManageUsers")

class listUser(CliMethodABCClass.CliMethodABCClass):

    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        parser = argparse.ArgumentParser(description = 'Print out all users.', prog = args[0])
        
        parser.add_argument("-k", action = "store_true", dest = "printKeys", default = False)
        options = parser.parse_args(list(args[1:]))
        session = dissomniag.Session()
        
        for user in session.query(User).all():
            if (not self.user.isAdmin and user.username != self.user.username) or user.username == dissomniag.Identity.systemUserName:
                continue
            self.printSuccess(str("User: %s" % user.username))
            print(str("\t isAdmin: %s" % user.isAdmin))
            if self.user.isAdmin:
                print(str("\t loginRPC: %s" % user.loginRPC))
                print(str("\t loginSSH: %s" % user.loginSSH))
                print(str("\t loginManhole: %s" % user.loginManhole))
            if options.printKeys and user.publicKeys:
                print(self.colorString(str("\t Public Keys: "), style = Style.BRIGHT))
                for key in user.publicKeys:
                    self.printInfo("Key-ID: %i" % key.id)
                    self.printInfo(str("%s" % key.publicKey))
            print("\n")

class listKeys(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        parser = argparse.ArgumentParser(description = 'Print out all keys or keys per User', prog = args[0])
        if self.user.isAdmin:
            parser.add_argument("-a", "--all", action = "store_true", dest = "all", default = False)
            parser.add_argument("-u", "--username", action = "store", dest = "username")
        options = parser.parse_args(list(args[1:]))
        
        session = dissomniag.Session()
        
        if (self.user.isAdmin):
            if options.all:
                try:
                    keys = session.query(PublicKey).all()
                    for key in keys:
                        self.printInfo("Key-ID: %i" % key.id)
                        self.printInfo(key.publicKey)
                    return
                except Exception:
                    self.printError("No Public Keys available")
                    return
            elif options.username:
                try:
                    user = session.query(User).filter(User.username == options.username).one()
                    for key in user.publicKeys:
                        self.printInfo("Key-ID: %i" % key.id)
                        self.printInfo(key.publicKey)
                    return
                except Exception:
                    self.printError("No such User.")
                    
        for key in self.user.publicKeys:
            self.printInfo("Key-ID: %i" % key.id)
            self.printInfo(key.publicKey)

class addUser(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        parser = argparse.ArgumentParser(description = "Add a user to DiSSOmniaG. ADMIN ACCESS NEEDED!", prog = args[0])
        parser.add_argument("-a", "--admin", action = "store_true", dest = "isAdmin", default = False)
        parser.add_argument("--dissable-ssh", action = "store_false", dest = "loginSSH", default = True)
        parser.add_argument("--dissable-rpc", action = "store_false", dest = "loginRPC", default = True)
        parser.add_argument("--enable-manhole", action = "store_true", dest = "loginManhole", default = False)
        parser.add_argument("username", action = "store")
        parser.add_argument("password", action = "store")
        parser.add_argument("-k", "--key", action = "store", nargs = "*", dest = "key", help = "Provide the key as the last Argument!")
        
        options = parser.parse_args(args[1:])
        assert options.username
        assert options.password
        if not self.user.isAdmin:
            print(self.colorString("Permission denied: Only Admin users are allowed to add a users!", color = Fore.RED, style = Style.BRIGHT))
            return
            
        options.key = " ".join(options.key)

        session = dissomniag.Session()
        try:
            existingUser = session.query(User).filter(User.username == options.username).one()
            if existingUser:
                print(self.colorString("User already exists.", color = Fore.RED, style = Style.BRIGHT))
                return
        except NoResultFound:
            newUser = User(options.username, options.password, options.key,
                           options.isAdmin, options.loginRPC, options.loginSSH,
                           options.loginManhole, isHtpasswd = False)
            session.add(newUser)
            session.commit()
            session.flush()
        except MultipleResultsFound:
            print(self.colorString("User already exists.", color = Fore.RED, style = Style.BRIGHT))
            return
        
        print(self.colorString("SUCCESS", color = Fore.GREEN, style = Style.BRIGHT))


class addKey(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        parser = argparse.ArgumentParser(description = "Add a key to a user.", prog = args[0])
        if self.user.isAdmin:
            parser.add_argument("-u", "--username", action = "store", dest = "username", help = "Enter the username of the User where you want to add the key.", default = None)
        
        parser.add_argument("key", nargs = "*", action = "store")
        options = parser.parse_args(args[1:])
        options.key = ' '.join(options.key)
        
        session = dissomniag.Session()
        if self.user.isAdmin and options.username and options.username != self.user.username:
            try:
                user = session.query(User).filter(User.username == options.username).one()
                user.addKey(options.key)
                print(self.colorString("SUCCESS. Added key to user %s" % options.username, color = Fore.GREEN, style = Style.BRIGHT))
                return
            except NoResultFound:
                print(self.colorString("User doesn't exists.", color = Fore.RED, style = Style.BRIGHT))
                return
            except dissomniag.BadKeyError:
                print(self.colorString("Entered Key is not a valid Key", color = Fore.RED, style = Style.BRIGHT))
                return
            except Exception:
                print(self.colorString("Unspecified Error (A)", color = Fore.RED, style = Style.BRIGHT))
        else:
            try:
                self.user.addKey(options.key)
                print(self.colorString("SUCCESS. Added key to user %s" % options.username, color = Fore.GREEN, style = Style.BRIGHT))
            except dissomniag.BadKeyError:
                print(self.colorString("Entered Key is not a valid Key", color = Fore.RED, style = Style.BRIGHT))
                
class modUser(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        parser = argparse.ArgumentParser(description = "Modify a user.", prog = args[0])
        parser.add_argument("-a", "--admin", action = "store_true", dest = "isAdmin", default = None)
        parser.add_argument("-A", "--notAdmin", action = "store_false", dest = "isAdmin", default = None)
        parser.add_argument("--dissable-ssh", action = "store_false", dest = "loginSSH", default = None)
        parser.add_argument("--enable-ssh", action = "store_true", dest = "loginSSH", default = None)
        parser.add_argument("--dissable-rpc", action = "store_false", dest = "loginRPC", default = None)
        parser.add_argument("--enable-rpc", action = "store_true", dest = "loginRPC", default = None)
        parser.add_argument("--enable-manhole", action = "store_true", dest = "loginManhole", default = None)
        parser.add_argument("--dissable-manhole", action = "store_false", dest = "loginManhole", default = None)
        
        if self.user.isAdmin:
            parser.add_argument("-u", "--username", action = "store", dest = "username")
        
        parser.add_argument("-p", "--newPassword", action = "store", help = "Enter the new password to store.", dest = "newPassword", default = None)
        parser.add_argument("-o", "--oldPassword", action = "store", help = "Enter the new password to store.", dest = "oldPassword", default = None)
        
        parser.add_argument("-k", "--key", action = "store", nargs = "*", dest = "key", help = "Provide the key as the last Argument!", default = None)
        
        options = parser.parse_args(args[1:])
        
        if not self.user.isAdmin:
            if options.username == dissomniag.Identity.systemUserName:
                self.printError("Could not find user.")
            if options.isAdmin != None or options.loginSSH != None or options.loginRPC != None or options.loginManhole != None:
                self.printError("You don't have the permissions to do that.")
                return
            if options.newPassword:
                if not options.oldPassword:
                    self.printError("Please enter your old Password.")
                    return
                if not self.user.checkPassword(options.oldPassword):
                    self.printError("Your old Password is not valid.")
                self.user.saveNewPassword(options.newPassword)
            if options.key:
                try:
                    self.user.addKey(options.Key)
                except dissomniag.BadKeyError:
                    self.printError("Please enter a valid PublicKey.")
                    return
        else:
            
            user = self.user
            session = dissomniag.Session()
            if options.username and options.username != self.user.username:
                try:
                    user = session.query(User).filter(User.username == options.username).one()
                except NoResultFound:
                    self.printError("Could not find the user.")
                    return
            if options.isAdmin != None:
                if self.user == user or user.username == dissomniag.config.htpasswd.adminUser:
                    self.printError("You can not change the admin status of yourself or the default admin user.")
                    self.printInfo("I continue.")
                else:
                    user.isAdmin = options.isAdmin
            if options.loginSSH != None:
                if self.user == user or user.username == dissomniag.config.htpasswd.adminUser:
                    self.printError("You can not exclude yourself or the default admin user from accessing this shell.")
                    self.printInfo("I continue.")
                else:
                    user.isAdmin = options.isAdmin
            if options.loginRPC != None:
                user.loginRPC = options.loginRPC
                
            if options.loginManhole != None:
                user.loginManhole = options.loginManhole
            
            if options.key != None:
                try:
                    user.addKey(options.Key)
                except dissomniag.BadKeyError:
                    self.printError("Please enter a valid PublicKey.")
                    return   
            
            session.commit()
            session.flush()
            
            if options.newPassword and user.username != self.user.username:
                user.saveNewPassword(options.newPassword)
            elif options.newPassword:
                if not options.oldPassword != None:
                    self.printError("Please enter your old Password.")
                    return
                if not self.user.checkPassword(options.oldPassword):
                    self.printError("Your old Password is not valid.")
                    return
                self.user.saveNewPassword(options.newPassword)
            
                
                    
                
            
        
class delUser(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        parser = argparse.ArgumentParser(description = "Delete a user", prog = args[0])
        parser.add_argument("username", action = "store", help = "Enter the username of the User you want to delete.")
        options = parser.parse_args(args[1:])
        
        if not self.user.isAdmin:
            self.printError("Permission denied: Only Admin users are allowed to delete a users!")
            return
        
        if options.username == self.user.username:
            self.printError("Permission denied: You cannot delete yourself!")
            return
        
        if options.username == dissomniag.config.htpasswd.adminUser:
            self.printError("Permission denied: You cannot delete the default admin user!")
            return
        
        if options.username == dissomniag.Identity.systemUserName:
            self.printError("Permission denied: You cannot delete the system user!")
            return
        
        session = dissomniag.Session()
        
        try:
            user = session.query(User).filter(User.username == options.username).one()
            session.delete(user)
            session.commit()
            session.flush()
        except NoResultFound:
            self.printError("User %s does not exists." % options.username)
            return
        except Exception:
            self.printError("Unspecified Error")
            return
        
        self.printSuccess("User %s successful deleted." % options.username)
        
               
class delKey(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        parser = argparse.ArgumentParser(description = "Delete a key", prog = args[0])
        parser.add_argument("keyId", action = "store", type = int, help = "Enter the Key-ID of the key you want to delete.")
        if self.user.isAdmin:
            parser.add_argument("-u", "--username", action = "store", help = "The user where to delete a key.", dest = "username", default = None)
            parser.add_argument("-f", "--force", action = "store_true", help = "Force to delete key in all users.", dest = "force", default = False)
        options = parser.parse_args(args[1:])
        
        session = dissomniag.Session()
        
        user = self.user
        
        if self.user.isAdmin:
            if options.force:
                try:
                    key = session.query(PublicKey).filter(PublicKey.id == options.keyId).one()
                except Exception:
                    self.printError("Could not find Key.")
                    return
                session.delete(key)
                session.commit()
                session.flush()
                return
            
            if options.username and options.username != self.user.username:
                # Change in other user
                try:
                    user = session.query(User).filter(User.username == options.username).one()
                except NoResultFound:
                    self.printError("Could not find user.")
                    return
            
        for key in user.publicKeys:
            if key.id == options.keyId:
                user.publicKeys.remove(key)
                if len(key.users) == 0:
                    #Only the actual user owns that key
                    session.delete(key)
                    session.commit()
                    session.flush()
                return
                        
        #Key not found
        self.printError("Could not find the key. Key-ID: %s" % options.keyId)
        return
    

class passwd(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        parser = argparse.ArgumentParser(description = "Delete a key", prog = args[0])
        parser.add_argument("newPassword", action = "store", help = "Enter the new password to store.", default = None)
        if self.user.isAdmin:
            parser.add_argument("-u", "--username", action = "store", help = "The user where to delete a key.", dest = "username", default = None)
            parser.add_argument("-o", "--oldPassword", action = "store", help = "Enter the new password to store.", dest = "oldPassword", default = None)
        else:
            parser.add_argument("oldPassword", action = "store", help = "Enter the new password to store.", default = None)
        options = parser.parse_args(args[1:])
        
        session = dissomniag.Session()
        
        if self.user.isAdmin:
            if options.username and options.username == dissomniag.Identity.systemUserName:
                self.printError("The user doesn't exists.")
                return
            if options.username and options.username != self.user.username:
                try:
                    user = session.query(User).filter(User.username == options.username).one()
                    user.saveNewPassword(options.newPassword)
                except NoResultFound:
                    self.printError("The user doesn't exists.")
                    return
            else:
                if not options.oldPassword:
                    self.printError("Please enter your old Password.")
                    return
                if not self.user.checkPassword(options.oldPassword):
                    self.printError("Your old Password is not valid.")
                    return
                self.user.saveNewPassword(options.newPassword)
        else:
            if not options.oldPassword:
                self.printError("Please enter your old Password.")
                return
            if not self.user.checkPassword(options.oldPassword):
                self.printError("Your old Password is not valid.")
            self.user.saveNewPassword(options.newPassword)
            
class whoami(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        self.printSuccess(self.user.username)

