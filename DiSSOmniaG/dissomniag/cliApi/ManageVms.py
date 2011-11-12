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
    
    def printVm(self, vm, withXml = False):
        session = dissomniag.Session()
        session.expire(vm)
        print("VM Name: %s" % str(vm.commonName))
        print("UUID: %s" % str(vm.uuid))
        print("State: %s" % str(dissomniag.model.NodeState.getStateName(vm.state)))
        print("RamSize: %s" % str(vm.ramSize))
        #print("HD Created?: %s" % str(vm.isHdCreated))
        #print("Use HD: %s" % str(vm.useHD))
        #print("HdSize: %s" % str(vm.hdSize))
        print("VNC Port: %s" % str(vm.vncPort))
        print("VNC Password: %s" % str(vm.vncPassword))
        print("InstalledSoftware: %s" % str(vm.dynamicAptList))
        if vm.lastSeenClient == None:
            self.printError("Live Client last seen: %s" % str(vm.lastSeenClient))
        else:
            self.printSuccess("Live Client last seen: %s" % str(vm.lastSeenClient))
        for interface in vm.interfaces:
            print("InterfaceName: %s Mac: %s" % (str(interface.name), str(interface.macAddress)))
            if interface.ipAddresses != []:
                print("\t Address: %s" % str(interface.ipAddresses[0].addr))
        
        if withXml:
            print("XML: \n %s" % vm.getLibVirtString(self.user))
        print("\n")
        
    def printVmSet(self, vms = [], withXml = False):
        for vm in vms:
            self.printVm(vm, withXml)
    
    def printAll(self, withXml = False):
        session = dissomniag.Session()
        try:
            vms = session.query(dissomniag.model.VM).all()
        except NoResultFound:
            self.printError("There are no VMs to print.")
            return
        else:
            self.printVmSet(vms, withXml)
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can list Nets!")
            return
        
        parser = argparse.ArgumentParser(description = 'List VMs', prog = args[0])
        
        parser.add_argument("-a", "--all", dest = "all", action = "store_true", default = True)
        parser.add_argument("-x", "--XML", dest = "xml", action = "store_true", default = False)
        parser.add_argument("-n" , "--name", dest = "name", action = "store", default = None)
        parser.add_argument("-t" , "--fromTopology", dest = "topo", action = "store", default = None)
        
        options = parser.parse_args(args[1:])
        
        withXml = options.xml
        session = dissomniag.Session()
        
        if options.all:
            self.printAll(withXml)
        elif options.name != None:
            try:
                vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.name == str(options.name)).one()
            except NoResultFound:
                self.printError("There is no VM with the Name %s." % str(options.name))
                return
            except MultipleResultsFound:
                self.printError("Query Inconsistency!")
                return
            else:
                self.printVm(vm, withXml = withXml)
                return
        elif options.topo != None:
            try:
                topo = session.query(dissomniag.model.Topology).filter(dissomniag.model.Topolgy.name == str(options.topo)).one()
            except NoResultFound:
                self.printError("There is no Topology with the Name %s." % str(options.topo))
                return
            except MultipleResultsFound:
                self.printError("Query Inconsistency!")
                return
            else:
                try: 
                    vms = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.topology == topo).all()
                except NoResultFound:
                    self.printError("There is no VM associated with the Topology %s." % str(options.topo))
                    return
                else:
                    self.printVmSet(vms, withXml = withXml)
                    return
        
class addVm(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can add a VM!")
            return
        
        parser = argparse.ArgumentParser(description = 'Add a VM to a host', prog = args[0])
        
        parser.add_argument("hostName", action = "store")
        parser.add_argument("vmName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        hostName = str(options.hostName)
        vmName = str(options.vmName)
        
        session = dissomniag.Session()
        
        try:
            host = session.query(dissomniag.model.Host).filter(dissomniag.model.Host.commonName == hostName).one()
        except NoResultFound:
            self.printError("There is no host with the name: %s" % hostName)
            return
        except MultipleResultsFound:
            self.printError("Query Inconsistency.")
            return
        else:
            vms = []
            try:
                vms = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).all()
            except NoResultFound:
                pass
            if vms != []:
                self.printError("A Vm with the name %s already exists." % vmName)#
                return
            vm = dissomniag.model.VM(self.user, vmName, host)
            self.printSuccess("Vm %s successfully created." % str(vm.commonName))
            return
        
        
class delVm(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can delete a VM!")
            return
        
        parser = argparse.ArgumentParser(description = 'Delete a VM', prog = args[0])

        parser.add_argument("vmName", action = "store")
        
        options = parser.parse_args(args[1:])
        session = dissomniag.Session()
        
        vmName = str(options.vmName)
        
        try:
            vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).one()
        except NoResultFound:
            self.printError("There is no Vm with the name: %s" % vmName)
            return
        except MultipleResultsFound:
            self.printError("Query Inconsistency.")
            return
        else:
            vm.createSanityDeleteJob(self.user)
            #dissomniag.model.VM.deleteVm(self.user, vm)
            return
        
class vmAddInterface(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can add an interface to a VM!")
            return
        
        parser = argparse.ArgumentParser(description = 'Add a VM Interface to a networkVM', prog = args[0])
                
        parser.add_argument("vmName", action = "store")
        parser.add_argument("netName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        vmName = str(options.vmName)
        netName = str(options.netName)
        
        session = dissomniag.Session()
        
        try:
            vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).one()
        except NoResultFound:
            self.printError("There is no Vm with the name: %s" % vmName)
            return
        except MultipleResultsFound:
            self.printError("Query Inconsistency.")
            return
        
        try:
            nets = session.query(dissomniag.model.generatedNetwork).filter(dissomniag.model.generatedNetwork.name == netName).all()
        except NoResultFound:
            self.printError("There is no Net with the name: %s" % netName)
            return
        else:
            net = None
            for myNet in nets:
                if vm.host in myNet.nodes:
                    net = myNet
                    break
            
            if net == None:
                self.printError("The net and the vm does not belong to the same host.")
                return
        
        vm.addInterfaceToNet(self.user, net)
        
class vmDelInterface(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can delete an interface from a net!")
            return
        
        parser = argparse.ArgumentParser(description = 'Delete a VM Interface from a networkVM', prog = args[0])
                
        parser.add_argument("vmName", action = "store")
        parser.add_argument("ifName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        vmName = str(options.vmName)
        ifName = str(options.ifName)
        
        session = dissomniag.Session()
        
        try:
            vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).one()
        except NoResultFound:
            self.printError("There is no Vm with the name: %s" % vmName)
            return
        except MultipleResultsFound:
            self.printError("Query Inconsistency.")
            return
        found = False
        for interface in vm.interfaces:
            if interface.name == ifName:
                dissomniag.model.Interface.deleteInterface(self.user, interface)
                found = True
                break
        if found:
            self.printSuccess("Successfully deleted Interface %s from %s" % (ifName, vmName))
        else:
            self.printError("Could not delete an Interface with the name %s from %s" % (ifName, vmName))
        
class prepareVm(CliMethodABCClass.CliMethodABCClass):
        
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can prepare a VM!")
            return
        
        parser = argparse.ArgumentParser(description = 'Prepare a VM', prog = args[0])
                
        parser.add_argument("vmName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        vmName = str(options.vmName)
        
        session = dissomniag.Session()
        
        try:
            vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).one()
        except NoResultFound:
            self.printError("There is no Vm with the name: %s" % vmName)
            return
        except MultipleResultsFound:
            self.printError("Query Inconsistency.")
            return
        
        vm.createPrepareJob(self.user)
        
class deployVm(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can deploy a VM!")
            return
        
        parser = argparse.ArgumentParser(description = 'Deploy a VM', prog = args[0])
                
        parser.add_argument("vmName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        vmName = str(options.vmName)
        
        session = dissomniag.Session()
        
        try:
            vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).one()
        except NoResultFound:
            self.printError("There is no Vm with the name: %s" % vmName)
            return
        except MultipleResultsFound:
            self.printError("Query Inconsistency.")
            return
        
        vm.createDeployJob(self.user)
        
class startVm(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can start a VM!")
            return
        
        parser = argparse.ArgumentParser(description = 'Start a VM', prog = args[0])
                
        parser.add_argument("vmName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        vmName = str(options.vmName)
        
        session = dissomniag.Session()
        
        try:
            vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).one()
        except NoResultFound:
            self.printError("There is no Vm with the name: %s" % vmName)
            return
        except MultipleResultsFound:
            self.printError("Query Inconsistency.")
            return
        
        vm.createStartJob(self.user)
        
        
class stopVm(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can stop a VM!")
            return
        
        parser = argparse.ArgumentParser(description = 'Stop a VM', prog = args[0])
                
        parser.add_argument("vmName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        vmName = str(options.vmName)
        
        session = dissomniag.Session()
        
        try:
            vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).one()
        except NoResultFound:
            self.printError("There is no Vm with the name: %s" % vmName)
            return
        except MultipleResultsFound:
            self.printError("Query Inconsistency.")
            return
        
        vm.createStopJob(self.user)
        
class refreshVm(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can refresh a VM!")
            return
        
        parser = argparse.ArgumentParser(description = 'Refresh a VM', prog = args[0])
                
        parser.add_argument("vmName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        vmName = str(options.vmName)
        
        session = dissomniag.Session()
        
        try:
            vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).one()
        except NoResultFound:
            self.printError("There is no Vm with the name: %s" % vmName)
            return
        except MultipleResultsFound:
            self.printError("Query Inconsistency.")
            return
        
        vm.createTestJob(self.user)
        vm.createLiveClientTestJob(self.user)
        
class resetVm(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can reset a VM!")
            return
        
        parser = argparse.ArgumentParser(description = 'Reset a VM', prog = args[0])
                
        parser.add_argument("vmName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        vmName = str(options.vmName)
        
        session = dissomniag.Session()
        
        try:
            vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).one()
        except NoResultFound:
            self.printError("There is no Vm with the name: %s" % vmName)
            return
        except MultipleResultsFound:
            self.printError("Query Inconsistency.")
            return
        
        vm.createResetJob(self.user)
        
class totalResetVm(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("Only Admin Users can reset a VM!")
            return
        
        parser = argparse.ArgumentParser(description = 'Total reset a VM', prog = args[0])
                
        parser.add_argument("vmName", action = "store")
        
        options = parser.parse_args(args[1:])
        
        vmName = str(options.vmName)
        
        session = dissomniag.Session()
        
        try:
            vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).one()
        except NoResultFound:
            self.printError("There is no Vm with the name: %s" % vmName)
            return
        except MultipleResultsFound:
            self.printError("Query Inconsistency.")
            return
        
        vm.createTotalResetJob(self.user)
