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

log = logging.getLogger("dissomniag.unittest.__taskManager1")


context1 = "HALLO"

counter = 0

context = None
revertStandard = False
revert = False
notrevert = False
failingButGoAhead = False

revertFailing = False
revertUnrevertable = False
revertFailingButGoAhead = False

dissomniag.initMigrate.init()
dissomniag.taskManager.Dispatcher.startDispatcher()
context = None

class testTask1(taskManager.AtomicTask):
    
        def run(self):
            global context, counter
            counter += 1
            assert self.context == context1
            context = self.context
            log.debug("Context: %s" % self.context)
            print "################## IN RUN STANDARD ##############"
            return True
        
        def revert(self):
            global counter
            counter -= 1
            global context, revertStandard
            revertStandard = True
            assert self.context == context1
            context = self.context
            log.debug("Context: %s" % self.context)
            print "########### IN REVERT STANDARD ##################"
            return False
        
class testTask2Failing(taskManager.AtomicTask):
    
        def run(self):
            global counter
            counter += 1
            self.job.trace("Run Failing")
            print "################## IN RUN FAILED ##############"
            raise dissomniag.taskManager.TaskFailed()
        
        def revert(self):
            global counter
            counter -= 1
            self.job.trace("Revert Failing")
            print "########### IN REVERT FAILED ##################"
            global revert
            revert = True
            return True
        
class testTask3FailingUnrevertable(taskManager.AtomicTask):
    
        def run(self):
            global counter
            counter += 1
            self.job.trace("TEST TRACE")
            global notrevert
            notrevert = True
            print "################## IN RUN UNREVERTABLE ##############"
            raise dissomniag.taskManager.UnrevertableFailure()
        
        def revert(self):
            global counter
            counter -= 1
            print "########### IN REVERT UNREVERTABLE ##################"
            return True
        
class testTask4FailingButGoAhead(taskManager.AtomicTask):
    
    def run(self):
        global counter
        counter += 1
        self.job.trace("TEST TRACE")
        global failingButGoAhead
        failingButGoAhead = True
        print "################## IN RUN FAILING BUT GO AHEAD##############"
        return False
    
    def revert(self):
            global counter
            counter -= 1
            print "################## IN RUN FAILING BUT GO AHEAD##############"
            global failingButGoAhead
            failingButGoAhead = False
            return True
        

class testTask5RevertFailing(taskManager.AtomicTask):
    
    def run(self):
        global counter
        counter += 1
        self.job.trace("TEST TRACE")
        print "################## IN RUN REVERT FAILING ##############"
        return True
    
    def revert(self):
        global counter
        counter -= 1
        global revertFailing
        revertFailing = True
        print "################## IN REVERT REVERT FAILLING ##############"
        raise dissomniag.taskManager.TaskFailed()
    
class testTask6RevertUnrevertableFailling(taskManager.AtomicTask):
    
    def run(self):
        global counter
        counter += 1
        self.job.trace("TEST TRACE")
        print "################## IN RUN REVERT Unrevertable ##############"
        return True
    
    def revert(self):
        
        global revertUnrevertable
        revertUnrevertable = True
        
        global counter
        counter -= 1
        
        print "################## IN REVERT REVERT Unrevertable ##############"
        raise dissomniag.taskManager.UnrevertableFailure()
        
class testTask7RevertFaillingButGoAhead(taskManager.AtomicTask):
    
    def run(self):
        global counter
        counter += 1
        self.job.trace("TEST TRACE")
        print "################## IN RUN REVERT FAILING BUT GO AHEAD ##############"
        return True
    
    def revert(self):
        global counter, revertFailingButGoAhead
        counter -= 1
        revertFailingButGoAhead = True
        print "################## IN REVERT REVERT FAILING BUT GO AHEAD ##############"
        return False
    
class counterTask(taskManager.AtomicTask):
    
    def run(self):
        print dir(self.context)
        self.context.counter += 1
        return True
    
    def revert(self):
        self.context.counter -= 1
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
    #===========================================================================
    #    
    # 
    # def testCreateJobAndTask(self):
    #    job = taskManager.Job(context = context1, description = "First Test Job")
    #    job.addTask(testTask1())
    #    dissomniag.taskManager.Dispatcher.addJob(user = None, job = job)
    #    time.sleep(3)
    #    global context
    #    print("Context1: %s" % context1)
    #    if context != None:
    #        print("Context: %s" % context)
    #    else:
    #        print("Context is None")
    #    assert context == context1
    #    context = None
    #    infoObj = job.getInfo()
    #    print(infoObj)
    #   
    # def testTaskFailed(self):
    #    log.debug("Started testTaskFailed")
    #    print "Current Thread Id in TestMethod: %s" % threading.current_thread().name
    #    job2 = taskManager.Job(context = context1, description = "Second Test Job")
    #    job2.addTask(testTask2Failing())
    #    dissomniag.taskManager.Dispatcher.addJob(user = None, job = job2)
    #    time.sleep(3)
    #    global revert
    #    assert revert == True
    #    revert = False
    #    infoObj = job2.getInfo()
    #    print(infoObj)
    #   
    # def testTaskUnrevertableFaild(self):
    #    log.debug("Started testTaskUnrevertableFailed")
    #    print "Current Thread Id in TestMethod: %s" % threading.current_thread().name
    #    job3 = taskManager.Job(context = context1, description = "Third Test Job")
    #    job3.addTask(testTask3FailingUnrevertable())
    #    dissomniag.taskManager.Dispatcher.addJob(user = None, job = job3)
    #    time.sleep(3)
    #    global notrevert
    #    assert notrevert == True
    #    notrevert = False
    #    infoObj = job3.getInfo()
    #    print(infoObj)
    #   
    # def testTaskFaillingButGoAhead(self):
    #    log.debug("Started testTaskRevertingFailing")
    #    print "Current Thread Id in TestMethod: %s" % threading.current_thread().name
    #    job4 = taskManager.Job(context = context1, description = "4 Test Job")
    #    job4.addTask(testTask4FailingButGoAhead())
    #    dissomniag.taskManager.Dispatcher.addJob(user = None, job = job4)
    #    time.sleep(4)
    #    global failingButGoAhead
    #    assert failingButGoAhead == True
    #    failingButGoAhead = False
    #    infoObj = job4.getInfo()
    #    print(infoObj)
    #   
    # def testTaskRevertFailing(self):
    #    log.debug("Started testTaskRevertingFailing")
    #    print "Current Thread Id in TestMethod: %s" % threading.current_thread().name
    #    job5 = taskManager.Job(context = context1, description = "5 Test Job")
    #    job5.addTask(testTask5RevertFailing())
    #    job5.addTask(testTask2Failing())
    #    dissomniag.taskManager.Dispatcher.addJob(user = None, job = job5)
    #    time.sleep(4)
    #    global revertFailing, revert
    #    assert revertFailing == True
    #    assert revert == True
    #    revertFailing = False
    #    revert = False
    #    infoObj = job5.getInfo()
    #    print(infoObj)
    #   
    # def testTaskRevertUnrevertbale(self):
    #    log.debug("Started testTaskRevertUnrevertable")
    #    print "Current Thread Id in TestMethod: %s" % threading.current_thread().name
    #    job6 = taskManager.Job(context = context1, description = "6 Test Job")
    #    job6.addTask(testTask1())
    #    job6.addTask(testTask6RevertUnrevertableFailling())
    #    job6.addTask(testTask2Failing())
    #    dissomniag.taskManager.Dispatcher.addJob(user = None, job = job6)
    #    time.sleep(4)
    #    global revertUnrevertable, revert, revertStandard
    #    assert revertUnrevertable == True
    #    assert revert == True
    #    assert revertStandard == False
    #    revertUnrevertable = False
    #    revert = False
    #    revertStandard = False
    #    infoObj = job6.getInfo()
    #    print(infoObj)
    #   
    # def testTaskRevertFaillingButGoAhead(self):
    #    log.debug("Started testTaskRevertFailingButGoAhead")
    #    print "Current Thread Id in TestMethod: %s" % threading.current_thread().name
    #    job7 = taskManager.Job(context = context1, description = "7 Test Job")
    #    job7.addTask(testTask1())
    #    job7.addTask(testTask7RevertFaillingButGoAhead())
    #    job7.addTask(testTask2Failing())
    #    dissomniag.taskManager.Dispatcher.addJob(user = None, job = job7)
    #    time.sleep(2)
    #    global revertFailingButGoAhead, revert, revertStandard, context
    #    assert revertFailingButGoAhead == True
    #    assert revert == True
    #    assert revertStandard == True
    #    revertFailingButGoAhead = False
    #    revert = False
    #    revertStandard = False
    #    context = None
    #    infoObj = job7.getInfo()
    #    print(infoObj)
    #===========================================================================
       
    def testMultiTask(self):
        log.debug("TestingMultitask")
        context = taskManager.Context()
        context.counter = 0
        job8 = taskManager.Job(context = context, description = "8 Test Job")
        job8.addTask(counterTask())
        job8.addTask(counterTask())
        job8.addTask(counterTask())
        dissomniag.taskManager.Dispatcher.addJob(user = None, job = job8)
        time.sleep(4)
        assert context.counter == 3
        print(job8.getInfo())
        
    def testMultiTask2(self):
        log.debug("TestingMultitask")
        mContext = taskManager.Context()
        mContext.counter = 0
        job9 = taskManager.Job(context = mContext, description = "9 Test Job")
        job9.addTask(counterTask())
        job9.addTask(counterTask())
        job9.addTask(counterTask())
        job9.addTask(testTask2Failing())
        dissomniag.taskManager.Dispatcher.addJob(user = None, job = job9)
        time.sleep(4)
        assert mContext.counter == 0
        global counter, revert, context
        assert revert == True
        counter = 0
        context = None
        revert = False
        print(job9.getInfo())
        
    def testAddMultiDispatcher(self):
        log.debug("TestingMultitask")
        mContext = taskManager.Context()
        mContext.counter = 0
        job9 = taskManager.Job(context = mContext, description = "9 Test Job")
        job9.addTask(counterTask())
        job9.addTask(counterTask())
        job9.addTask(counterTask())
        job9.addTask(testTask2Failing())
        dissomniag.taskManager.Dispatcher.addJob(user = None, job = job9)
        time.sleep(4)
        assert mContext.counter == 0
        global counter, revert, context
        assert revert == True
        counter = 0
        context = None
        revert = False
        print(job9.getInfo())
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testCreateTask']
    unittest.main()
