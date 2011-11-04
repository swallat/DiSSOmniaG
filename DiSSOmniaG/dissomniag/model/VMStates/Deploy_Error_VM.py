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
        raise dissomniag.taskManager.TaskFailed("VM in inconsistent state! Could not recreate image!")
    
    def deploy(self, job):
        raise NotImplementedError()
    
    def start(self, job):
        if self.sanityCheck(job):
            return self.vm.runningJob.create(job)
        else:
            raise dissomniag.taskManager("VM could not be started!")
    
    def stop(self, job):
        raise NotImplementedError()
    
    def sanityCheck(self, job):
        raise NotImplementedError()
    
    def reset(self, job):
        raise NotImplementedError()
        