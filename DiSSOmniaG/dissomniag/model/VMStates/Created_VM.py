'''
Created on 01.11.2011

@author: Sebastian Wallat
'''
import libvirt
import dissomniag
from dissomniag.model.VMStates import *

import logging

log = logging.getLogger("model.VMStates.Created_VM")

class Created_VM(AbstractVMState):
    '''
    classdocs
    '''
    def test(self, job):
        session = dissomniag.Session()
        try:
            con = libvirt.open(str(self.vm.host.qemuConnector))
        except libvirt.libvirtError:
            self.vm.changeState(dissomniag.model.NodeState.RUNTIME_ERROR)
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            vm = con.lookupByName(self.vm.commonName)
        except libvirt.libvirtError:
            job.trace("VM is not Running.")
            self.vm.changeState(dissomniag.model.NodeState.RUNTIME_ERROR)
            return self.vm.runningState.sanityCheck(job)
        
        if vm.isActive() == 1:
            job.trace("VM state is correct!")
            return True
        else:
            job.trace("VM is not Running.")
            self.vm.changestate(dissomniag.model.NodeState.RUNTIME_ERROR)
            return self.vm.runningState.sanityCheck(job)
    
    def prepare(self, job):
        job.trace("VM already created!")
        return True
    
    def deploy(self, job):
        return True
    
    def start(self, job):
        return True
    
    def stop(self, job):
        try:
            con = libvirt.open(str(self.vm.host.qemuConnector))
        except libvirt.libvirtError:
            self.vm.changeState(dissomniag.model.NodeState.DEPLOY_ERROR)
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            vm = con.lookupByName(self.vm.commonName)
        except libvirt.libvirtError:
            self.multiLog("destroyVMOnHost: Could not find VM on host.", job, log)
        else:
            try:
                vm.destroy()
            except libvirt.libvirtError:
                self.multiLog("destroyVMOnHost: could not destroy or undefine vm", job, log)
                self.vm.changeState(dissomniag.model.NodeState.DEPLOY_ERROR)
                return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        
        self.vm.changeState(dissomniag.model.NodeState.DEPLOYED)
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def sanityCheck(self, job):
        return True
    
    def reset(self, job):
        returnMe = self.stop(job)
        self.vm.changeState(dissomniag.model.NodeState.DEPLOYED)
        return returnMe