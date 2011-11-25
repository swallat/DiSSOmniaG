# -*- coding: utf-8 -*-
'''
Created on 17.11.2011

@author: Sebastian Wallat
'''
import logging, argparse
from colorama import Fore, Style, Back
import sys, time
import getpass
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import dissomniag
from dissomniag.utils import CliMethodABCClass
from dissomniag import taskManager

log = logging.getLogger("cliApi.ManageApps")

class apps(CliMethodABCClass.CliMethodABCClass):
    
    def printApp(self, app, withLog = False):
        session = dissomniag.Session()
        session.expire(app)
        
        self.printSuccess("App Name: %s" % str(app.name))
        self.printInfo("\tUsers:")
        for user in app.users:
            self.printInfo("\t\t%s" % str(user.username))
        print("\n")
        self.printInfo("\tRelated LiveCD's:")
        for rel in app.AppLiveCdRelations:
            self.printInfo("\t\tNode Name: %s" % str(rel.liveCd.vm.commonName))
            self.printInfo("\t\tApp Last Seen: %s" % str(rel.lastSeen))
            self.printInfo("\t\tState: %s" % str(rel.state))
            if withLog:
                self.printInfo("\t\tLog:")
                print(str(rel.log))
        print("\n\n")
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        parser = argparse.ArgumentParser(description = 'List Apps', prog = args[0])
        
        parser.add_argument("-a", "--all", dest = "all", action = "store_true", default = False)
        parser.add_argument("-l", "--log", dest = "log", action = "store_true", default = False)
        parser.add_argument("-n" , "--name", dest = "name", action = "store", default = None)
        
        options = parser.parse_args(args[1:])
        
        withLog = options.log
        all = options.all
        name = options.name
        
        session = dissomniag.Session()
        
        if name != None:
            try:
                app = session.query(dissomniag.model.App).filter(dissomniag.model.App.name == name).one()
            except NoResultFound:
                self.printError("No App Found with this name!")
                return
            except MultipleResultsFound:
                apps = session.query(dissomniag.model.App).filter(dissomniag.model.App.name == name).all()
                foundOne = False
                for app in apps:
                    if self.user in app.users or self.user.isAdmin:
                        foundOne = True
                        self.printApp(app, withLog)
                if not foundOne:
                    self.printError("There are no Apps with name %s for user %s." %(name, self.user.username))
                return
            else:
                if self.user in app.users or self.user.isAdmin:
                    self.printApp(app, withLog)
                else:
                    self.printError("There are no Apps with name %s for user %s." %(name, self.user.username))
                return
        
        if self.user.isAdmin and all:
            try:
                apps = session.query(dissomniag.model.App).all()
            except NoResultFound:
                return
            else:
                for app in apps:
                    self.printApp(app, withLog)
        
        try:
            apps = session.query(dissomniag.model.App).all()
        except NoResultFound:
            return
        else:
            for app in apps:
                if self.user in app.users:
                    self.printApp(app, withLog)
        
        return
                        
                
        
class addApp(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        parser = argparse.ArgumentParser(description = 'Add a App', prog = args[0])
        
        parser.add_argument("appName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        session = dissomniag.Session()
        
        name = str(options.appName)
        
        try:
            apps = session.query(dissomniag.model.App).filter(dissomniag.model.App.name == name).all()
        except NoResultFound:
            pass
        else:
            for app in apps:
                if app.name == name:
                    self.printError("App with name %s already exists." % name)
                    return
        try:
            dissomniag.model.App(self.user, name)
        except Exception as e:
            self.printError("App creation Error. %s" % str(e))
            return
        else:
            self.printSuccess("Successfully added App %s for user %s." % (name, self.user.username))
            return
        
class delApp(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        parser = argparse.ArgumentParser(description = 'Delete a App', prog = args[0])
        
        parser.add_argument("appName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        session = dissomniag.Session()
        
        name = str(options.appName)
        
        try:
            apps = session.query(dissomniag.model.App).filter(dissomniag.model.App.name == name).all()
        except NoResultFound:
            self.printError("There is no app with name %s." % name)
            return
        else:
            found = False
            for app in apps:
                if app.name == name and ((self.user in app.users) or (self.user.isAdmin)):
                    found = True
                    try:
                        dissomniag.model.App.delApp(self.user, app)
                    except Exception as e:
                        self.printError("Delete error. %s" % str(e))
            if not found:
                self.printError("There is no app with name %s." % name)
            else:
                self.printSuccess("Successfully deleted app %s." % name)
            
            return
        
class addAppUser(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        parser = argparse.ArgumentParser(description = 'Add a User to a App', prog = args[0])
        
        parser.add_argument("appName", action = "store")
        parser.add_argument("userName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        session = dissomniag.Session()
        
        appName = str(options.appName)
        userName = str(options.userName)
        dbUser = None
        
        try:
            users = session.query(dissomniag.auth.User).filter(dissomniag.auth.User.username == userName).all()
        except NoResultFound:
            self.printError("There is no user with username %s." % userName)
            return
        else:
            found = False
            for user in users:
                if user.username == userName and (not user.isAdmin or (self.user.isAdmin)):
                    found = True
                    dbUser = user
                    break
            if not found:
                self.printError("There is no user with username %s." % userName)
                return
            
        try:
            apps = session.query(dissomniag.model.App).filter(dissomniag.model.App.name == appName).all()
        except NoResultFound:
            self.printError("There is no app with name %s." % appName)
            return
        else:
            found = False
            for app in apps:
                if app.name == appName and ((self.user in app.users) or (self.user.isAdmin)):
                    found = True
                    try:
                        app.addUser(self.user, dbUser)
                    except Exception as e:
                        self.printError("Could not add user %s to app %s. %s" % (userName, appName, str(e)))
                        return
                    break
            if not found:
                self.printError("Could not add user %s to app %s." % (userName, appName))
                return
            else:
                self.printSuccess("User %s added to app %s." % (userName, appName))
                return
        
        
        
class delAppUser(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        parser = argparse.ArgumentParser(description = 'Delete a User from an App', prog = args[0])
        
        parser.add_argument("appName", action = "store")
        parser.add_argument("userName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        session = dissomniag.Session()
        
        appName = str(options.appName)
        userName = str(options.userName)
        dbUser = None
        
        try:
            users = session.query(dissomniag.auth.User).filter(dissomniag.auth.User.username == userName).all()
        except NoResultFound:
            self.printError("There is no user with username %s." % userName)
            return
        else:
            found = False
            for user in users:
                if user.username == userName and (not user.isAdmin or (self.user.isAdmin)):
                    found = True
                    dbUser = user
                    break
            if not found:
                self.printError("There is no user with username %s." % userName)
                return
            
        try:
            apps = session.query(dissomniag.model.App).filter(dissomniag.model.App.name == appName).all()
        except NoResultFound:
            self.printError("There is no app with name %s." % appName)
            return
        else:
            found = False
            for app in apps:
                if app.name == appName and ((self.user in app.users) or (self.user.isAdmin)):
                    found = True
                    try:
                        dissomniag.model.App.delUserFromApp(self.user, app, dbUser)
                    except Exception as e:
                        self.printError("Could not delete user %s from app %s. %s" % (userName, appName, str(e)))
                        return
                    break
            if not found:
                self.printError("Could not delete user %s from app %s." % (userName, appName))
                return
            else:
                self.printSuccess("User %s deleted from app %s." % (userName, appName))
                return
        
class addAppVm(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can add a VM to a App!")
            return
        
        parser = argparse.ArgumentParser(description = 'Add a VM to a App', prog = args[0])
        
        parser.add_argument("appName", action = "store")
        parser.add_argument("vmName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        session = dissomniag.Session()
        
        appName = str(options.appName)
        vmName = str(options.vmName)
        dbVm = None
        
        try:
            vms = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).all()
        except NoResultFound:
            self.printError("There is no vm with name %s." % vmName)
            return
        else:
            found = False
            for vm in vms:
                if vm.commonName == vmName:
                    found = True
                    dbVm = vm
                    break
            if not found:
                self.printError("There is no vm with name %s." % vmName)
                return
            
        try:
            apps = session.query(dissomniag.model.App).filter(dissomniag.model.App.name == appName).all()
        except NoResultFound:
            self.printError("There is no app with name %s." % appName)
            return
        else:
            found = False
            for app in apps:
                if app.name == appName:
                    found = True
                    try:
                        app.addLiveCdRelation(self.user, dbVm.liveCd)
                    except Exception as e:
                        self.printError("Could not add vm %s to app %s. %s" % (vmName, appName, str(e)))
                        return
                    break
            if not found:
                self.printError("Could not add vm %s to app %s." % (vmName, appName))
                return
            else:
                self.printSuccess("VM %s added to app %s." % (vmName, appName))
                return
        
class delAppVm(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can delete a VM to a App!")
            return
        
        parser = argparse.ArgumentParser(description = 'Delete a VM to a App', prog = args[0])
        
        parser.add_argument("appName", action = "store")
        parser.add_argument("vmName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        session = dissomniag.Session()
        
        appName = str(options.appName)
        vmName = str(options.vmName)
        dbVm = None
        
        try:
            vms = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).all()
        except NoResultFound:
            self.printError("There is no vm with name %s." % vmName)
            return
        else:
            found = False
            for vm in vms:
                if vm.commonName == vmName:
                    found = True
                    dbVm = vm
                    break
            if not found:
                self.printError("There is no vm with name %s." % vmName)
                return
            
        try:
            apps = session.query(dissomniag.model.App).filter(dissomniag.model.App.name == appName).all()
        except NoResultFound:
            self.printError("There is no app with name %s." % appName)
            return
        else:
            found = False
            for app in apps:
                if app.name == appName:
                    found = True
                    try:
                        dissomniag.model.App.delLiveCdFromApp(self.user, app, dbVm.liveCd)
                    except Exception as e:
                        self.printError("Could not delete vm %s from app %s. %s" % (vmName, appName, str(e)))
                        return
                    break
            if not found:
                self.printError("Could not delete vm %s from app %s." % (vmName, appName))
                return
            else:
                self.printSuccess("VM %s deleted from app %s." % (vmName, appName))
                return
        
class appUpdate(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
class appCompile(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
class appStop(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
class appStart(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal