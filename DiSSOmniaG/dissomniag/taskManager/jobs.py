# -*- coding: utf-8 -*-
"""
Created on 27.07.2011

@author: Sebastian Wallat
"""
import logging
from abc import ABCMeta
import sqlalchemy as sa
from sqlalchemy import Column
from sqlalchemy.orm import relationship 
import datetime
import threading

import dissomniag
import dissomniag.dbAccess
import tasks
import context
import dispatcher
from dissomniag.taskManager.dispatcher import Dispatcher

log = logging.getLogger("taskManagaer.jobs")

class JobStates:
    QUEUED = 0
    RUNNING = 1
    REVERTING = 2
    CANCELLED = 3
    SUCCEDED = 4
    FAILED = 5
    FAILED_UNREVERTABLE = 6
    
class JobStartNotAllowed(Exception):
    """
    Class doc
    """
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)

class Job(dissomniag.dbAccess.Base, threading.Thread):
    """
    classdocs
    """
    __tablename__ = 'jobs'
    
    id = Column(sa.types.Integer, primary_key = True)
    description = Column(sa.types.Text, nullable = False)
    startTime = Column(sa.types.DateTime, default = datetime.datetime.now(), nullable = False)
    endTime = Column(sa.types.DateTime)
    state = Column(sa.types.Integer, sa.CheckConstraint("0 >= state > 7", name = "jobState"), nullable = False)
    trace = Column(sa.types.Text)
    user_id = Column(sa.types.Integer, sa.ForeignKey("users.id"))
    user = relationship("User", backref = "jobs")
    
    
    currentTaskId = 0
    isCancelled = False


    def __init__(self, jobId, context, description, group = None, target = None, name = None,
                 args = (), kwargs = None, verbose = None):
        """
        Constructor
        """
        threading.Thread.__init__(self, group = group, target = target,
                                      name = name, verbose = verbose)
        self.state = JobStates.QUEUED
        self.context = context
        self.description = description
        self.taskList = []
        self.currentTaskId = 0
        self.runningLock = threading.RLock()
        self.writeProperty = threading.Condition()
        self.dispatcher = None
        
        session = dissomniag.Session()
        session.commit()
        
    def start(self, dispatcher):
        """
        Overwrite standard start method.
        Ensures that only a dispatcher can start a Job
        """
        if not threading.current_thread().name().startsWith(dispatcher.Dispatcher.startName):
            raise JobStartNotAllowed()
        
        self.dispatcher = dispatcher
        
        threading.Thread.start(self)
        
    def addTask(self, Task):
        """
        Add a Task to a Job
        
        Ensure that no Tasks can be added after a Job has started.
        """
        with self.runningLock:
            self.taskList.append(Task)
        
    def run(self):
        """
        Called from worker.
        """
        
        if not isinstance(self.dispatcher, Dispatcher):
            log.WARNING("Dispatcher not set in Job %d at startup." % self.id)
            return
        
        with self.runningLock:
            with self.writeProperty:
                session = dissomniag.Session()
                self.state = JobStates.RUNNING 
                session.commit()
            
            try:
                self._run()
                """ 
                Run all tasks
                """
                with self.writeProperty:
                    self.state = JobStates.SUCCEDED
                    """
                    Run was successfull
                    """
            except tasks.TaskFailed, f:
                """
                A task failed, but not unrevertable
                """
                try:
                    self._revertFrom(self.currentTaskId)
                    """
                    Try to revert
                    """
                    with self.writeProperty:
                        self.state = JobStates.FAILED
                        """
                        If revert was successful, mark this job as 
                        Failed (normally)
                        """ 
                except (tasks.TaskFailed, tasks.UnrevertableFailure), f:
                    """
                    If annother Error occures:
                    The system has been corrupted unrevertable.
                    """
                    with self.writeProperty:
                        self.state = JobStates.FAILED_UNREVERTABLE
                        """
                        Mark the Job as Failed.
                        The System may be corrupted
                        """
                        
            except tasks.UnrevertableFailure, f:
                """
                An unrevertable Failure occured.
                The system may be corrupted.
                """
                with self.writeProperty:
                    self.state = JobStates.FAILED_UNREVERTABLE
                    """
                    Mark the Job as Failed.
                    The System may be corrupted
                    """
            finally:
                session.commit()
                """
                Commit the final state to the Database
                """
    
    def _run(self):
        """
        Runs all Jobs.
        
        Raises all Exceptions from job.run()
        """
        lastFailed = False
        for i, task in enumerate(self.taskList):
            
            if self.state == JobStates.CANCELLED:
                """
                Check if a cancell request occured
                """
                self.trace("Job %s cancelled while executing taskId: %s" % \
                            (str(self.id), str(self.currentTaskId)))
                log.INFO("Job %s cancelled while executing taskId: %s" % \
                            (str(self.id), str(self.currentTaskId)))
                raise tasks.TaskFailed()
            
            self.currentTaskId = i
            param = task.run(self, self.context, lastFailed)
            if param == tasks.TaskReturns.FAILED_BUT_GO_AHEAD:
                lastFailed = True
                self.trace("In Job %s the Task %s failed without stopping" % \
                            (str(self.id), str(self.currentTaskId)))
            else: # param == task.TaskReturns.SUCCESS
                lastFailed = False
    
    def _revertFrom(self, taskId):
        """
        Revert performed Tasks.
        """
        with self.writeProperty:
            
            if self.state == JobStates.CANCELLED:
                """
                Check if a cancell request occured
                """
                self.trace("Job %s cancelled while executing taskId: %s" % \
                            (str(self.id), str(self.currentTaskId)))
                log.INFO("Job %s cancelled while executing taskId: %s" % \
                            (str(self.id), str(self.currentTaskId)))
                raise tasks.TaskFailed()
            
            self.state = JobStates.REVERTING
            session = dissomniag.Session()
            session.commit()
        
        lastFailed = False
        
        for i, task in zip(range(taskId, -1, -1), reversed(self.taskList[:(taskId + 1)])):
            
            if self.state == JobStates.CANCELLED:
                """
                Check if a cancell request occured
                """
                self.trace("Job %s cancelled while executing taskId: %s" % \
                            (str(self.id), str(self.currentTaskId)))
                log.INFO("Job %s cancelled while executing taskId: %s" % \
                            (str(self.id), str(self.currentTaskId)))
                raise tasks.TaskFailed()
            
            self.currentTaskId = i
            
            try:
                
                param = task.revert(self, self.context, lastFailed)
                
            except NotImplementedError:
                self.trace("In Job %s the Task %s failed reverting." % \
                            (str(self.id), str(self.currentTaskId)))
                log.INFO("In Job %s the Task %s failed reverting." % \
                            (str(self.id), str(self.currentTaskId)))
                raise tasks.UnrevertableFailure()
            else:
            
                if param == tasks.TaskReturns.FAILED_BUT_GO_AHEAD:
                    lastFailed = True
                    self.trace("In Job %s the Task %s failed without stopping" % \
                            (str(self.id), str(self.currentTaskId)))
                else: # param == task.TaskReturns.SUCCESS
                    lastFailed = False
            
        
    def cancel(self):
        """
        Cancel Job
        """
        with self.writeProperty:
            self.state = JobStates.CANCELLED
            session = dissomniag.Session()
            session.commit()
        
    def trace(self, traceMessage):
        """
        Adds a Trace message from a Task or the running Job.
        """
        with self.writeProperty:
            self.trace += traceMessage + "\n"
            self.state = JobStates.CANCELLED
            session = dissomniag.Session()
            session.commit()
    
    def getTrace(self):
        """
        returns the Trace Message from the running Job.
        """
        return self.trace
    
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
    
    
        
        
        
