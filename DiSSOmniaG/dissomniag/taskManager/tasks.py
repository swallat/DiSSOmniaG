# -*- coding: utf-8 -*-
"""
Created on 27.07.2011

@author: Sebastian Wallat
"""
import logging
from abc import ABCMeta, abstractmethod

import dissomniag

log = logging.getLogger("taskManagaer.tasks")

class TaskStates:
    QUEUED = 0
    RUNNING = 1
    REVERTING = 2
    SUCCEDED = 3
    FAILED = 4
    
class TaskReturns:
    FAILED_BUT_GO_AHEAD = 0
    SUCCESS = 1
    
class TaskException(Exception):
    """
    Class doc
    """
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)
    
class TaskFailed(TaskException):
    """
    Class doc
    """
    pass
    
class UnrevertableFailure(TaskException):
    """
    Raised when an Failer appears that cannot be reverted.
    """
    pass

class TaskIsUnrevertable(TaskException):
    """
    Raised when Job tries to revert the current Task although it is
    not revertable.
    """
    pass

class AtomicTask:
    __metaclass__ = ABCMeta
    """
    classdocs
    """
    
    
    def __init__(self, isRevertable = None):
        """
        Constructor
        """
        self.state = TaskStates.QUEUED
        self.job = None
        self.context = None
        if isRevertable != None:
            self.isRevertable = isRevertable
        
    
    @abstractmethod
    def run(self, JobObject, Context):
        self.job = JobObject
        self.context = Context
        assert self.job != None
        assert self.context != None
        
    @abstractmethod
    def revert(self, JobObject, Context):
        self.job = JobObject
        self.context = Context
        assert self.job != None
        assert self.context != None
        
    def _isSelfRevertable(self):
        return self.isRevertable
        
