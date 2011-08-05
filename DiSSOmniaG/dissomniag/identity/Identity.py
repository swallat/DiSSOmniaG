# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
from abc import ABCMeta, abstractmethod

import dissomniag

class Identity():
    __metaclass__ = ABCMeta()
    
    """
    classdocs
    """
    
    def __new__(cls, *args, **kwargs):
        # Store instance on cls._instance_dict with cls hash
        key = str(hash(cls))
        if not hasattr(cls, '_instance_dict'):
            cls._instance_dict = {}
        if key not in cls._instance_dict:
            cls._instance_dict[key] = \
                super(Identity, cls).__new__(cls, *args, **kwargs)
        return cls._instance_dict[key]
    
    @abstractmethod
    def start(self):
        raise NotImplementedError()
    
    @abstractmethod
    def tearDown(self):
        raise NotImplementedError()
    
class ControlSystemIdentity(Identity, dissomniag.model.ControlSystem.ControlSystem):
    
    def start(self):
        pass
    
    def tearDown(self):
        pass
    
class VmIdentity(Identity, dissomniag.model.VM.VM):
    pass
