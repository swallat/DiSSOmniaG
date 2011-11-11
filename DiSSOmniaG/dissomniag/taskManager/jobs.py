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
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import and_
import datetime
import threading

import dissomniag
import dissomniag.dbAccess
import dissomniag.auth.User
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
    
    @staticmethod
    def getStateName(id):
        if id == JobStates.QUEUED:
            return "QUEUED"
        if id == JobStates.RUNNING:
            return "RUNNING"
        if id == JobStates.REVERTING:
            return "REVERTING"
        if id == JobStates.CANCELLED:
            return "CANCELLED"
        if id == JobStates.SUCCEDED:
            return "SUCCEDED"
        if id == JobStates.FAILED:
            return "FAILED"
        if id == JobStates.FAILED_UNREVERTABLE:
            return "FAILED_UNREVERTABLE"
        else:
            return "UNKNOWN"
    @staticmethod
    def getFinalStates():
        return (JobStates.CANCELLED,
                     JobStates.SUCCEDED,
                     JobStates.FAILED,
                     JobStates.FAILED_UNREVERTABLE)
    @staticmethod
    def getRunningStates():
        return (JobStates.QUEUED,
                JobStates.RUNNING,
                JobStates.REVERTING)
        
    
class JobStartNotAllowed(Exception):
    """
    Class doc
    """
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)
    
class JobInfo(dissomniag.dbAccess.Base):
    __tablename__ = 'jobs'
    
    id = Column(sa.types.Integer, primary_key = True)
    description = Column(sa.types.Text, nullable = False)
    startTime = Column(sa.types.DateTime, default = datetime.datetime.now(), nullable = False)
    endTime = Column(sa.types.DateTime)
    state = Column(sa.types.Integer, sa.CheckConstraint("0 <= state < 7", name = "jobState"), nullable = False)
    trace = Column(sa.types.Text)
    user_id = Column(sa.types.Integer, sa.ForeignKey("users.id")) # Many to One style
    user = relationship("User", backref = "jobs") # Many to One style
    
    def __init__(self, description, state, user = None):
        self.state = state
        self.user = user
        self.description = description

    def __repr__(self):
        if self.trace == None:
            printTrace = "None"
        else:
            printTrace = self.trace
        return "<JobInfo: id: %d, state: %s, description: %s, trace: %s>" % (self.id, JobStates.getStateName(self.state), self.description, printTrace)
        
class NoJobInfoObj(Exception):
    pass

class Job(threading.Thread):
    """
    classdocs
    """
    __tablename__ = 'jobs'
    
    currentTaskId = 0
    isCancelled = False


    def __init__(self, context, description, user = None, group = None, target = None, name = None,
                 args = (), kwargs = None, verbose = None):
        """
        Constructor
        """
        threading.Thread.__init__(self, group = group, target = target,
                                      name = name, verbose = verbose)
        session = dissomniag.Session()
        self.state = JobStates.QUEUED
        self.infoObj = JobInfo(description = description, state = self.state, user = user)
        session.add(self.infoObj)
        session.commit()
        session.flush()
        self.id = self.infoObj.id
        if user != None:
            self.user = user
        else:
            self.user = None
        
        
        self.context = context
        self.description = description
        self.taskList = []
        self.currentTaskId = 0
        self.runningLock = threading.RLock()
        self.writeProperty = threading.RLock()
        self.dispatcher = None
        
        self.infoObj = None
        
        
        
        
    def _setState(self, state):
        with self.writeProperty:
            self._reFetchInfoObj()
            self.state = state
            self.infoObj.state = state
        
    def _reFetchInfoObj(self):
        if self.infoObj == None:
            session = dissomniag.Session()
            try:
                self.infoObj = session.query(JobInfo).filter(JobInfo.id == self.id).one()
            except NoResultFound:
                raise NoJobInfoObj()
    
    def getState(self):
        info = self.getInfo()
        return info.state
    
    def getUser(self):
        info = self.getInfo()
        if info.user == None:
            return False
        else:
            return info.user
        
    def _getStatePrivate(self):
        self._reFetchInfoObj()
        if self.state != self.infoObj.state:
            session = dissomniag.Session()
            if self.state == JobStates.CANCELLED:
                self.trace("### JOB CANCELLED ###")
            self.infoObj.state = self.state
            session.commit()
        return self.state
    
    def getUserId(self):
        return self.user_id
    
        
    def getInfo(self):
        session = dissomniag.Session()
        try:
            return session.query(JobInfo).filter(JobInfo.id == self.id).one()
        except NoResultFound:
            raise NoJobInfoObj()
        
    def getId(self):
        return self.id
    
    def _setEndTime(self):
        with self.writeProperty:
            session = dissomniag.Session()
            self._reFetchInfoObj()
            self.infoObj.endTime = datetime.datetime.now()
            session.commit()
        
        
    def start(self, dispatcher):
        """
        Overwrite stanetdard start method.
        Ensures that only a dispatcher can start a Job
        """
        if not threading.current_thread().name.startswith(dispatcher.startName):
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
            
    def appendTask(self, index, Task):
        
        with self.runningLock:
            self.taskList.insert(index, Task)
            
    def getIndexOfTask(self, Task):
        
        with self.runningLock:
            return self.taskList.index(Task)
        
    def run(self):
        """
        Called from worker.
        """
        self._reFetchInfoObj()
        
        if not isinstance(self.dispatcher, Dispatcher):
            log.WARNING("Dispatcher not set in Job %d at startup." % self.id)
            return
        
        with self.runningLock:
            
            with self.writeProperty:
                if self._getStatePrivate() == JobStates.CANCELLED:
                    self._setEndTime()
                    self.dispatcher.jobFinished(self)
                    return
                
                session = dissomniag.Session()
                self._setState(JobStates.RUNNING) 
                session.commit()
                self.context.parse(self.getUser())
            
            try:
                self.trace("### RUNNING ###")
                self._run()
                """ 
                Run all tasks
                """
                with self.writeProperty:
                    self._setState(JobStates.SUCCEDED)
                    """
                    Run was successfull
                    """
            except tasks.TaskFailed:
                """
                A task failed, but not unrevertable
                """
                self.trace("### TASK FAILED, TRY REVERTING ###")
                try:
                    self._revertFrom(self.currentTaskId)
                    """
                    Try to revert
                    """
                    with self.writeProperty:
                        self._setState(JobStates.FAILED)
                        """
                        If revert was successful, mark this job as 
                        Failed (normally)
                        """ 
                except (tasks.TaskFailed, tasks.UnrevertableFailure):
                    """
                    If annother Error occures:
                    The system has been corrupted unrevertable.
                    """
                    self.trace("### TASK UNREVERTABLE FAILED ###")
                    with self.writeProperty:
                        self._setState(JobStates.FAILED_UNREVERTABLE)
                        """
                        Mark the Job as Failed.
                        The System may be corrupted
                        """
                        
            except tasks.UnrevertableFailure:
                """
                An unrevertable Failure occured.
                The system may be corrupted.
                """
                self.trace("### TASK UNREVERTABLE FAILED ###")
                with self.writeProperty:
                    self._setState(JobStates.FAILED_UNREVERTABLE)
                    """
                    Mark the Job as Failed.
                    The System may be corrupted
                    """
            finally:
                self.trace("### TASK END ###")
                self._setEndTime()
                self.dispatcher.jobFinished(self)
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
            
            if self._getStatePrivate() == JobStates.CANCELLED:
                """
                Check if a cancell request occured
                """
                self.trace("Job %s cancelled while executing taskId: %s" % \
                            (str(self.id), str(self.currentTaskId)))
                log.info("Job %s cancelled while executing taskId: %s" % \
                            (str(self.id), str(self.currentTaskId))) 
                raise tasks.TaskFailed()
            
            self.currentTaskId = i
            param = task.call(self, self.context, lastFailed)
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
            if not dissomniag.config.dispatcher.revertBeforeCancel:
                if self._getStatePrivate() == JobStates.CANCELLED:
                    """
                    Check if a cancell request occured
                    """
                    self.trace("Job %s cancelled while executing taskId: %s" % \
                                (str(self.id), str(self.currentTaskId)))
                    log.info("Job %s cancelled while executing taskId: %s" % \
                                (str(self.id), str(self.currentTaskId)))
                    raise tasks.TaskFailed()
            
            if self._getStatePrivate() != JobStates.CANCELLED:   
                self._setState(JobStates.REVERTING)
            session = dissomniag.Session()
            session.commit()
        
        lastFailed = False
        
        for i, task in zip(range(taskId, -1, -1), reversed(self.taskList[:(taskId + 1)])):
            
            if not dissomniag.config.dispatcher.revertBeforeCancel:
                if self._getStatePrivate() == JobStates.CANCELLED:
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
                
                param = task.callRevert(self, self.context, lastFailed)
                
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
    
    def jobCallIsCancelled(self):
        if self._getStatePrivate() == JobStates.CANCELLED:
            return True
        else:
            return False
        
    def cancelBeforeStartup(self):
        with self.runningLock:
            session = dissomniag.Session()
            self._reFetchInfoObj()
            self.state = JobStates.CANCELLED
            self.infoObj.state = self.state
            session.commit()
            self.infoObj = None
            
        
    def trace(self, traceMessage):
        """
        Adds a Trace message from a Task or the running Job.
        """
        with self.writeProperty:
            self._reFetchInfoObj()
            #try:
            #    self.infoObj.trace == None
            #except InvalidRequestError:
            if self.infoObj.trace == None:
                self.infoObj.trace = traceMessage + "\n"
            elif traceMessage == None:
                self.infoObj.trace += "\n"
            else:
                self.infoObj.trace += traceMessage + "\n"
                
            
    
    def getTrace(self):
        """
        returns the Trace Message from the running Job.
        """
        self._reFetchInfoObj()
        return self.infoObj.trace
    
    @staticmethod
    def getJobsViaUser(user, userName = None, withRunning = True, exclusiveRunning = False):
        """
        Get all Jobs per User
        """
        
        session = dissomniag.Session()
        if userName != None:
            try:
                otherUser = session.query(dissomniag.auth.User).filter(dissomniag.auth.User.username == str(userName)).one()
            except (NoResultFound, MultipleResultsFound):
                otherUser = None
        else:
            otherUser = None
        
        try:
            if user.isAdmin and userName != None and otherUser != None:
                if withRunning:
                    if exclusiveRunning:
                        return session.query(JobInfo).filter(and_(JobInfo.state.in_(JobStates.getRunningStates()), JobInfo.user == otherUser)).all()
                    else:
                        return session.query(JobInfo).filter(JobInfo.user == otherUser).all()
                else:
                    return session.query(JobInfo).filter(and_(JobInfo.state.in_(JobStates.getFinalStates()), JobInfo.user_id == otherUser)).all()
    
            elif userName == None or (userName != None and userName == user.username):
                if withRunning:
                    if exclusiveRunning:
                        return session.query(JobInfo).filter(and_(JobInfo.state.in_(JobStates.getRunningStates()), JobInfo.user == user)).all()
                    else:
                        return session.query(JobInfo).filter(JobInfo.user == user).all()
                else:
                    return session.query(JobInfo).filter(and_(JobInfo.state.in_(JobStates.getFinalStates()), JobInfo.user == user)).all()
            else:
                return None
        except NoResultFound:
            return None
            
    @staticmethod
    def getJobViaId(user, jobId, withZombi = True, exclusiveZombi = False, withRunning = True, exclusiveRunning = False):
        """
        Get a single Job with a specific ID
        """
        session = dissomniag.Session()
        #jobId = int(jobId)
        try:
            if withRunning:
                if exclusiveRunning:
                    if withZombi:
                        if exclusiveZombi:
                            job = session.query(JobInfo).filter(and_(JobInfo.state.in_(JobStates.getRunningStates()), JobInfo.id == jobId)).filter(JobInfo.user == None).one()
                        else:
                            job = session.query(JobInfo).filter(and_(JobInfo.state.in_(JobStates.getRunningStates()), JobInfo.id == jobId)).one()
                    else:
                        job = session.query(JobInfo).filter(and_(JobInfo.state.in_(JobStates.getRunningStates()), JobInfo.id == jobId)).filter(JobInfo.user != None).one()
    
                else:
                    if withZombi:
                        if exclusiveZombi:
                            job = session.query(JobInfo).filter(JobInfo.id == jobId).filter(JobInfo.user == None).one()
                        else:
                            job = session.query(JobInfo).filter(JobInfo.id == jobId).one()
                    else:
                        job = session.query(JobInfo).filter(JobInfo.id == jobId).filter(JobInfo.user != None).one()
    
            else:
                if withZombi:
                    if exclusiveZombi:
                        job = session.query(JobInfo).filter(and_(JobInfo.state.in_(JobStates.getFinalStates()), JobInfo.id == jobId)).filter(JobInfo.user == None).one()
                    else:
                        job = session.query(JobInfo).filter(and_(JobInfo.state.in_(JobStates.getFinalStates()), JobInfo.id == jobId)).one()
                else:
                    job = session.query(JobInfo).filter(and_(JobInfo.state.in_(JobStates.getFinalStates()), JobInfo.id == jobId)).filter(JobInfo.user != None).one()
        
        except (NoResultFound, MultipleResultsFound):
            return None
        
        if job != None and (user.isAdmin or job.user == user):
            return job
        else:
            return None
        
    @staticmethod
    def getJobs(user, withZombi = True, exclusiveZombi = False, withRunning = True, exclusiveRunning = False):
        """
        Get all Jobs in Db
        """
        if not user.isAdmin:
            return None
        session = dissomniag.Session()
        try:
            if withRunning:
                if exclusiveRunning:
                    if withZombi:
                        if exclusiveZombi:
                            return session.query(JobInfo).filter(JobInfo.state.in_(JobStates.getRunningStates())).filter(JobInfo.user == None).all()
                        else:
                            return session.query(JobInfo).filter(JobInfo.state.in_(JobStates.getRunningStates())).all()
                    else:
                        return session.query(JobInfo).filter(JobInfo.state.in_(JobStates.getRunningStates())).filter(JobInfo.user != None).all()
                else:
                    if withZombi:
                        if exclusiveZombi:
                            return session.query(JobInfo).filter(JobInfo.user == None).all()
                        else:
                            return session.query(JobInfo).all()
                    else:
                        return session.query(JobInfo).filter(JobInfo.user != None).all()
            else:
                if withZombi:
                    if exclusiveZombi:
                        return session.query(JobInfo).filter(JobInfo.state.in_(JobStates.getFinalStates())).filter(JobInfo.user == None).all()
                    else:
                        return session.query(JobInfo).filter(JobInfo.state.in_(JobStates.getFinalStates())).all()
                else:
                    return session.query(JobInfo).filter(JobInfo.state.in_(JobStates.getFinalStates())).filter(JobInfo.user != None).all()
        except (NoResultFound, MultipleResultsFound):
            return None
    
    @staticmethod
    def cleanUpJobDbViaUser(user, userName = None):
        """
        Delete old Jobs in Db via userName
        """
        session = dissomniag.Session()
        if userName != None:
            try:
                otherUser = session.query(dissomniag.auth.User).filter(dissomniag.auth.User.username == str(userName)).one()
            except (NoResultFound, MultipleResultsFound):
                otherUser = None
        else:
            otherUser = None
            
        try:
            if user.isAdmin and userName != None and otherUser != None:
                jobs = session.query(JobInfo).filter(JobInfo.user == otherUser).filter(JobInfo.state.in_(JobStates.getFinalStates())).all()
            elif userName == None:
                jobs = session.query(JobInfo).filter(JobInfo.user == user).filter(JobInfo.state.in_(JobStates.getFinalStates())).all()
            else:
                return False
        except NoResultFound:
            return False
        
        for job in jobs:
            session.delete(job)
        session.commit()
        return True
   
    @staticmethod
    def cleanUpJobDbViaId(user, jobId):
        """
        Delete single Job in Db via jobId
        """
        session = dissomniag.Session()
        
        jobId = int(jobId)

        try:
            if user.isAdmin:
                job = session.query(JobInfo).filter(JobInfo.id == jobId).filter(JobInfo.state.in_(JobStates.getFinalStates())).one()
            else:
                job = session.query(JobInfo).filter(JobInfo.user == user).filter(JobInfo.state.in_(JobStates.getFinalStates())).filter(JobInfo.id == jobId).one()
        except (NoResultFound, MultipleResultsFound):
            return False
        
        session.delete(job)
        session.commit()
        return True
    
    @staticmethod
    def cleanUpJobDbViaZombi(user):
        """
        Delete all Zombi Jobs
        """
        session = dissomniag.Session()
        if not user.isAdmin:
            return False
        
        try:
            jobs = session.query(JobInfo).filter(JobInfo.user == None).all()
        except NoResultFound:
            return False
        
        for job in jobs:
            session.delete(job)
            
        session.commit()
        return True
   
    @staticmethod
    def cleanUpJobDb(user):
        """
        Delete Jobs in Db
        If user == adminUser all Final State jobs are deleted
        """
        session = dissomniag.Session()
        try:
            if user.isAdmin:
                jobs = session.query(JobInfo).filter(JobInfo.state.in_(JobStates.getFinalStates())).all()
            else:
                jobs = session.query(JobInfo).filter(JobInfo.state.in_(JobStates.getFinalStates())).filter(JobInfo.user == user).all()
        except NoResultFound:
            return False
        
        for job in jobs:
            session.delete(job)
        session.commit()
        return True
        
    
    
        
        
        
