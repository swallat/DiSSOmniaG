'''
Created on 01.11.2011

@author: Sebastian Wallat
'''
import dissomniag

import logging

log = logging.getLogger("model.VMStates.Deploy_Error_VM")

class Deploy_Error_VM(dissomniag.model.VMStates.AbstractVMState):
    '''
    classdocs
    '''
    def test(self, job):
        return self.sanityCheck(job)
    
    def prepare(self, job):
        return self.reset(job)
        
    def deploy(self, job):
        return self.sanityCheck(job)
    
    def start(self, job):
        if self.sanityCheck(job):
            return self.vm.runningJob.create(job)
        else:
            raise dissomniag.taskManager("VM could not be started!")
    
    def stop(self, job):
        return self.sanityCheck(job)
    
    def sanityCheck(self, job):
        self.vm.changeState(dissomniag.model.NodeState.PREPARED)
        return self.vm.runningState.deploy(job)
    
    def reset(self, job):
        self.vm.changeState(dissomniag.model.NodeState.DEPLOYED)
        if self.vm.runningState.reset(job):
            return True
        else:
            self.changeState(dissomniag.model.NodeState.PREPARE_ERROR)
            return False
        