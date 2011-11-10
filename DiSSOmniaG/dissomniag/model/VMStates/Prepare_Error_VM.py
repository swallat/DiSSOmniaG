'''
Created on 01.11.2011

@author: Sebastian Wallat
'''
import dissomniag
from dissomniag.model.VMStates import *

import logging

log = logging.getLogger("model.VMStates.Prepare_Error_VM")

class Prepare_Error_VM(AbstractVMState):
    '''
    classdocs
    '''
    def test(self, job):
        return self.sanityCheck(job)
    
    def prepare(self, job):
        return self.sanityCheck(job)
    
    def deploy(self, job):
        self.vm.changeState(dissomniag.model.NodeState.NOT_CREAED)
        return self.vm.runningState.deploy(job)
    
    def start(self, job):
        self.vm.changeState(dissomniag.model.NodeState.NOT_CREAED)
        return self.vm.runningState.start(job)
    
    def stop(self, job):
        return True
    
    def sanityCheck(self, job):
        self.vm.changeState(dissomniag.model.NodeState.NOT_CREATED)
        return self.vm.runningState.prepare(job)
    
    def reset(self, job):
        self.vm.changeState(dissomniag.model.NodeState.PREPARED)
        return self.vm.runningState.reset(job)
        