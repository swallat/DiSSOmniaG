'''
Created on 01.11.2011

@author: Sebastian Wallat
'''
import dissomniag

import logging

log = logging.getLogger("model.VMStates.Prepare_Error_VM")

class Prepare_Error_VM(dissomniag.model.VMStates.AbstractVMState):
    '''
    classdocs
    '''
    def test(self, job):
        return self.sanityCheck(job)
    
    def prepare(self, job):
        if self.sanityCheck(job):
            self.vm.changeState(dissomniag.model.NodeState.NOT_CREATED)
            return self.vm.runningState.create(job)
        else:
            raise dissomniag.taskManager.TaskFailed("VM could not be created.")
    
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
        