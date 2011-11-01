'''
Created on 01.11.2011

@author: Sebastian Wallat
'''
import dissomniag


class Prepared_VM(dissomniag.model.VMStates.AbstractVMState):
    '''
    classdocs
    '''
    def test(self):
        raise NotImplementedError()
    
    def create(self):
        raise NotImplementedError()
    
    def deploy(self):
        raise NotImplementedError()
    
    def start(self):
        raise NotImplementedError()
    
    def stop(self):
        raise NotImplementedError()
    
    def sanity(self):
        raise NotImplementedError()
    
    def reset(self):
        raise NotImplementedError()