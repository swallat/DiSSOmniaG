'''
Created on 24.10.2011

@author: Sebastian Wallat
'''
import unittest


import unittest
import time
import logging
import dissomniag
import dissomniag.taskManager as taskManager
import dissomniag.utils.Logging
import dissomniag.dbAccess
import threading

log = logging.getLogger("dissomniag.unittest.__taskManager2")

counterLock = threading.RLock()
counter = 0

class counterTask(taskManager.AtomicTask):
    
    def run(self):
        global counter, counterLock
        with counterLock:
            if self.context.runMethod == "add":
                counter += self.context.runValue
            elif self.context.runMethod == "sub":
                counter -= self.context.runValue
            
            self.job.trace("Set counter to %d" % counter)
        return True 
    
    def revert(self):
        global counter, counterLock
        with counterLock:
            if self.context.revertMethod == "add":
                counter += self.context.revertValue
            elif self.context.revertMethod == "sub":
                counter -= self.context.revertValue
            self.job.trace("Set counter to %d" % counter)
        return True
    
class initRevertTask(taskManager.AtomicTask):
    
    def run(self):
        global counter, counterLock
        with counterLock:
            if self.context.runMethod == "add":
                counter += self.context.runValue
            elif self.context.runMethod == "sub":
                counter -= self.context.runValue
                self.job.trace("Set counter to %d" % counter)
        raise taskManager.TaskFailed()
    
    def revert(self):
        global counter, counterLock
        with counterLock:
            if self.context.revertMethod == "add":
                counter += self.context.revertValue
            elif self.context.revertMethod == "sub":
                counter -= self.context.revertValue
            self.job.trace("Set counter to %d" % counter)
        return True
    
class longRunningTask(taskManager.AtomicTask):
    
    def run(self):
        self.job.trace("### IN LONG RUNNING TASK RUN ###")
        time.sleep(3)
        global counter, counterLock
        with counterLock:
            if self.context.runMethod == "add":
                counter += self.context.runValue
            elif self.context.runMethod == "sub":
                counter -= self.context.runValue
        return True
    
    def revert(self):
        self.job.trace("### IN LONG RUNNING TASK REVERT ###")
        global counter, counterLock
        with counterLock:
            if self.context.revertMethod == "add":
                counter += self.context.revertValue
            elif self.context.revertMethod == "sub":
                counter -= self.context.revertValue
        return True
    
class concurrentTask(taskManager.AtomicTask):
    
    def run(self):
        self.job.trace("### IN CONCURRENT TASK RUN ###")
        global counter, counterLock
        with counterLock:
            if self.context.concurrentRunMethod == "add":
                counter += self.context.concurrentRunValue
            elif self.context.concurrentRunMethod == "sub":
                counter -= self.context.concurrentRunValue
            self.job.trace("Set counter to %d" % counter)
        return True
    
    def revert(self):
        self.job.trace("### IN CONCURRENT TASK REVERT ###")
        global counter, counterLock
        with counterLock:
            if self.context.concurrentRevertMethod == "add":
                counter += self.context.concurrentRevertValue
            elif self.context.concurrentRevertMethod == "sub":
                counter -= self.context.concurrentRevertValue
            self.job.trace("Set counter to %d" % counter)
        return True
        
class longRunningConcurrentTask(taskManager.AtomicTask):
    
    def run(self):
        self.job.trace("### IN CONCURRENT TASK RUN ###")
        global counter, counterLock
        with counterLock:
            if self.context.concurrentRunMethod == "add":
                counter += self.context.concurrentRunValue
            elif self.context.concurrentRunMethod == "sub":
                counter -= self.context.concurrentRunValue
            self.job.trace("Set counter to %d" % counter)
        time.sleep(2)
        return True
    
    def revert(self):
        self.job.trace("### IN CONCURRENT TASK REVERT ###")
        global counter, counterLock
        with counterLock:
            if self.context.concurrentRevertMethod == "add":
                counter += self.context.concurrentRevertValue
            elif self.context.concurrentRevertMethod == "sub":
                counter -= self.context.concurrentRevertValue
            self.job.trace("Set counter to %d" % counter)
        time.sleep(2)
        return True

class synchronizator(object):
    def __init(self):
        pass

class Test(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        dissomniag.initMigrate.init()
        dissomniag.taskManager.Dispatcher.startDispatcher()
        global context
        context = None     
        
    @classmethod
    def tearDownClass(cls):
        log.info("Starting Tear Down")
        super(Test, cls).tearDownClass()
        dissomniag.taskManager.Dispatcher.cleanUpDispatcher()
        global context
        context = None

    def test1Synchronized(self):
        sync = synchronizator()
        
        
        context = taskManager.Context()
        context.runMethod = "add"
        context.runValue = 1
        context.revertMethod = "sub"
        context.revertValue = 2
        job1 = taskManager.Job(context = context, description = "Job 1")
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        
        job2 = taskManager.Job(context = context, description = "Job 2")
        job2.addTask(counterTask())
        job2.addTask(counterTask())
        job2.addTask(initRevertTask())
        
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user = None, syncObj=sync, job = job1)
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user = None, syncObj=sync, job = job2)
        time.sleep(3)
        job1.getInfo()
        job2.getInfo()
        
        global counter, counterLock
        print "#### Counter: %d ####" % counter
        assert counter == 1
        with counterLock:
            counter = 0
            
    def test2CancelSyncRunningObj(self):
        sync = synchronizator()
        
        
        context = taskManager.Context()
        context.runMethod = "add"
        context.runValue = 1
        context.revertMethod = "sub"
        context.revertValue = 2
        job1 = taskManager.Job(context = context, description = "Job 1")
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(longRunningTask())
        
        job2 = taskManager.Job(context = context, description = "Job 2")
        job2.addTask(counterTask())
        job2.addTask(counterTask())
        job2.addTask(counterTask())
        job2.addTask(initRevertTask())
        
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user = None, syncObj=sync, job = job1)
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user = None, syncObj=sync, job = job2)
        time.sleep(1)
        dissomniag.taskManager.Dispatcher.cancelJob(user = None, jobId=job1.id)
        time.sleep(3)
        job1.getInfo()
        job2.getInfo()
        
        global counter, counterLock
        print "#### Counter: %d ####" % counter
        assert counter == 0
        with counterLock:
            counter = 0
    
    def test3CancelSyncQueuedJob(self):
        sync = synchronizator()
        
        
        context = taskManager.Context()
        context.runMethod = "add"
        context.runValue = 1
        context.revertMethod = "sub"
        context.revertValue = 2
        job1 = taskManager.Job(context = context, description = "Job 1")
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(longRunningTask())
        
        job2 = taskManager.Job(context = context, description = "Job 2")
        job2.addTask(counterTask())
        job2.addTask(counterTask())
        job2.addTask(counterTask())
        job2.addTask(initRevertTask())
        
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user = None, syncObj=sync, job = job1)
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user = None, syncObj=sync, job = job2)
        time.sleep(1)
        dissomniag.taskManager.Dispatcher.cancelJob(user = None, jobId=job2.id)
        time.sleep(3)
        job1.getInfo()
        job2.getInfo()
        
        global counter, counterLock
        print "#### Counter: %d ####" % counter
        assert counter == 4
        with counterLock:
            counter = 0
            
        #time.sleep(100)
    
    def test4GetSyncJobFromDispatcher(self):
        sync = synchronizator()
        
        
        context = taskManager.Context()
        context.runMethod = "add"
        context.runValue = 1
        context.revertMethod = "sub"
        context.revertValue = 2
        job1 = taskManager.Job(context = context, description = "Job 1")
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(longRunningTask())
        
        job2 = taskManager.Job(context = context, description = "Job 2")
        job2.addTask(counterTask())
        job2.addTask(counterTask())
        job2.addTask(counterTask())
        job2.addTask(initRevertTask())
        
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user = None, syncObj=sync, job = job1)
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user = None, syncObj=sync, job = job2)
        job1.getInfo()
        job2.getInfo()
        
        global counter, counterLock
        print "#### Counter: %d ####" % counter
        assert job2 == dissomniag.taskManager.Dispatcher.getJob(user = None, jobId = job2.id)
        assert job1 == dissomniag.taskManager.Dispatcher.getJob(user = None, jobId = job1.id)
        
        #time.sleep(10)
        with counterLock:
            counter = 0
        
    
    def test4PreemptDispatcher(self):
        sync = synchronizator()
        
        
        context = taskManager.Context()
        context.runMethod = "add"
        context.runValue = 1
        context.revertMethod = "sub"
        context.revertValue = 2
        job1 = taskManager.Job(context = context, description = "Job 1")
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(longRunningTask())
        
        job2 = taskManager.Job(context = context, description = "Job 2")
        job2.addTask(counterTask())
        job2.addTask(counterTask())
        job2.addTask(counterTask())
        job2.addTask(initRevertTask())
        
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user = None, syncObj=sync, job = job1)
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user = None, syncObj=sync, job = job2)
        
        #dissomniag.taskManager.Dispatcher.cleanUpDispatcher()
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()