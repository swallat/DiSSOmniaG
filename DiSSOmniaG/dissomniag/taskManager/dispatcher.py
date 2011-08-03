# -*- coding: utf-8 -*-
"""
Created on 27.07.2011

@author: Sebastian Wallat
"""
import threading
import Queue
import logging

import dissomniag.utils as utils

log = logging.getLogger("dissomniag.taskManager.dispatcher")#


class dispatcherStates:
    RUNNING = "running"
    CANCELLED = "cancelled"

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
            self.cancelCondition = threading.Condition()
    
    def run(self):
        """ Start the Dispatche Run while """
        log.info("Dispatcher started")
        while self.state == dispatcherStates.RUNNING or self.state == dispatcherStates.CANCELLED:
            with self.condition:
                self.condition.wait()
                """ Wait for any condition to occure """
                log.info("POINT State %s" % ("Running" if self.state == dispatcherStates.RUNNING else "Cancelled"))
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
            Cancel all running Jobs
            """
            log.debug("Cancelling all Running Jobs")
            for job in self.runningJobDict:
                job.cancel()
            
            for job in self.independentJobList:
                job.cancel()
            
            """
            Wait until all Jobs have finished correctly.
            Must be outside of a Lock!!
            """
            listBefore = self.finishedJobList
            while not self._compareJobLists() and self.independentJobList != []:
                with self.condition:
                    self.condition.wait(timeout = 10000)
                    """
                    The Timeout makes sure, that the Program exits.
                    """
                    if listBefore == self.finishedJobList: 
                        break
        
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
    
    def _handleJobsFinished(self):
        with self.condition:
            if self._compareJobLists():
                log.info("All Jobs in Concurrent List completed")
                self._startUpNewJobs()
            else:
                return
            
    def _handleJobsCancelRequest(self):
        with self.condition:
            
            for id in self.jobIdsToCancel:
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
                
            return None
        
    def _cancelQueuedJob(self, id):
        with self.condition:
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
        
    
    
    
    
    
