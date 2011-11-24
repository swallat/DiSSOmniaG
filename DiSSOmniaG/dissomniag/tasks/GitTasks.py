# -*- coding: utf-8 -*-
'''
Created on 17.11.2011

@author: Sebastian Wallat
'''

import dissomniag
import logging

log = logging.getLogger("tasks.GitTasks")
    
class GitPushAdminRepo(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        try:
            dissomniag.GitEnvironment().update(self.job)
        except Exception as e:
            self.multiLog("GitPushAdminRepo %s" % str(e), log)
            return dissomniag.taskManager.TaskFailed("GitPushAdminRepo %s" % str(e))
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class CheckGitEnvironment(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        try:
            env = dissomniag.GitEnvironment()
            self.multiLog("Entering GitEnvironment()._checkAdmin", log)
            env._checkAdmin(self.job)
            self.multiLog("Entering GitEnvironment()._checkRepoFolder", log)
            env._checkRepoFolder(self.job)
        except Exception as e:
            self.multiLog(str(e), log)
            
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS