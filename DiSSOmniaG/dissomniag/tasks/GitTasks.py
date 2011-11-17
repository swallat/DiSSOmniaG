# -*- coding: utf-8 -*-
'''
Created on 17.11.2011

@author: Sebastian Wallat
'''

import dissomniag


class DeleteAppVMRelationInGit(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        ### DELETE BRANCH ###
        if not hasattr(self.context, "appVmRel") or type(self.context.appVmRel) != dissomniag.model.AppVmRelation:
            self.job.trace("DeleteAppVMRelationInGit: In Context missing appVmRel object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing appVmRel object.")
        
    
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