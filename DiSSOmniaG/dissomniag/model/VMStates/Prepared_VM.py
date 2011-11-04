'''
Created on 01.11.2011

@author: Sebastian Wallat
'''
import dissomniag

import logging

log = logging.getLogger("model.VMStates.Prepared_VM")

class Prepared_VM(dissomniag.model.VMStates.AbstractVMState):
    '''
    classdocs
    '''
    
    def test(self, job):
        try:
            upToDate = self.vm.liveCd.checkOnHdUpToDate(self.job.getUser(), refresh = True)
        except Exception as e:
            job.trace(e.message)
            self.vm.changeState(dissomniag.model.NodeState.PREPARE_ERROR)
            return self.vm.runningState.sanityCheck(job)
        else:
            if upToDate:
                job.trace("VM in correct state!")
                return True
            else:
               self.vm.changeState(dissomniag.model.NodeState.PREPARE_ERROR)
               return self.vm.runningState.sanityCheck(job)
    
    def prepare(self, job):
        job.trace("VM already created.")
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