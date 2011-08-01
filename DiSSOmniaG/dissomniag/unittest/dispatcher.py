# -*- coding: utf-8 -*-
"""
Created on 01.08.2011

@author: Sebastian Wallat
"""
import unittest
import time
import logging
import dissomniag
import dissomniag.taskManager as taskManager
import dissomniag.utils.Logging
import dissomniag.dbAccess
import threading

log = logging.getLogger("dissomniag.__init__")


context1 = "HALLO"

context = None

revert = False
notrevert = False
failingButGoAhead = False

dissomniag.initMigrate.init()
dissomniag.taskManager.Dispatcher.startDispatcher()
context = None

class testTask1(taskManager.AtomicTask):
    
        def run(self):
            global context
            assert self.context == context1
            context = self.context
            log.debug("Context: %s" % self.context)
            print "################## IN RUN STANDARD ##############"
            time.sleep(1)
            return True
        
        def revert(self):
            global context
            assert self.context == context1
            context = self.context
            log.debug("Context: %s" % self.context)
            print "########### IN REVERT STANDARD ##################"
            time.sleep(1)
            return False
        
class testTask2Failing(taskManager.AtomicTask):
    
        def run(self):
            self.job.trace("TEST TRACE")
            print "################## IN RUN FAILED ##############"
            raise dissomniag.taskManager.TaskFailed()
        
        def revert(self):
            print "########### IN REVERT FAILED ##################"
            global revert
            revert = True
            return True
        
class testTask3FailingUnrevertable(taskManager.AtomicTask):
    
        def run(self):
            self.job.trace("TEST TRACE")
            global notrevert
            notrevert = True
            print "################## IN RUN UNREVERTABLE ##############"
            raise dissomniag.taskManager.UnrevertableFailure()
        
        def revert(self):
            print "########### IN REVERT UNREVERTABLE ##################"
            return True
        
class testTask4FailingButGoAhead(taskManager.AtomicTask):
    
    def run(self):
        self.job.trace("TEST TRACE")
        global failingButGoAhead
        failingButGoAhead = True
        print "################## IN RUN FAILING BUT GO AHEAD##############"
        return False
    
    def revert(self):
            print "################## IN RUN FAILING BUT GO AHEAD##############"
            global failingButGoAhead
            failingButGoAhead = False
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
        dissomniag.taskManager.Dispatcher.cancelAll()
        global context
        context = None     
        
    
    def testCreateJobAndTask(self):
        job = taskManager.Job(context = context1, description = "First Test Job")
        job.addTask(testTask1())
        dissomniag.taskManager.Dispatcher.addJob(user = None, job = job)
        time.sleep(2)
        global context
        print("Context1: %s" % context1)
        if context != None:
            print("Context: %s" % context)
        else:
            print("Context is None")
        assert context == context1
        context = None
        infoObj = job.getInfo()
        print(infoObj)
        
    def testTaskFailed(self):
        log.debug("Started testTaskFailed")
        print "Current Thread Id in TestMethod: %s" % threading.current_thread().name
        job2 = taskManager.Job(context = context1, description = "Second Test Job")
        job2.addTask(testTask2Failing())
        dissomniag.taskManager.Dispatcher.addJob(user = None, job = job2)
        time.sleep(2)
        global revert
        assert revert == True
        revert = False
        infoObj = job2.getInfo()
        print(infoObj)
        
    def testTaskUnrevertableFaild(self):
        log.debug("Started testTaskUnrevertableFailed")
        print "Current Thread Id in TestMethod: %s" % threading.current_thread().name
        job3 = taskManager.Job(context = context1, description = "Third Test Job")
        job3.addTask(testTask3FailingUnrevertable())
        dissomniag.taskManager.Dispatcher.addJob(user = None, job = job3)
        time.sleep(2)
        global notrevert
        assert notrevert == True
        notrevert = False
        infoObj = job3.getInfo()
        print(infoObj)
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testCreateTask']
    unittest.main()
