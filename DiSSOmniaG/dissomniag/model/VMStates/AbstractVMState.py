'''
Created on 01.11.2011

@author: Sebastian Wallat
'''
from abc import ABCMeta, abstractmethod
import dissomniag

class AbstractVMState():
    __metaclass__ = ABCMeta
    
    def __init__(self, vm):
        self.vm = vm
        
    @abstractmethod
    def test(self):
        raise NotImplementedError()
    
    @abstractmethod
    def create(self):
        raise NotImplementedError()
    
    @abstractmethod
    def deploy(self):
        raise NotImplementedError()
    
    @abstractmethod
    def start(self):
        raise NotImplementedError()
    
    @abstractmethod
    def stop(self):
        raise NotImplementedError()
    
    @abstractmethod
    def sanity(self):
        raise NotImplementedError()
    
    @abstractmethod
    def reset(self):
        raise NotImplementedError()