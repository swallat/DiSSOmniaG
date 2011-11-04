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
    def test(self, job):
        raise NotImplementedError()
    
    @abstractmethod
    def createImage(self, job):
        raise NotImplementedError()
    
    @abstractmethod
    def deploy(self, job):
        raise NotImplementedError()
    
    @abstractmethod
    def start(self, job):
        raise NotImplementedError()
    
    @abstractmethod
    def stop(self, job):
        raise NotImplementedError()
    
    @abstractmethod
    def sanityCheck(self, job):
        raise NotImplementedError()
    
    @abstractmethod
    def reset(self, job):
        raise NotImplementedError()
    
    def multiLog(self, msg, job, log = None):
        if log != None:
            log.info(msg)
        job.trace(msg)