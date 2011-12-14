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
import threading
import Queue
import logging
import collections

import dissomniag.utils as utils

log = logging.getLogger("dissomniag.taskManager.dispatcher")#


class dispatcherStates:
    RUNNING = "running"
    CANCELLED = "cancelled"
    
class SynchronizedJobHelper(object):
    
    def __init__(self, syncObj, dispatcher):
        self.syncObj = syncObj
        self.jobQueue = Queue.Queue()
        self.jobRunning = None
        self.isRunning = False
        self.lock = threading.RLock()
        self.jobIds = []
        self.dispatcher = dispatcher
        self.cancelled = False
    
    def add(self, job):
        with self.lock:
            self.jobIds.append(job.id)
            self.jobQueue.put_nowait(job)
            
    def run(self):
        if not self.isRunning:
            return self.runNext()
        else:
            return True
    
    def runNext(self):
        with self.lock:
            try:
                self.jobRunning = self.jobQueue.get_nowait()
            except Queue.Empty:
                self.isRunning = False;
                self.jobRunning = None
                return False
            else:
                self.isRunning = True
                self.jobRunning.start(self.dispatcher)
                return True              
        
    def finishRunningJob(self):
        """
        Called when Job finished itself.
        """
        with self.lock:
            self.jobIds.remove(self.jobRunning.id)
            return True
    
    def isJobIn(self, jobId):
        with self.lock:
            if jobId in self.jobIds:
                return True
            else:
                return False
        
    def getJob(self, jobId):
        with self.lock:
            if self.isJobIn(jobId) != True:
                return None
            else:
                if self.jobRunning != None and self.jobRunning.id == jobId:
                    return self.jobRunning
                else:
                    tmpJobQueue = Queue.Queue()
                    returnJob = None
                    queueEmpty = False
                    while not queueEmpty:
                        try:
                            job = self.jobQueue.get_nowait()
                            if job.id == jobId:
                                returnJob = job
                            tmpJobQueue.put_nowait(job)
                        except Queue.Empty:
                            queueEmpty = True
                            break
                        
                    self.jobQueue = tmpJobQueue
                    return returnJob

    def cancelList(self):
        with self.lock:
            self.cancelled
            self.cancelRunningJob()
            queueEmpty = False
            while not queueEmpty:
                try:
                    job = self.jobQueue.get_nowait()
                    job.cancelBeforeStartup()
                    self.jobIds.remove(job.id)
                except Queue.Empty:
                    queueEmpty = True
                    break
    
    def cancelRunningJob(self):
        with self.lock:
            if self.isRunning and self.jobRunning != None:
                self.jobRunning.cancel()
    
    def cancelQueuedJob(self, jobId):
        with self.lock:
            if self.isJobIn(jobId) != True:
                return False
            else:
                tmpJobQueue = Queue.Queue()
                jobCancelled = False
                queueEmpty = False
                while not queueEmpty:
                    try:
                        job = self.jobQueue.get_nowait()
                        if job.id == jobId:
                            job.cancelBeforeStartup()
                            jobCancelled = True
                            self.jobIds.remove(jobId) # Remove Job From JobId
                        else:
                            tmpJobQueue.put_nowait(job)
                    except Queue.Empty:
                        queueEmpty = True
                    
                    self.jobQueue = tmpJobQueue
                return jobCancelled
                            
                        
            
        

class Dispatcher(threading.Thread):
    """
    classdocs
    """
    staticLock = threading.Lock()
    startName = "Dispatcher"
    isStarted = False
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """ 
        Override the __new__() Method, to get a singleton
        """
        if not cls._instance:
            cls._instance = super(Dispatcher, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, group = None, target = None, name = None,
                 args = (), kwargs = None, verbose = None):
        
        """
        Constructor
        """
        if not '_ready' in dir(self):
            # Der Konstruktor wird bei jeder Instanziierung aufgerufen.
            # Einmalige Dinge wie zum Beispiel die Initialisierung von Klassenvariablen müssen also in diesen Block.
            name = self.startName
            """
            To identify a Thread as a Dispatcher Thread
            """
            threading.Thread.__init__(self, group = group, target = target,
                                      name = name, verbose = verbose)
            self._ready = True
            self.args = args,
            self.kwargs = kwargs
            self.condition = threading.Condition()
            self.runningJobDict = []
            self.finishedJobList = []
            self.state = dispatcherStates.RUNNING
            self.inputQueue = Queue.Queue()
            self.independentQueue = Queue.Queue()
            self.independentJobList = []
            self.independentJobListLock = threading.RLock()
            self.jobsArrived = False
            self.independentJobArrived = False
            self.jobsFinished = False
            self.jobIdsToCancel = []
            self.synchronizedJobLists = {}
            self.arrivedSyncJobInfo = Queue.Queue()
            self.synchronizedJobsArrived = False
            self.syncRunNext = []
            self.cancelCondition = threading.Condition()
    
    def run(self):
        """ Start the Dispatche Run while """
        log.info("Dispatcher started")
        while self.state == dispatcherStates.RUNNING or self.state == dispatcherStates.CANCELLED:
            with self.condition:
                self.condition.wait()
                """ Wait for any condition to occure """
                log.info("State %s" % ("Running" if self.state == dispatcherStates.RUNNING else "Cancelled"))
                if self.state == dispatcherStates.CANCELLED:
                    """ 
                    A cancel request Arrived for the Dispatcher arrived 
                    
                    :caution: 
                    
                        Make sure that the current state does not change 
                        in self._handleCancel()
                            
                    """
                    log.debug("Cancel request arrived")
                    self._handleDispatcherCanceled()
                    break
                    
                if self.jobsFinished:
                    """
                    Some Jobs finished Work.
                    
                    :caution: 
                        
                        More than one Job could have finished.
                    
                    """
                    log.debug("Jobs have finished")
                    self.jobsFinished = False
                    self._handleJobsFinished()
                
                if self.jobIdsToCancel != []:
                    """
                    Some Jobs are requested to be canceled.
                    
                    :caution: 
                        
                        More than one Job could could be requested to be canceled.
                    """
                    log.debug("Cancel Job request")
                    self._handleJobsCancelRequest()
                    
                if self.jobsArrived:
                    """ 
                    Some requests to handle a new Job arrived 
                    
                    :caution: 
                        
                        More than one Job could be arrived
                    
                    """
                    log.debug("New Job arrived in Dispatcher")
                    self.jobsArrived = False
                    self._handleJobsArrived()
                
                if self.independentJobArrived:
                    """
                    Some independent Jobs arrived and can be handled
                    concurrently to the jobs in the standard input Queue.
                    
                    :caution:
                    
                        More than one Job could be arrived
                    """
                    log.debug("New independent job arrived in dispatcher.")
                    self.independentJobArrived = False
                    self._handleIndependentJobsArrived()
                    
                if self.synchronizedJobsArrived:
                    """
                    Some synchronized Jobs arrived and can be handled
                    concurrently to the jobs in the standard input Queue and the
                    independent Job Queue.
                    
                    :caution:
                    
                        More than one Job could be arrived
                    """
                    log.debug("New synchronized job arrived in dispatcher.")
                    self.synchronizedJobsArrived = False
                    self._handleSynchronizedJobsArrived()
        
        #End while
        log.info("Dispatcher cleaned up")
        with self.cancelCondition:
            self.cancelCondition.notifyAll()
        self._instance = None
    
    def _handleDispatcherCanceled(self):
        """ Handle self.state == dispatcherStates.CANCELLED """
        with self.condition:
            log.debug("Got Dispatcher Cancel Request")
            """
            Clean up Input Queue
            """
            log.debug("Cancelling all jobs in the queue.")
            queueCleanedUp = False
            while not queueCleanedUp:
                try:
                    for job in self.inputQueue.get_nowait():
                        job.cancelBeforeStartup()
                except Queue.Empty:
                    queueCleanedUp = True
                    break
            """
            Clean up independent Queue
            """
            independentQueueCleanedUp = False
            while not independentQueueCleanedUp:
                try:
                    job = self.independentQueue.get_nowait()
                    job.cancelBeforeStartup()
                except Queue.Empty:
                    independentQueueCleanedUp = True
                    break
                
            """
            Clean up synchronized Input Queue
            """
            syncQueueCleanedUp = False
            while not syncQueueCleanedUp:
                try:
                    obj = self.arrivedSyncJobInfo.get_nowait()
                    job = obj["job"]
                    job.cancelBeforeStartup()
                except Queue.Empty:
                    syncQueueCleanedUp = True
                    break
                except KeyError:
                    continue
            
            """
            Cancel all running Jobs
            """
            log.debug("Cancelling all Running Jobs")
            for job in self.runningJobDict:
                job.cancel()
            
            for job in self.independentJobList:
                job.cancel()
                
            for syncObj, info in self.synchronizedJobLists.items():
                info.cancelList()
            
        """
        Wait until all Jobs have finished correctly.
        Must be outside of a Lock!!
        """
        listBefore = self.finishedJobList
        while not self._compareJobLists() and self.independentJobList != [] and self._checkAllSyncListsStopped():
            with self.condition:
                self.condition.wait(timeout = 10000)
                """
                The Timeout makes sure, that the Program exits.
                """
                if listBefore == self.finishedJobList: 
                    break

    def _checkAllSyncListsStopped(self):
        with self.condition:
            for syncObj, info in self.synchronizedJobLists.items():
                if info.isRunning:
                    return False
            return True

    def _handleJobsArrived(self):
        with self.condition:
            if self._compareJobLists():
                self._startUpNewJobs()
            else:
                log.debug("Jobs arrived but not all Jobs finished yet")
                return                            
    
    def _handleIndependentJobsArrived(self):
        with self.condition:
            queueEmpty = False
            while not queueEmpty:
                try:
                    job = self.independentQueue.get_nowait()
                except Queue.Empty:
                    queueEmpty = True
                else:
                    with self.independentJobListLock:
                        if job not in self.independentJobList:
                            self.independentJobList.append(job)
                            job.start(self)
                            
    def _handleSynchronizedJobsArrived(self):
        with self.condition:
            queueEmpty = False
            while not queueEmpty:
                try:
                    info = self.arrivedSyncJobInfo.get_nowait()
                    syncObj = info["syncObj"]
                    job = info["job"]
                    try:
                        syncObjInfo = self.synchronizedJobLists[syncObj]
                        syncObjInfo.add(job)
                    except KeyError:
                        syncObjInfo = SynchronizedJobHelper(syncObj, self) # Add Dispatcher to call
                        syncObjInfo.add(job)
                        self.synchronizedJobLists[syncObj] = syncObjInfo
                    finally:
                        syncObjInfo.run()
                except Queue.Empty:
                    queueEmpty = True
                    break
                except KeyError:
                    continue
    
    def _handleJobsFinished(self):
        with self.condition:
            for info in self.syncRunNext:
                info.runNext()
            self.syncRunNext = []
            
            if self._compareJobLists():
                log.info("All Jobs in Concurrent List completed")
                self._startUpNewJobs()
            else:
                return
            
    def _handleJobsCancelRequest(self):
        with self.condition:
            
            for id in self.jobIdsToCancel:
                """
                If Job is a Running Synchronized Job
                """
                continueMe = False
                for syncObj, info in self.synchronizedJobLists.items():
                    if info.isJobIn(id) and info.jobRunning.id == id:
                        info.cancelRunningJob()
                        continueMe = True
                        break
                if continueMe:
                    continue
                
                """
                Else look general.
                """
                job = self._getJobRunning(id)
                if job != None:
                    job.cancel()
                    continue
                
                self._cancelQueuedJob(id)

            #Before returning clear JobIdsToCancel
            self.jobIdsToCancel = []
        
    def _getJobRunning(self, id):
        with self.condition:
            for job in self.runningJobDict:
                if job.getId() == id:
                    return job
            for job in self.independentJobList:
                if job.getId() == id:
                    return job
            for sync, info in self.synchronizedJobLists.items():
                if info.isJobIn(id):
                    returnJob = info.getJob(id)
                    if returnJob == info.jobRunning:
                        return returnJob    
            return None
        
    def _cancelQueuedJob(self, id):
        with self.condition:
            if self._cancelSynchronizedQueuedJob(id):
                return True
            
            replacementQueue = None
            queueEmpty = False
            found = False
            try:
                    elem = self.inputQueue.get_nowait()
                    found, replacement = self._getReplacement(elem, id)
                    if found and replacement == []:
                        return True
                    else:
                        replacementQueue = Queue.Queue()
                        replacementQueue.put_nowait(elem)
            except Queue.Empty:
                log.warning("Try to cancel a Job, but inputQueue is empty.")
                #return False
            while not queueEmpty:
                try:
                    elem = self.inputQueue.get_nowait()
                    if found:
                        replacementQueue.put_nowait(elem)
                    else:
                        found, replacement = self._getReplacement(elem, id)
                        if found and replacement == []:
                            continue
                        else:
                            replacementQueue.put_nowait(elem)
                except Queue.Empty:
                    queueEmpty = True
            self.inputQueue = replacementQueue
            
            if not found:
                replacementIndependentQueue = Queue.Queue()
                independentQueueEmpty = False
                while not independentQueueEmpty:
                    try:
                        job = self.independentQueue.get_nowait()
                        if job.getId() == id:
                            found = True
                            job.cancelBeforeStartup()
                        else:
                            replacementIndependentQueue.put_nowait(job)
                    except Queue.Empty:
                        independentQueueEmpty = True
                self.independentQueue = replacementIndependentQueue
            
            if found:
                return True
            else:
                return False
                    
    def _getReplacement(self, jobList, id):
        with self.condition:
            replacement = []
            found = False
            for job in jobList:
                if job.getId() == id:
                    job.cancelBeforeStartup()
                    found = True
                    continue
                replacement.append(job)
            return found, replacement
        
    def _cancelSynchronizedQueuedJob(self, id) :
        for syncObj, info in self.synchronizedJobLists.items():
            if info.isJobIn(id):
                info.cancelQueuedJob(id)
                return True
        return False
        
    def _startUpNewJobs(self):
        with self.condition:
            try:
                self.runningJobDict = self.inputQueue.get_nowait()
            except Queue.Empty, e:
                #log.warning("Dispatcher notified Jobs inserted. But there were no Jobs. Exception: %s" % str(e))
                return
            else:
                self.finishedJobList = []
                for job in self.runningJobDict:
                    job.start(self)
                    
    def _compareJobLists(self):
        """
        Compares the Job Lists, if all Jobs have finished.
        Return True if all Jobs completed.
               False if not all Jobs are completed jet.
        """
        with self.condition:
            for job in self.runningJobDict:
                if not job in self.finishedJobList:
                    return False
            return True
    
    def _addJob(self, job):
        with self.condition:
            assert job != None
            ticket = []
            ticket.append(job)
            self.inputQueue.put_nowait(ticket)
            self.jobsArrived = True
            log.debug("Job %d arrived in Dispatcher" % job.getId())
            self.condition.notifyAll()

    def _addJobsConcurrent(self, jobs = []):
        with self.condition:
            fullTicket = []
            for job in jobs:
                fullTicket.append(job)
            self.inputQueue.put_nowait(fullTicket)
            self.jobsArrived = True
            self.condition.notifyAll()
            
    def _addJobIndependent(self, job):
        with self.condition:
            assert job != None
            self.independentQueue.put_nowait(job)
            self.independentJobArrived = True
            log.debug("Independent Job arrived in Dispatcher %d" % job.getId())
            self.condition.notifyAll()
    
    def _addJobSynchronized(self, syncObj, job):
        with self.condition:
            assert job != None
            assert syncObj != None and isinstance(syncObj, collections.Hashable)
            syncObjInfo = {"syncObj":syncObj, "job":job}
            
            self.arrivedSyncJobInfo.put_nowait(syncObjInfo)
            self.synchronizedJobsArrived = True
            
            log.debug("Synchronized Job arrived in Dispatcher %d" % job.getId())
            self.condition.notifyAll()
    
    def _cancelJob(self, jobId):
        with self.condition:
            self.jobIdsToCancel.append(jobId)
            self.condition.notifyAll()
    
    def _cancelAll(self):
        log.info("In CancelAll")
        with self.condition:
            self.state = dispatcherStates.CANCELLED
            self.condition.notifyAll()
        with self.cancelCondition:  
            self.cancelCondition.wait()
        
    def _getJob(self, jobId):
        with self.condition:
            job = self._getJobRunning(jobId)
            if job != None:
                """
                Job is a running job
                """
                return job
            
            return self._getQueuedJob(jobId)
        
    def _getQueuedJob(self, jobId):
        replacementQueue = Queue.Queue()
        returnJob = None
        
        inputQueueEmpty = False
        while not inputQueueEmpty:
            try:
                jobs = self.inputQueue.get_nowait()
                for job in jobs:
                    if job.getId() == jobId:
                        returnJob = job
                replacementQueue.put_nowait(jobs)
            except Queue.Empty:
                inputQueueEmpty = True
        self.inputQueue = replacementQueue
        
        if returnJob == None:
            replacementIndependentQueue = Queue.Queue()
            independentQueueEmpty = False
            while not independentQueueEmpty:
                try:
                    job = self.independentQueue.get_nowait()
                    if job.getId() == jobId:
                        returnJob = job
                    replacementIndependentQueue.put_nowait(job)
                except Queue.Empty:
                    independentQueueEmpty = True
            self.independentQueue = replacementIndependentQueue
            
        if returnJob == None:
            #Get Job in Sync Job Lists
            for syncObj, info in self.synchronizedJobLists.items():
                if info.isJobIn(jobId):
                    returnJob = info.getJob(jobId)
            
        return returnJob      
    
    def jobFinished(self, job):
        with self.condition:
            if job in self.runningJobDict:
                self.finishedJobList.append(job)
                self.jobsFinished = True
                log.debug("Job %d finished in Dispatcher." % job.getId())
                self.condition.notifyAll()
            elif job in self.independentJobList:
                with self.independentJobListLock:
                    self.independentJobList.remove(job)
            else:
                found = False
                for syncObj, info in self.synchronizedJobLists.items():
                    if info.isJobIn(job.id):
                        info.finishRunningJob()
                        self.syncRunNext.append(info)
                        found = True
                if found:
                    self.jobsFinished = True
                    self.condition.notifyAll()

    @staticmethod
    def startDispatcher():
        with Dispatcher.staticLock:
            """ Start the Dispatcher and return the Dispatcher object """
            d = Dispatcher()
            if not d.isStarted:
                d.start()
                d.isStarted = True
            return d

    @staticmethod
    def addJob(user, job):
        with Dispatcher.staticLock:
            """
            For future use added. If we want more than one dispatcher
            the dispatching process must be controlled by a single instance.
            
            Use this method to add a job, if you want future consistency.
            """
            return Dispatcher()._addJob(job)

    @staticmethod
    def addJobsConcurrent(user, jobs = []):
        with Dispatcher.staticLock:
            """
            For future use added. If we want more than one dispatcher
            the dispatching process must be controlled by a single instance.
            
            Use this method to add a job, if you want future consistency.
            """
            return Dispatcher()._addJobsConcurrent(jobs)
    
    @staticmethod
    def addJobIndependent(user, job):
        with Dispatcher.staticLock:
            """
            For future use added. If we want more than one dispatcher
            the dispatching process must be controlled by a single instance.
            
            Use this method to add a job, if you want future consistency.
            """
            return Dispatcher()._addJobIndependent(job)
    
    @staticmethod
    def addJobSyncronized(user, syncObj, job):
        with Dispatcher.staticLock:
            """
            For future use added. If we want more than one dispatcher
            the dispatching process must be controlled by a single instance.
            
            Use this method to add a job, if you want future consistency.
            """
            return Dispatcher()._addJobSynchronized(syncObj, job)
    
    @staticmethod
    def cancelJob(user, jobId):
        with Dispatcher.staticLock:
            """
            For future use added. If we want more than one dispatcher
            the dispatching process must be controlled by a single instance.
            
            Use this method to add a job, if you want future consistency.
            """
            return Dispatcher()._cancelJob(jobId)

    @staticmethod
    def cleanUpDispatcher():
        with Dispatcher.staticLock:
            """
            For future use added. If we want more than one dispatcher
            the dispatching process must be controlled by a single instance.
            
            Use this method to add a job, if you want future consistency.
            """
            return Dispatcher()._cancelAll()

    @staticmethod
    def getJob(user, jobId):
        with Dispatcher.staticLock:
            """
            For future use added. If we want more than one dispatcher
            the dispatching process must be controlled by a single instance.
            
            Use this method to add a job, if you want future consistency.
            """
            return Dispatcher()._getJob(jobId)
        
    
    
    
    
    
