# -*- coding: utf-8 -*-
"""
Created on 08.08.2011

@author: Sebastian Wallat
"""

from abc import ABCMeta, abstractmethod
import dissomniag

class IdentityRestartNotAllowed(Exception):
    pass

class Identity():
    __metaclass__ = ABCMeta
    isStarted = False
    
    """
    classdocs
    """
    
    @abstractmethod
    def start(self):
        if not self.isStarted:
            self.isStarted = True
        else:
            raise IdentityRestartNotAllowed()
    
    @abstractmethod
    def _tearDown(self):
        raise NotImplementedError()


identity = None

def _getVMIdentity():
    pass

def _getControlIdentity():
    return dissomniag.model.ControlSystem()

def getIdentity():
    global identity
    if identity == None:
        if dissomniag.config.dissomniag.isCentral:
            identity = _getControlIdentity()
        else:
            identity = _getVMIdentity()
    
    return identity

def start():
    dissomniag.init()
    getIdentity().start()


        




