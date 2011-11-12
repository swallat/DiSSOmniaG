'''
Created on 01.11.2011

@author: Sebastian Wallat
'''

import dissomniag
from dissomniag.model.VMStates import *

import logging

log = logging.getLogger("model.VMStates.Runtime_Error_VM")

class Runtime_Error_VM(AbstractVMState):
    '''
    classdocs
    '''
    def test(self, job):
        try:
            ret = self.sanityCheck(job)
        except Exception:
            self.vm.changeState(dissomniag.model.NodeState.DEPLOY_ERROR)
            return self.vm.runningState.test(job)
        else:
            return ret
    
    def prepare(self, job):
        raise dissomniag.taskManager.TaskFailed("VM in inconsistent state! Could not recreate image!")
    
    def deploy(self, job):
        return self.stop()
    
    def start(self, job):
        return self.sanityCheck(job)
    
    def stop(self, job):
        self.vm.changeState(dissomniag.model.NodeState.CREATED)
        return self.vm.runningState.stop(job)
    
    def sanityCheck(self, job):
        self.vm.changeState(dissomniag.model.NodeState.CREATED)
        try:
            self.vm.runningState.stop(job)
        except Exception:
            self.vm.changeState(dissomniag.model.NodeState.DEPLOYED)
        return self.vm.runningState.start(job)
        
    def reset(self, job):
        return self.stop(job)