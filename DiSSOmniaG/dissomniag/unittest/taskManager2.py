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
        super(Test, cls).tearDownClass()
        dissomniag.taskManager.Dispatcher.cleanUpDispatcher()
        global context
        context = None


    def test1Single(self):
        log.info("Single Multitask")
        
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
        
        dissomniag.taskManager.Dispatcher.addJob(user = None, job = job1)
        dissomniag.taskManager.Dispatcher.addJob(user = None, job = job2)
        
        time.sleep(3)
        print(job1.getInfo())
        print(job2.getInfo())
        global counter, counterLock
        assert counter == 1
        with counterLock:
            counter = 0
        
           
    def test2SingleCancelSecond(self):
        log.info("Single Multitask Cancel Second")
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
        
        job2Id = job2.getId()
        dissomniag.taskManager.Dispatcher.addJob(user = None, job = job1)
        dissomniag.taskManager.Dispatcher.addJob(user = None, job = job2)
        dissomniag.taskManager.Dispatcher.cancelJob(user = None, jobId = job2Id)
        time.sleep(3)
        print(job1.getInfo())
        print(job2.getInfo())
        global counter, counterLock
        assert counter == 4
        with counterLock:
            counter = 0
        
        
    def test3CancelRunningTask(self):
        global counter, counterLock
        with counterLock:
            counter = 0
        context = taskManager.Context()
        context.runMethod = "add"
        context.runValue = 1
        context.revertMethod = "sub"
        context.revertValue = 2
        log.info("Cancel Running Task")
        job1 = taskManager.Job(context = context, description = "Job 3")
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(longRunningTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        
        job1Id = job1.getId()
        dissomniag.taskManager.Dispatcher.addJob(user = None, job = job1)
        time.sleep(1)
        dissomniag.taskManager.Dispatcher.cancelJob(user = None, jobId = job1Id)
        time.sleep(5)
        print(job1.getInfo())
        
        print ("#### COUNTER %d ####" % counter)
        if dissomniag.config.dispatcher.revertBeforeCancel:
            assert counter == -3
        else:
            assert counter == 3
        with counterLock:
            counter = 0

    def test4AddConcurrent(self):
        context = taskManager.Context()
        context.runMethod = "add"
        context.runValue = 1
        context.revertMethod = "sub"
        context.revertValue = 2
        context.concurrentRunMethod = "sub"
        context.concurrentRunValue = 1
        context.concurrentRevertMethod = "add"
        context.concurrentRevertValue = 2
        
        
        job1 = taskManager.Job(context = context, description = "Job A")
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        
        job2 = taskManager.Job(context = context, description = "Job B")
        job2.addTask(concurrentTask())
        job2.addTask(concurrentTask())
        job2.addTask(concurrentTask())
        job2.addTask(concurrentTask())
        job2.addTask(concurrentTask())
        jobs = [job1, job2]
        taskManager.Dispatcher.addJobsConcurrent(user = None, jobs = jobs)
        time.sleep(5)
        print(job1.getInfo())
        print(job2.getInfo())
        global counter, counterLock
        print ("#### COUNTER %d ####" % counter)
        assert counter == 0
        with counterLock:
            counter = 0
    
    def test5CancelConcurrentTask(self):
        context = taskManager.Context()
        context.runMethod = "add"
        context.runValue = 1
        context.revertMethod = "sub"
        context.revertValue = 2
        context.concurrentRunMethod = "sub"
        context.concurrentRunValue = 1
        context.concurrentRevertMethod = "add"
        context.concurrentRevertValue = 2
        
        
        job1 = taskManager.Job(context = context, description = "Job A")
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        
        job2 = taskManager.Job(context = context, description = "Job B")
        job2.addTask(concurrentTask())
        job2.addTask(concurrentTask())
        job2.addTask(concurrentTask())
        job2.addTask(concurrentTask())
        job2.addTask(concurrentTask())
        jobs = [job1, job2]
        jobBId = job2.getId()
        taskManager.Dispatcher.addJobsConcurrent(user = None, jobs = jobs)
        taskManager.Dispatcher.cancelJob(user = None, jobId = jobBId)
        time.sleep(5)
        print(job1.getInfo())
        print(job2.getInfo())
        global counter, counterLock
        print ("#### COUNTER %d ####" % counter)
        assert counter == 5
        with counterLock:
            counter = 0
            
    def test6CancelConcurrentTaskRunning(self):
        context = taskManager.Context()
        context.runMethod = "add"
        context.runValue = 1
        context.revertMethod = "sub"
        context.revertValue = 2
        context.concurrentRunMethod = "sub"
        context.concurrentRunValue = 1
        context.concurrentRevertMethod = "add"
        context.concurrentRevertValue = 2
        
        
        job1 = taskManager.Job(context = context, description = "Job A")
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        
        job2 = taskManager.Job(context = context, description = "Job B")
        job2.addTask(concurrentTask())
        job2.addTask(concurrentTask())
        job2.addTask(longRunningConcurrentTask())
        job2.addTask(concurrentTask())
        job2.addTask(concurrentTask())
        jobs = [job1, job2]
        jobBId = job2.getId()
        taskManager.Dispatcher.addJobsConcurrent(user = None, jobs = jobs)
        time.sleep(1)
        taskManager.Dispatcher.cancelJob(user = None, jobId = jobBId)
        time.sleep(5)
        print(job1.getInfo())
        print(job2.getInfo())
        global counter, counterLock
        print ("#### COUNTER %d ####" % counter)
        if dissomniag.config.dispatcher.revertBeforeCancel:
            assert counter == 8
        else:
            assert counter == 2
        with counterLock:
            counter = 0
            
    def test7GetJob(self):
        context = taskManager.Context()
        context.runMethod = "add"
        context.runValue = 1
        context.revertMethod = "sub"
        context.revertValue = 2
        context.concurrentRunMethod = "sub"
        context.concurrentRunValue = 1
        context.concurrentRevertMethod = "add"
        context.concurrentRevertValue = 2
        
        
        job1 = taskManager.Job(context = context, description = "Job A")
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        
        job2 = taskManager.Job(context = context, description = "Job B")
        job2.addTask(concurrentTask())
        job2.addTask(concurrentTask())
        job2.addTask(longRunningConcurrentTask())
        job2.addTask(concurrentTask())
        job2.addTask(concurrentTask())
        jobBId = job2.getId()
        taskManager.Dispatcher.addJob(user = None, job = job1)
        taskManager.Dispatcher.addJob(user = None, job = job2)
        time.sleep(1)
        taskMJobB = taskManager.Dispatcher.getJob(user = None, jobId = jobBId)
        print(job2.getInfo())
        print(taskMJobB.getInfo())
        assert job2 == taskMJobB
        time.sleep(5)
        taskMJobB = taskManager.Dispatcher.getJob(user = None, jobId = jobBId)
        print(job2.getInfo())
        print(taskMJobB.getInfo())
        assert job2 == taskMJobB
        print(job1.getInfo())
        print(job2.getInfo())
        global counter, counterLock
        print ("#### COUNTER %d ####" % counter)
        with counterLock:
            counter = 0
            
            
    def test8CancelledAll(self):
        context = taskManager.Context()
        context.runMethod = "add"
        context.runValue = 1
        context.revertMethod = "sub"
        context.revertValue = 2
        context.concurrentRunMethod = "sub"
        context.concurrentRunValue = 1
        context.concurrentRevertMethod = "add"
        context.concurrentRevertValue = 2
        
        
        job1 = taskManager.Job(context = context, description = "Job A")
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        job1.addTask(counterTask())
        
        job2 = taskManager.Job(context = context, description = "Job B")
        job2.addTask(concurrentTask())
        job2.addTask(concurrentTask())
        job2.addTask(longRunningConcurrentTask())
        job2.addTask(concurrentTask())
        job2.addTask(concurrentTask())
        taskManager.Dispatcher.addJob(user = None, job = job1)
        taskManager.Dispatcher.addJob(user = None, job = job2)
        time.sleep(1)
        taskManager.Dispatcher.cleanUpDispatcher()
        time.sleep(5)
        print(job1.getInfo())
        print(job2.getInfo())
        global counter, counterLock
        print ("#### COUNTER %d ####" % counter)
        assert counter > 0
        with counterLock:
            counter = 0

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
