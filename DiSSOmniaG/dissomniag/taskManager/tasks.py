# -*- coding: utf-8 -*-
"""
Created on 27.07.2011

@author: Sebastian Wallat
"""
import logging
from abc import ABCMeta, abstractmethod
from _pyio import __metaclass__

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
    __metaclass__ = ABCMeta
    """
    Class doc
    """
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)
    
class TaskFailed(TaskException):# 
    """
    Class doc
    """
    pass
    
class UnrevertableFailure(TaskException):
    """
    Raised when an Failure appears that cannot be reverted.
    """
    pass

class AtomicTask:
    __metaclass__ = ABCMeta
    """
    classdocs
    """
    
    
    def __init__(self):
        """
        Constructor
        """
        self.state = TaskStates.QUEUED
        self.job = None
        self.context = None
        
    
    @abstractmethod
    def run(self, JobObject, Context, lastFailed = False):
        self.job = JobObject
        self.context = Context
        assert self.job != None
        assert self.context != None
        
    @abstractmethod
    def revert(self, JobObject, Context, lastFailed = False):
        self.job = JobObject
        self.context = Context
        assert self.job != None
        assert self.context != None
        
