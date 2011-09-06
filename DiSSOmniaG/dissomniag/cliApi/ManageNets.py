# -*- coding: utf-8 -*-
"""
Created on 06.09.2011

@author: Sebastian Wallat
"""

import logging, argparse, os
from colorama import Fore, Style, Back
import sys, time
import getpass
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import dissomniag
from dissomniag.utils import CliMethodABCClass

log = logging.getLogger("cliApi.ManageNets")

class nets(CliMethodABCClass.CliMethodABCClass):
    
    def printNet(self, net, withXml = False, user = None):
        if user == None:
            user = self.user
            
        self.printInfo("Network Name: %s" % net.name)
        
        if isinstance(net, dissomniag.model.generatedNetwork):
            self.printInfo("Host: %s" % net.getHost(user).commonName)
            self.printInfo("State: %s" % dissomniag.model.GenNetworkState.getStateName(net.state))
            
        self.printInfo(str(net))
        
        if isinstance(net, dissomniag.model.generatedNetwork) and withXml:
            self.printInfo(net.getLibVirtString(user))
        
        self.printInfo("\n")
        
    def printAll(self, withXml = False, user = None, onlyGen = False, onlyNative = False):
        if user == None:
            user = self.user
        session = dissomniag.Session()
        try:
            if onlyGen:
                nets = session.query(dissomniag.model.generatedNetwork).all()
            else:
                nets = session.query(dissomniag.model.Network).all()
        except NoResultFound:
            return
        for net in nets:
            if onlyNative and isinstance(net, dissomniag.model.generatedNetwork):
                continue
            self.printNet(net, withXml = withXml, user = user)
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can list Nets!")
            return
        
        parser = argparse.ArgumentParser(description = 'List Nets', prog = args[0])
        
        parser.add_argument("-a", "--all", dest = "all", action = "store_true", default = True)
        parser.add_argument("-x", "--XML", dest = "xml", action = "store_true", default = False)
        parser.add_argument("-g", "--onlyGenerated", dest = "gen", action = "store_true", default = False)
        parser.add_argument("-n" , "--name", dest = "name", action = "store", default = None)
        parser.add_argument("-N" , "--onlyNative", dest = "native", action = "store_true", default = False)
        
        options = parser.parse_args(args[1:])
        xml = options.xml
        onlyGen = options.gen
        onlyNative = options.native
        if onlyGen and onlyNative:
            self.printError("Options Error: You cannot use --onlyGenerated and --onlyNative at the same time")
            return
        if options.name == None or options.all:
            self.printAll(withXml = xml, user = self.user, onlyGen = onlyGen, onlyNative = onlyNative)
        
        if options.name != None:
            name = str(options.name)
            session = dissomniag.Session()
            try:
                if onlyGen:
                    net = session.query(dissomniag.model.generatedNetwork).filter(dissomniag.model.generatedNetwork.name == name).one()
                else:
                    net = session.query(dissomniag.model.Network).filter(dissomniag.model.Network.name == name).one()
            except NoResultFound:
                self.printError("Could not find a net with the name %s" % name)
                return
            except MultipleResultsFound:
                self.printError("Query inconsistency")
            else:
                if onlyNative and isinstance(net, dissomniag.model.generatedNetwork):
                    return
                self.printNet(net, withXml = xml, user = self.user)
        return
            
        
        
        
class addNet(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can add Nets!")
            return
        
        parser = argparse.ArgumentParser(description = 'Add a net to a host', prog = args[0])
        
        parser.add_argument("hostName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        hostName = str(options.hostName)
        session = dissomniag.Session()
        try:
            host = session.query(dissomniag.model.Host).filter(dissomniag.model.Host.commonName == hostName).one()
        except NoResultFound:
            self.printError("Could not find a host with hostname %s. Please enter a valid hostname." % hostName)
            return
        except MultipleResultsFound:
            self.printError("Invalid Query")
            return
        else:
            freeNetString = dissomniag.model.generatedNetwork.getFreeNetString(self.user, host)
            if not freeNetString:
                self.printError("There is no free net available on the host %s." % hostName) 
            dissomniag.model.generatedNetwork(self.user, freeNetString, host = host)
            self.printSuccess("Created Net %s on host %s." % (str(freeNetString), hostName))
                    
        return
            
        
        
class delNet(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can delete Nets!")
            return
        
        parser = argparse.ArgumentParser(description = 'Delete a net from a host', prog = args[0])
        
        parser.add_argument("hostName", action = "store")
        parser.add_argument("netName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        netName = str(options.netName)
        hostName = str(options.hostName)
        
        session = dissomniag.Session()
        try:
            nets = session.query(dissomniag.model.generatedNetwork).filter(dissomniag.model.generatedNetwork.name == netName).all()
        except NoResultFound:
            self.printError("Could not find net with name %s" % netName)
        else:
            net = None
            for myNet in nets:
                if myNet.getHost(self.user).commonName == hostName:
                    net = myNet
                    break
            
            if net == None:
                self.printError("Could not find net %s on host %s." % (netName, hostName))
                return
            
            dissomniag.model.generatedNetwork.deleteNetwork(self.user, net)  
        return                 
        
        
class startNet(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can start Nets!")
            return
        
        parser = argparse.ArgumentParser(description = 'Start a net', prog = args[0])
        
        parser.add_argument("hostName", action = "store")
        parser.add_argument("netName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        netName = str(options.netName)
        hostName = str(options.hostName)
        
        session = dissomniag.Session()
        try:
            nets = session.query(dissomniag.model.generatedNetwork).filter(dissomniag.model.generatedNetwork.name == netName).all()
        except NoResultFound:
            self.printError("Could not find net with name %s" % netName)
        else:
            net = None
            for myNet in nets:
                if myNet.getHost(self.user).commonName == hostName:
                    net = myNet
                    break
            
            if net == None:
                self.printError("Could not find net %s on host %s." % (netName, hostName))
                return
            
            net.start(self.user)
        return
        
class stopNet(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can stop Nets!")
            return
        
        parser = argparse.ArgumentParser(description = 'Stop a net', prog = args[0])
        
        parser.add_argument("hostName", action = "store")
        parser.add_argument("netName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        netName = str(options.netName)
        hostName = str(options.hostName)
        
        session = dissomniag.Session()
        try:
            nets = session.query(dissomniag.model.generatedNetwork).filter(dissomniag.model.generatedNetwork.name == netName).all()
        except NoResultFound:
            self.printError("Could not find net with name %s" % netName)
        else:
            net = None
            for myNet in nets:
                if myNet.getHost(self.user).commonName == hostName:
                    net = myNet
                    break
            
            if net == None:
                self.printError("Could not find net %s on host %s." % (netName, hostName))
                return
            
            net.stop(self.user)
        return

class refreshNet(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can stop Nets!")
            return
        
        parser = argparse.ArgumentParser(description = 'Stop a net', prog = args[0])
        
        parser.add_argument("hostName", action = "store")
        parser.add_argument("netName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        netName = str(options.netName)
        hostName = str(options.hostName)        
        
        session = dissomniag.Session()
        try:
            nets = session.query(dissomniag.model.generatedNetwork).filter(dissomniag.model.generatedNetwork.name == netName).all()
        except NoResultFound:
            self.printError("Could not find net with name %s" % netName)
        else:
            net = None
            for myNet in nets:
                if myNet.getHost(self.user).commonName == hostName:
                    net = myNet
                    break
            
            if net == None:
                self.printError("Could not find net %s on host %s." % (netName, hostName))
                return
            
            net.refresh(self.user)
        return
