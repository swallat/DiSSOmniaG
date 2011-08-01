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
            self.jobsArrived = False
            self.jobsFinished = False
            self.jobIdsToCancel = []
    
    def run(self):
        """ Start the Dispatche Run while """
        log.info("Dispatcher started")
        while self.state == dispatcherStates.RUNNING:
            with self.condition:
                self.condition.wait()
                """ Wait for any condition to occure """
            
            if self.state == dispatcherStates.CANCELLED:
                """ 
                A cancel request Arrived for the Dispatcher arrived 
                
                :caution: 
                
                    Make sure that the current state does not change 
                    in self._handleCancel()
                        
                """
                log.debug("Cancel request arrived")
                self._handleDispatcherCanceled()
                continue
            
            if self.jobsArrived:
                """ 
                Some requests to handle a new Job arrived 
                
                :caution: 
                    
                    More than one Job could be arrived
                
                """
                log.debug("New Job arrived in Dispatcher")
                self.jobsArrived = False
                self._handleJobsArrived()
                
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
                
        
        #End while
        log.info("Dispatcher cleaned up")
    
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
                        job.cancel()
                except Queue.Empty:
                    queueCleanedUp = True
                    continue
                
            """
            Cancel all running Jobs
            """
            log.debug("Cancelling all Running Jobs")
            for job in self.runningJobDict:
                job.cancel()
            
        """
        Wait until all Jobs have finished correctly.
        Must be outside of a Lock!!
        """
        listBefore = self.finishedJobList
        while not self._compareJobLists():
            self.condition.wait(timeout = 10000)
            if listBefore == self.finishedJobList:
                """
                The Timeout makes sure, that the Programm exits.
                """
                break
        
                
            
        
    def _handleJobsArrived(self):
        with self.condition:
            if self._compareJobLists(self):
                self._startUpNewJobs()
            else:
                log.debug("Jobs arrived but not all Jobs finished yet")
                return                            
        
    def _handleJobsFinished(self):
        with self.condition:
            if self._compareJobLists():
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
                if job.id == id:
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
                log.WARRINING("Try to cancel a Job, but inputQueue is empty.")
                return False
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
            if found:
                return True
            else:
                return False
                    
    def _getReplacement(self, jobList, id):
        with self.condition:
            replacement = []
            found = False
            for job in jobList:
                if job.id == id:
                    job.cancel()
                    found = True
                    continue
                replacement.append(job)
            return found, replacement
    
        
    def _startUpNewJobs(self):
        with self.condition:
            try:
                self.runningJobDict = self.inputQueue.get_nowait()
            except Queue.Empty, e:
                log.WARNING("Dispatcher notified Jobs inserted. But there were no Jobs. Exception: %s" % str(e))
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
            self.condition.notifyAll()
            self.jobsArrived = True

    def _addJobsConcurrent(self, jobs = []):
        with self.condition:
            fullTicket = []
            for job in jobs:
                fullTicket.append(job)
            self.inputQueue.put_nowait(fullTicket)
            self.condition.notifyAll()
            self.jobsArrived = True
    
    def _cancelJob(self, jobId):
        with self.condition:
            self.jobIdsToCancel.append(jobId)
            self.condition.notifyAll()
    
    def _cancelAll(self):
        with self.condition:
            self.state = dispatcherStates.CANCELLED
            self.condition.notifyAll()
        
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
                    if job.id == jobId:
                        returnJob = job
                replacementQueue.put_nowait(jobs)
            except Queue.Empty:
                inputQueueEmpty = True
        
        return returnJob
            
            
    
    def jobFinished(self, job):
        with self.condition:
            self.finishedJobList.append(job)
            self.jobsFinished = True
            log.debug("Job %d finished in Dispatcher." % job.id)
            self.condition.notifyAll()
        

    @staticmethod
    def startDispatcher():
        with Dispatcher.staticLock:
            """ Start the Dispatcher and return the Dispatcher object """
            d = Dispatcher()
            d.start()
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
            return Dispatcher()._addJobConcurrent(jobs)
    
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
    def cancelAll():
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
        
    
    
    
    
    
