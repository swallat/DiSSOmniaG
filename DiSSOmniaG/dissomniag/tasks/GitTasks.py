# -*- coding: utf-8 -*-
'''
Created on 17.11.2011

@author: Sebastian Wallat
'''

import dissomniag
import logging

log = logging.getLogger("tasks.GitTasks")


class DeleteAppLiveCdRelationInGit(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        ### DELETE BRANCH ###
        if not hasattr(self.context, "appLiveCdRel") or type(self.context.appLiveCdRel) != dissomniag.model.AppLiveCdRelation:
            self.job.trace("DeleteAppLiveCdRelationInGit: In Context missing appLiveCdRel object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing appLiveCdRel object.")
        
    
    def revert(self):
        pass
    
class DeleteAppRepository(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        
        if not hasattr(self.context, "app") or type(self.context.app) != dissomniag.model.App:
            self.job.trace("DeleteAppRepository: In Context missing app object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing app object.")
    
    def revert(self):
        pass
    
class GitPushAdminRepo(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        pass
    
    def revert(self):
        pass
    
class CheckGitEnvironment(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        try:
            env = dissomniag.GitEnvironment()
            self.multiLog("Entering GitEnvironment()._checkAdmin", log)
            env._checkAdmin(self.job)
            self.multiLog("Entering GitEnvironment()._checkRepoFolder", log)
            env._checkRepoFolder(self.job)
        except Exception as e:
            self.multiLog(e, log)
            
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS