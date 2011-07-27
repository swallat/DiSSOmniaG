# -*- coding: utf-8 -*-
"""
Created on 27.07.2011

@author: Sebastian Wallat
"""
import logging

import dissomniag

log = logging.getLogger("taskManagaer.worker")

class WorkerStates:
    NOT_RUNNING = 0
    RUNNING = 1
    CANCELED = 2
    STOPED = 3
    
class WorkerJobList(object):
    
    def __init__(self):
        pass
    
    def addJob(self, job):
        pass
    
    def getJob(self):
        pass

class Worker(object):
    """
    classdocs
    """


    def __init__(self):
        """
        Constructor
        """
        self.state = WorkerStates.NOT_RUNNING
        self.jobList = []
        self.runningJob = None
    
    def cancel(self):
        self.state = WorkerStates.CANCELED
        self.runningJob.cancel()
    
    def run(self):
        pass
    
        
