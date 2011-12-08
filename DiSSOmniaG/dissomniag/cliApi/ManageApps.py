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
from abc import ABCMeta, abstractmethod

import dissomniag
from dissomniag.utils import CliMethodABCClass
from dissomniag import taskManager
from abc import abstractproperty

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
            session.expire(rel)
            self.printInfo("\t\tNode Name: %s" % str(rel.liveCd.vm.commonName))
            self.printInfo("\t\tApp Last Seen: %s" % str(rel.lastSeen))
            self.printInfo("\t\tState: %s" % str(dissomniag.model.AppState.getName(rel.state)))
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
            
class AbstractAppAction(CliMethodABCClass.CliMethodABCClass):
    __metaclass__ = ABCMeta
    
    @abstractproperty
    def msg(self):
        raise NotImplementedError()
    
    @abstractproperty
    def action(self):
        raise NotImplementedError()
    
    @abstractproperty
    def name(self):
        raise NotImplementedError()
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
    
        parser = argparse.ArgumentParser(description = self.msg(), prog = args[0])
               
        parser.add_argument("-v" , "--vmName", dest = "vmName", action = "store", default = None)
        parser.add_argument("-s" , "--scriptName", dest = "scriptName", action = "store", default = None)
        parser.add_argument("-t" , "--tagOrCommit", dest = "tagOrCommit", action = "store", default = None)
        parser.add_argument("-T" , "--topology", dest = "topology", action = "store", default = None)
        
        parser.add_argument("appName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        self.appName = str(options.appName)
        
        self.vmName = options.vmName
        if self.vmName != None:
            self.vmName = str(self.vmName)
            
        self.scriptName = options.scriptName
        if self.scriptName != None:
            self.scriptName = str(self.scriptName)
            
        self.tagOrCommit = options.tagOrCommit
        if self.tagOrCommit != None:
            self.tagOrCommit = str(self.tagOrCommit)
        
        self.topology = options.topology
        if self.topology != None:
            self.topology = str(self.topology)
        
        session = dissomniag.Session()
        app = None
        try:
            app = session.query(dissomniag.model.App).filter(dissomniag.model.App.name == self.appName).one()
        except NoResultFound as e:
            self.printError("There is no app with name %s." % self.appName)
            return
        except MultipleResultsFound as e:
            app = app[0]
        
        try:
            app.authUser(self.user)
        except Exception as e:
            self.printError("There is no app with name %s." % self.appName)
            return False
        
        relObj = None
        
        if self.vmName != None:
            vm = None
            try:
                vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == self.vmName).one()
            except NoResultFound as e:
                self.printError("There is no VM with name %s." % self.vmName)
                return False
            except MultipleResultsFound as e:
                self.printError("There are multiple VM's with name %s. DB ERROR." % self.vmName)
                return False
            
            if not hasattr(vm, "liveCd"):
                self.printError("VM has no liveCd!")
                return False
            liveCd = vm.liveCd
            
            try:
                relObj = session.query(dissomniag.model.AppLiveCdRelation).filter(dissomniag.model.AppLiveCdRelation.app == app).filter(dissomniag.model.AppLiveCdRelation.liveCd == liveCd).one()
            except NoResultFound as e:
                self.printError("There is no Relation between app %s and vm %s." % (self.appName, self.vmName))
                return False
            except MultipleResultsFound as e:
                self.printError("There are multiple relations between add %s and vm %s." % (self.appName, self.vmName))
                return False
            
        try:
            ret = app.operate(self.user, self.action(), relObj, scriptName = self.scriptName, tagOrCommit = self.tagOrCommit)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.printError("General Exception %s." % str(e))
            return False
        else:
            return ret
        
class appCompile(AbstractAppAction):
    
    def msg(self):
        return "Compile an App."
    
    def action(self):
        return dissomniag.model.AppActions.COMPILE
    
    def name(self):
        return "appCompile"
        
class appStop(AbstractAppAction):
    
    def msg(self):
        return "Stop an App."
    
    def action(self):
        return dissomniag.model.AppActions.STOP
    
    def name(self):
        return "appStop"
        
class appStart(AbstractAppAction):
    
    def msg(self):
        return "Start an App."
    
    def action(self):
        return dissomniag.model.AppActions.START
    
    def name(self):
        return "appStart"
        
class appClone(AbstractAppAction):
    
    def msg(self):
        return "Clone an App."
    
    def action(self):
        return dissomniag.model.AppActions.CLONE
    
    def name(self):
        return "appClone"

class appInterrupt(AbstractAppAction):
    
    def msg(self):
        return "Interrupt an App."
    
    def action(self):
        return dissomniag.model.AppActions.INTERRUPT
    
    def name(self):
        return "appInterrupt"
        
class appReset(AbstractAppAction):
    
    def msg(self):
        return "Reset an App."
    
    def action(self):
        return dissomniag.model.AppActions.RESET
    
    def name(self):
        return "appReset"
        
class appRefreshGit(AbstractAppAction):
    
    def msg(self):
        return "Refresh Git repo on an App."
    
    def action(self):
        return dissomniag.model.AppActions.REFRESH_GIT
    
    def name(self):
        return "appRefreshGit"
        
class appRefreshAndReset(AbstractAppAction):
    
    def msg(self):
        return "Refresh and reset an App."
    
    def action(self):
        return dissomniag.model.AppActions.REFRESH_AND_RESET
    
    def name(self):
        return "appRefreshAndReset"