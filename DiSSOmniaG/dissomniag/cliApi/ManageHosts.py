# -*- coding: utf-8 -*-
"""
Created on 31.08.2011

@author: Sebastian Wallat
"""
import logging, argparse
from colorama import Fore, Style, Back
import sys, time
import getpass
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import dissomniag
from dissomniag.utils import CliMethodABCClass

log = logging.getLogger("cliApi.ManageHosts")


class listHosts(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can add Hosts!")
            return
        
        session = dissomniag.Session()
        self.printHeading()
        hosts = None
        try:
            hosts = session.query(dissomniag.model.Host).all()
        except NoResultFound:
            pass
        
        for host in hosts:
            self.printHost(host)
                
    def printHeading(self):
        self.printInfo("CommonName: \t State:     UUID: \t\t\t\t MaintainanceIP: AdminUser: \t lastChecked: \t libvirt Version: kvmUsable: \t freeDiskspace: ramCapacity: \t")
        self.printInfo("=============================================================================================================================================================================")
                
    def printHost(self, host):
        
        if host == None or type(host) != dissomniag.model.Host:
            print( str(type(host)))
            print(str(dissomniag.model.Host == type(host)))
            return
        
        print("%s \t\t%s     %s \t %s \t %s \t \t %s \t \t %s \t \t  %s \t \t %s \t \t %s" %
              (str(host.commonName), str(dissomniag.model.NodeState.getStateName(host.state)), str(host.uuid),  str(host.getMaintainanceIP().addr), str(host.administrativeUserName), str(host.lastChecked), str(host.libvirtVersion), str(host.kvmUsable), str(host.freeDiskspace), str(host.ramCapacity)))
        
        
            
        
        
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
        
        options = parser.parse_args(args[1:])
        
        if not dissomniag.model.IpAddress.checkValidIpAddress(options.ipAddress):
            self.printError("The IpAddress is not valid.")
            return
        
        if options.adminUser == None:
            adminUser = "root"
        else:
            adminUser = options.adminUser
        
        session = dissomniag.Session()
        host = dissomniag.model.Host(self.user, commonName = options.commonName, maintainanceIP = options.ipAddress, administrativeUserName = adminUser)
        session.add(host)
        session.commit()
        
        

class modHost(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can modify Hosts!")
        
    
class delHost(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can delete Hosts!")