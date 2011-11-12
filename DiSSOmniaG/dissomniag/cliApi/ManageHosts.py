# -*- coding: utf-8 -*-
"""
Created on 31.08.2011

@author: Sebastian Wallat
"""
import logging, argparse, os
from colorama import Fore, Style, Back
import sys, time
import getpass
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import dissomniag
from dissomniag.utils import CliMethodABCClass

log = logging.getLogger("cliApi.ManageHosts")


class hosts(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can add Hosts!")
            return
        
        parser = argparse.ArgumentParser(description = 'List All Hosts', prog = args[0])
        parser.add_argument("-c", "--withCapabilities", dest = "withCap", action = "store_true", default = False)
        
        options = parser.parse_args(args[1:])
        
        session = dissomniag.Session()
        hosts = None
        try:
            hosts = session.query(dissomniag.model.Host).all()
        except NoResultFound:
            pass
        
        for host in hosts:
            self.printHost(host, withCap = options.withCap)
    
                    
    def printHost(self, host, withCap = False):
        
        if host == None or type(host) != dissomniag.model.Host:
            print(str(type(host)))
            print(str(dissomniag.model.Host == type(host)))
            return
        session = dissomniag.Session()
        session.expire(host)
        
        print("Common Name: %s" % str(host.commonName))
        print("State: %s" % str(dissomniag.model.NodeState.getStateName(host.state)))
        print("UUID: %s" % str(host.uuid))
        print("MaintainanceIP: %s" % str(host.getMaintainanceIP().addr))
        print("AdministrativeUserName: %s" % str(host.administrativeUserName))
        print("BridgedInterfaceName: %s" % str(host.bridgedInterfaceName))
        print("lastChecked: %s" % str(host.lastChecked))
        print("Libvirt Version: %s" % str(host.libvirtVersion))
        print("KVMUsable: %s" % str(host.kvmUsable))
        print("FreeDiskspace: %s" % str(host.freeDiskspace))
        print("RamCapacity: %s" % str(host.ramCapacity))
        print("ConfigurarionMissmatch: %s" % str(host.configurationMissmatch))
        if withCap:
            print("LibVirtCapabilities: \n %s" % str(host.libvirtCapabilities))
        print("\n")
            
        
        
class addHost(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can add Hosts!")
            return
        
        parser = argparse.ArgumentParser(description = 'Add a Host to the Dissomniag System', prog = args[0])
        parser.add_argument("commonName", action = "store")
        parser.add_argument("ipAddress", action = "store")
        parser.add_argument("-u", "--adminUser", dest = "adminUser", action = "store", default = None)
        parser.add_argument("-b", "--bridgeName", dest = "bridgeName", action = "store", default = None)
        
        options = parser.parse_args(args[1:])
        
        if not dissomniag.model.IpAddress.checkValidIpAddress(options.ipAddress):
            self.printError("The IpAddress is not valid.")
            return
        
        if options.adminUser == None:
            adminUser = "root"
        else:
            adminUser = options.adminUser
    
        if options.bridgeName == None:
            bridgeName = "br0"
        else:
            bridgeName = str(options.bridgeName)
        
        session = dissomniag.Session()
        try:
            found = session.query(dissomniag.model.Host).filter(dissomniag.model.Host.commonName == options.commonName).one()
        except NoResultFound:
            pass
        except MultipleResultsFound:
            self.printError("Query Inconsistency")
            return
        else:
            if not found:
                pass
            self.printError("The hostname is already in use.")
            return
        host = dissomniag.model.Host(self.user, commonName = options.commonName, maintainanceIP = options.ipAddress, administrativeUserName = adminUser, bridgedInterfaceName = bridgeName)
        session.add(host)
        dissomniag.saveCommit(session)
        
        self.printSuccess("Host added. Make sure to add the SSH-Key %s to the admin user on the Host!" % os.path.abspath(dissomniag.config.dissomniag.rsaKeyPublic))
        
        

class modHost(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can modify Hosts!")
        
        parser = argparse.ArgumentParser(description = "Modify a Host", prog = args[0])
        parser.add_argument("-i", "--ipAddress", dest = "ipAddress", action = "store", default = None)
        parser.add_argument("-u", "--adminUser", dest = "adminUser", action = "store", default = None)
        parser.add_argument("-b", "--bridgeName", dest = "bridgeName", action = "store", default = None)
        parser.add_argument("commonName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        session = dissomniag.Session()
        host = None
        try:
            host = session.query(dissomniag.model.Host).filter(dissomniag.model.Host.commonName == str(options.commonName)).one()
        except (NoResultFound, MultipleResultsFound):
            self.printError("The Host you have entered is not known or valid.")
            return
        if options.ipAddress != None:
            if not dissomniag.model.IpAddress.checkValidIpAddress(options.ipAddress):
                self.printError("The IpAddress is not valid.")
            else:
                host.modMaintainandceIP(self.user, str(options.ipAddress), deleteOld = True)
        
        if options.adminUser != None:
            host.modAdministrativeUserName(self.user, str(options.adminUser))
        
        if options.bridgeName != None:
            host.modBridgedInterfaceName(self.user, str(options.bridgeName))
        
        dissomniag.saveCommit(session)

        
    
class delHost(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can delete Hosts!")
            
        parser = argparse.ArgumentParser(description = "Delete a Host", prog = args[0])
        parser.add_argument("commonName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        session = dissomniag.Session()
        
        host = None
        try:
            host = session.query(dissomniag.model.Host).filter(dissomniag.model.Host.commonName == str(options.commonName)).one()
        except (NoResultFound, MultipleResultsFound):
            self.printError("The Host you have entered is not known or valid.")
            return
        
        if not dissomniag.model.Host.deleteHost(self.user, host):
            self.printError("Could not delete Host.")
        
class checkHost(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can delete Hosts!")
            
        parser = argparse.ArgumentParser(description = "Check a Host", prog = args[0])
        parser.add_argument("commonName", action = "store")
        
        options = parser.parse_args(args[1:])
        session = dissomniag.Session()
        host = None
        try:
            host = session.query(dissomniag.model.Host).filter(dissomniag.model.Host.commonName == str(options.commonName)).one()
        except (NoResultFound, MultipleResultsFound):
            self.printError("The Host you have entered is not known or valid.")
            return
        
        host.checkFull(self.user)
        self.printSuccess("Checks started.")
        
            
            
