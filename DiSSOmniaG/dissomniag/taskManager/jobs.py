# -*- coding: utf-8 -*-
"""
Created on 27.07.2011

@author: Sebastian Wallat
"""
import logging
from abc import ABCMeta
import sqlalchemy as sa
from sqlalchemy import Column
import datetime

import dissomniag
import dissomniag.dbAccess
import tasks
import context

log = logging.getLogger("taskManagaer.jobs")

class JobStates:
    QUEUED = 0
    RUNNING = 1
    REVERTING = 2
    CANCELLED = 3
    SUCCEDED = 4
    FAILED = 5
    FAILED_UNREVERTABLE = 6

class Job(dissomniag.dbAccess.Base):
    """
    classdocs
    """
    __tablename__ = 'jobs'
    
    id = Column(sa.types.Integer, primary_key = True)
    description = Column(sa.types.Text, nullable = False)
    startTime = Column(sa.types.DateTime, default = datetime.datetime.now(), nullable = False)
    endTime = Column(sa.types.DateTime)
    state = Column(sa.types.Enum(JobStates().getList()), sa.CheckConstraint("0 >= state > 7", name = "jobState"), nullable = False)
    trace = Column(sa.types.Text)
    
    
    currentTaskId = 0
    isCancelled = False


    def __init__(self, Context, Description):
        """
        Constructor
        """
        self.state = JobStates.QUEUED
        self.context = Context
        self.description = Description
        self.jobList = []
        self.currentTaskId = 0
        self.isCancelled = False
        
    def addTask(self, Task):
        self.jobList.append(Task)
        
    def run(self):
        """
        Called from worker.
        """
        self.state = JobStates.RUNNING
        
    
    def _revertFrom(self, taskId):
        """
        Revert performed Tasks.
        """
        self.state = JobStates.REVERTING
        
    def cancel(self):
        """
        Cancel Job
        """
        self.state = JobStates.CANCELLED
        
    def trace(self, traceMessage):
        """
        Adds a Trace message from a Task or the running Job.
        """
        pass
    
    def getTrace(self):
        """
        returns the Trace Message from the running Job.
        """
        pass
    
    def getDetailsJson(self):
        """
        returns a details in Json Format
        """
        pass

    def getDetails(self):
        """
        return Detailed String (Colorisation in view)
        """
        pass
    
    @staticmethod
    def getJobListJson():
        """
        Get a list of all Jobs Json
        """
        pass
    
    @staticmethod
    def getJobList():
        """
        Get a job list (Colorisation in view)
        """
        pass
    
    @staticmethod
    def cleanUpJobDatabase():
        """
        Cleans up old jobs in the database
        """
        pass
    
    
        
        
        
