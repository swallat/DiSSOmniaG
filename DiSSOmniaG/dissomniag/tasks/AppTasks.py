# -*- coding: utf-8 -*-
'''
Created on 17.11.2011

@author: Sebastian Wallat
'''
import dissomniag

class DeleteAppFinally(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "app") or  type(self.context.app) != dissomniag.model.App:
            self.job.trace("DeleteAppFinally: In Context missing app object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing app object.")
        
    def revert(self):
        pass

class DeleteAppVMRelation(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "appVmRel") or  type(self.context.appVmRel) != dissomniag.model.AppVmRelation:
            self.job.trace("DeleteAppVMRelation: In Context missing appVmRel object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing appVmRel object.")
        
    
    def revert(self):
        pass
    
class DeleteAppOnVmRemote(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "appVmRel") or  type(self.context.appVmRel) != dissomniag.model.AppVmRelation:
            self.job.trace("DeleteAppOnRemote: In Context missing appVmRel object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing appVmRel object.")
        
    def revert(self):
        pass
    
class DeleteUserFromApp(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "app") or  type(self.context.app) != dissomniag.model.App:
            self.job.trace("DeleteAppOnRemote: In Context missing  object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing appVmRel object.")
        
        if not hasattr(self.context, "user") or  type(self.context.user) != dissomniag.auth.User:
            self.job.trace("DeleteAppOnRemote: In Context missing User object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing User object.")
        
        """
        DANGER:
        Check first if a key is used twice, and then and only then delete the key from the admin git repo.
        But always delete the designated user.
        """