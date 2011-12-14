# -*- coding: utf-8 -*-
# DiSSOmniaG (Distributed Simulation Service wit OMNeT++ and Git)
# Copyright (C) 2011, 2012 Sebastian Wallat, University Duisburg-Essen
# 
# Based on an idea of:
# Sebastian Wallat <sebastian.wallat@uni-due.de, University Duisburg-Essen
# Hakim Adhari <hakim.adhari@iem.uni-due.de>, University Duisburg-Essen
# Martin Becke <martin.becke@iem.uni-due.de>, University Duisburg-Essen
#
# DiSSOmniaG is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DiSSOmniaG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DiSSOmniaG. If not, see <http://www.gnu.org/licenses/>
import logging
import subprocess
import shlex
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
    FAILED_BUT_GO_AHEAD = False
    SUCCESS = True
    
class TaskException(Exception):
    __metaclass__ = ABCMeta
    """
    Class doc
    """
    def __init__(self, value = None):
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
    
      
    def call(self, JobObject, Context, lastFailed = False):
        self.job = JobObject
        self.context = Context
        self.lastFailed = lastFailed
        assert self.job != None
        assert self.context != None
        self.run()
    
    @abstractmethod   
    def run(self):
        raise NotImplementedError()
        
    def callRevert(self, JobObject, Context, lastFailed = False):
        self.job = JobObject
        self.context = Context
        assert self.job != None
        assert self.context != None
        self.revert()
        
    @abstractmethod   
    def revert(self):
        raise NotImplementedError()
    
    def multiLog(self, msg, log = None):
        if log != None:
            log.info(msg)
        self.job.trace(msg)
        
    def callSubprocessAndLog(self, cmd, log = log):
        cmd = shlex.split(cmd)
        proc = subprocess.Popen(cmd, stdout = subprocess.PIPE,
                                     stderr = subprocess.STDOUT)
        
        while True:
            line = proc.stdout.readline()
            line = line.strip()
            if not line:
                break
            self.multiLog(line, log)
        
        self.stdout, self.stderr = proc.communicate()
        
        return proc
