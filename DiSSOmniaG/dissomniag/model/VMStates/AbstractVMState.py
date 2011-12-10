'''
Created on 01.11.2011

@author: Sebastian Wallat
'''
from abc import ABCMeta, abstractmethod

import dissomniag

import logging

log = logging.getLogger("model.VMStates.AbstractVMState")

class AbstractVMState():
    __metaclass__ = ABCMeta
    
    def __init__(self, vm, liveCd):
        self.vm = vm
        self.liveCd = liveCd
        #log.info("In AbstractVMState.__init__() vm: %s, liveCd: %s" % (str(self.vm), str(self.liveCd)))
        
    @abstractmethod
    def test(self, job):
        raise NotImplementedError()
    
    @abstractmethod
    def prepare(self, job):
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