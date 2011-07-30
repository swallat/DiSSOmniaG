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
            name = Dispatcher.startName + " " + name
            """
            To identify a Thread as a Dispatcher Thread
            """
            threading.Thread.__init__(self, group = group, target = target,
                                      name = name, verbose = verbose)
            self._ready = True
            self.args = args,
            self.kwargs = kwargs
            self.condition = threading.Condition()
            self.jobList = []
            self.state = dispatcherStates.RUNNING
            self.inputQueue = Queue.Queue()
            self.jobsArrived = False
            self.jobsFinished = False
    
    def run(self):
        """ Start the Dispatche Run while """
        log.info("Dispatcher started")
        while self.state == dispatcherStates.RUNNING:
            
            self.waitForEvent()
            """ Wait for any condition to occure """
            
            if self.state == dispatcherStates.CANCELLED:
                """ 
                A cancel request Arrived 
                
                :caution: 
                    Make sure that the current state does not change in
                    self._handleCancel() 
                        
                """
                log.debug("Cancel request arrived")
                self._handleCancel()
                continue
            
            if self.jobsArrived:
                """ 
                Some requests to handle a new Job arrived 
                
                :caution: More than one Job could be arrived
                
                """
                log.debug("New Job arrived in Dispatcher")
                self.jobsArrived = False
                self._handleJobsArrived()
                
            if self.jobsFinished:
                """
                Some Jobs finished Work.
                
                :caution: More than one Job could have finished.
                
                """
                log.debug("Jobs have finished")
                self.jobsFinished = False
                self._handleJobsFinished()
        
        #End while
        log.info("Dispatcher cleaned up")
    
    def _handleCancel(self):
        """ Handle self.state == dispatcherStates.CANCELLED """
        with self.condition:
            
            self._cancelRunningJobs()
            
            """
            Clean up Input Queue
            """
            queueCleanedUp = False
            while not queueCleanedUp:
                try:
                    job = self.inputQueue.get_nowait()
                except Queue.Empty:
                    queueCleanedUp = True
                    continue
                
                job.cancel()
                
            
        
    def _handleJobsArrived(self):
        with self.condition:
            while not self.inputQueue.empty():
                pass 
        
    def _handleJobsFinished(self):
        with self.condition:
            pass
        
    def _defStartJobInNewWorker(self, job):
        with self.condition:
            pass
    
    def _waitForEvent(self):
        with self.condition:
            pass
        
    def _cancelRunningJobs(self):
        with self.condition:
            pass
        
    def _clearInputQueue(self):
        with self.condition:
            pass
    
    def addJob(self, job):
        with self.condition:
            pass

    def addJobsConcurrent(self, jobs = []):
        with self.condition:
            pass
    
    def cancelJob(self, jobId):
        with self.condition:
            pass
    
    def cancelAll(self):
        with self.condition:
            pass
    
    def jobFinished(self, jobId):
        with self.condition:
            pass
        
    @utils.synchronized(staticLock)
    @staticmethod
    def startDispatcher():
        """ Start the Dispatcher and return the Dispatcher object """
        d = Dispatcher(name = "Disspatcher")
        d.start()
        return d
    
    
    
    
    
    
