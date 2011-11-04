'''
Created on 01.11.2011

@author: Sebastian Wallat
'''
import libvirt
import dissomniag

import logging

log = logging.getLogger("model.VMStates.Created_VM")

class Created_VM(dissomniag.model.VMStates.AbstractVMState):
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
            self.vm.changestate(dissomniag.model.NodeState.RUNTIME_ERROR)
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
        raise NotImplementedError()
    
    def start(self, job):
        raise NotImplementedError()
    
    def stop(self, job):
        raise NotImplementedError()
    
    def sanityCheck(self, job):
        raise NotImplementedError()
    
    def reset(self, job):
        raise NotImplementedError()