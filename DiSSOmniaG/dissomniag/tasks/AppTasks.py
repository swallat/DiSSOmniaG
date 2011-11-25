# -*- coding: utf-8 -*-
'''
Created on 17.11.2011

@author: Sebastian Wallat
'''
import os
import shutil
import git
import dissomniag
import logging
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

log = logging.getLogger("tasks.AppTasks")

class DeleteAppFinally(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "app") or  type(self.context.app) != dissomniag.model.App:
            self.job.trace("DeleteAppFinally: In Context missing app object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing app object.")
        
        if self.context.app.AppLiveCdRelations != []:
            self.multiLog("Cannot delete an app with LiveCd Relations!", log)
            raise dissomniag.taskManager.TaskFailed("Cannot delete an app with LiveCd Relations!")
        
        self.deleted = True
        pathToRepository = os.path.join(dissomniag.config.git.pathToGitRepositories, ("%s.git") % self.context.app.name)
        try:
            dissomniag.getRoot()
            shutil.rmtree(pathToRepository)
        except Exception as e:
            self.multiLog("Cannot delete local Repository %s %s" % (str(e), pathToRepository), log)
        finally:
            dissomniag.resetPermissions()
            
        session = dissomniag.Session()
        session.delete(self.context.app)
        dissomniag.saveCommit(session)
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
            
        
    def revert(self):
        if hasattr(self, "deleted") and self.deleted == True:
            return dissomniag.taskManager.UnrevertableFailure("Cannot undelete App")
        
        return dissomniag.taskManager.TaskReturns.SUCCESS

class DeleteAppLiveCdRelation(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "app") or  type(self.context.app) != dissomniag.model.App:
            self.job.trace("DeleteAppLiveCdRelation: In Context missing app object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing app object.")
        
        if not hasattr(self.context, "liveCd") or  type(self.context.liveCd) != dissomniag.model.LiveCd:
            self.job.trace("DeleteAppLiveCdRelation: In Context missing liveCd object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing liveCd object.")
        
        session = dissomniag.Session()
        try:
            appLiveCdRel = session.query(dissomniag.model.AppLiveCdRelation).filter(dissomniag.model.AppLiveCdRelation.app == self.context.app).filter(dissomniag.model.AppLiveCdRelation.liveCd == self.context.liveCd).one()
        except NoResultFound:
            self.job.trace("DeleteAppLiveCdRelation: No Relation object found.")
            raise dissomniag.taskManager.UnrevertableFailure("No Relation object found.")
        except MultipleResultsFound:
            appLiveCdRel = appLiveCdRel[0]
            
        
        pathToRepository = os.path.join(dissomniag.config.git.pathToGitRepositories, ("%s.git") % appLiveCdRel.app.name)
        branchName = self.context.liveCd.vm.commonName
        
        try:
            dissomniag.getRoot()
            repo = git.Repo(pathToRepository)
            if branchName in repo.heads:
                #repo.delete_head(branchName)
                repo.git.branch("-D", branchName)
        except Exception as e:
            self.multiLog("Cannot delete branch in Revert %s" % str(e), log)
            raise dissomniag.taskManager.TaskFailed("Cannot delete branch in Revert %s" % str(e))
        finally:
            dissomniag.resetPermissions()
        
        self.deleted = True
        session = dissomniag.Session()
        session.delete(appLiveCdRel)
        dissomniag.saveCommit(session)
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        if hasattr(self, "deleted") and self.deleted == True:
            return dissomniag.taskManager.UnrevertableFailure("Cannot undelete Relation")
        
        if not hasattr(self.context, "app") or  type(self.context.app) != dissomniag.model.App:
            self.job.trace("DeleteAppLiveCdRelation: In Context missing app object. REVERT")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing app object. REVERT")
        
        if not hasattr(self.context, "liveCd") or  type(self.context.liveCd) != dissomniag.model.LiveCd:
            self.job.trace("DeleteAppLiveCdRelation: In Context missing liveCd object. REVERT")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing liveCd object. REVERT")
        
        session = dissomniag.Session()
        try:
            appLiveCdRel = session.query(dissomniag.model.AppLiveCdRelation).filter(dissomniag.model.AppLiveCdRelation.app == self.context.app).filter(dissomniag.model.AppLiveCdRelation.liveCd  == self.context.liveCd).one()
        except NoResultFound:
            self.job.trace("DeleteAppLiveCdRelation: No Relation object found. REVERT")
            raise dissomniag.taskManager.UnrevertableFailure("No Relation object found. REVERT")
        except MultipleResultsFound:
            appLiveCdRel = appLiveCdRel[0]
        
        pathToRepository = os.path.join(dissomniag.config.git.pathToGitRepositories, ("%s.git") % appLiveCdRel.app.name)
        branchName = self.context.liveCd.vm.commonName
        
        try:
            dissomniag.getRoot()
            repo = git.Repo(pathToRepository)
            if not branchName in repo.heads:
                repo.create_head(branchName)
        except Exception as e:
            self.multiLog("Cannot create branch %s" % str(e), log)
            raise dissomniag.taskManager.TaskFailed("Cannot create branch %s" % str(e))
        finally:
            dissomniag.resetPermissions()
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
        
    
class DeleteAppOnLiveCdRemote(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "app") or  type(self.context.app) != dissomniag.model.App:
            self.job.trace("DeleteAppLiveCdRelation: In Context missing app object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing app object.")
        
        if not hasattr(self.context, "liveCd") or  type(self.context.liveCd) != dissomniag.model.LiveCd:
            self.job.trace("DeleteAppLiveCdRelation: In Context missing liveCd object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing liveCd object.")
        
        session = dissomniag.Session()
        try:
            appLiveCdRel = session.query(dissomniag.model.AppLiveCdRelation).filter(dissomniag.model.AppLiveCdRelation.app == self.context.app).filter(dissomniag.model.AppLiveCdRelation.liveCd == self.context.liveCd).one()
        except NoResultFound:
            self.job.trace("DeleteAppLiveCdRelation: No Relation object found.")
            raise dissomniag.taskManager.UnrevertableFailure("No Relation object found.")
        except MultipleResultsFound:
            appLiveCdRel = appLiveCdRel[0]
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
        
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
        
class AddAppBranch(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "app") or  type(self.context.app) != dissomniag.model.App:
            self.job.trace("AddAppBranch: In Context missing app object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing app object.")
        
        if not hasattr(self.context, "liveCd") or  type(self.context.liveCd) != dissomniag.model.LiveCd:
            self.job.trace("AddAppBranch: In Context missing liveCd object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing liveCd object.")
        
        session = dissomniag.Session()
        try:
            appLiveCdRel = session.query(dissomniag.model.AppLiveCdRelation).filter(dissomniag.model.AppLiveCdRelation.app == self.context.app).filter(dissomniag.model.AppLiveCdRelation.liveCd == self.context.liveCd).one()
        except NoResultFound:
            self.job.trace("AddAppBranch: No Relation object found.")
            raise dissomniag.taskManager.UnrevertableFailure("No Relation object found.")
        except MultipleResultsFound:
            appLiveCdRel = appLiveCdRel[0]
        
        pathToRepository = os.path.join(dissomniag.config.git.pathToGitRepositories, ("%s.git") % appLiveCdRel.app.name)
        branchName = self.context.liveCd.vm.commonName
        
        try:
            dissomniag.getRoot()
            repo = git.Repo(pathToRepository)
            if not branchName in repo.heads:
                repo.create_head(branchName)
        except Exception as e:
            self.multiLog("Cannot create branch %s" % str(e), log)
            raise dissomniag.taskManager.TaskFailed("Cannot create branch %s" % str(e))
        finally:
            dissomniag.resetPermissions()
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        if not hasattr(self.context, "app") or  type(self.context.app) != dissomniag.model.App:
            self.job.trace("AddAppBranch: In Context missing app object. REVERT")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing app object. REVERT")
        
        if not hasattr(self.context, "liveCd") or  type(self.context.liveCd) != dissomniag.model.LiveCd:
            self.job.trace("AddAppBranch: In Context missing liveCd object. REVERT")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing liveCd object. REVERT")
        
        session = dissomniag.Session()
        try:
            appLiveCdRel = session.query(dissomniag.model.AppLiveCdRelation).filter(dissomniag.model.AppLiveCdRelation.app == self.context.app).filter(dissomniag.model.AppLiveCdRelation.liveCd == self.context.liveCd).one()
        except NoResultFound:
            self.job.trace("AddAppBranch: No Relation object found. REVERT")
            raise dissomniag.taskManager.UnrevertableFailure("No Relation object found. REVERT")
        except MultipleResultsFound:
            appLiveCdRel = appLiveCdRel[0]
        
        pathToRepository = os.path.join(dissomniag.config.git.pathToGitRepositories, ("%s.git") % appLiveCdRel.app.name)
        branchName = self.context.liveCd.vm.commonName
        
        try:
            dissomniag.getRoot()
            repo = git.Repo(pathToRepository)
            if branchName in repo.heads:
                #repo.delete_head(branchName)
                repo.git.branch("-D", branchName)
        except Exception as e:
            self.multiLog("Cannot delete branch in Revert %s" % str(e), log)
            raise dissomniag.taskManager.TaskFailed("Cannot delete branch in Revert %s" % str(e))
        finally:
            dissomniag.resetPermissions()
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
            
            
class MakeInitialCommit(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "app") or  type(self.context.app) != dissomniag.model.App:
            self.job.trace("MakeInitialCommit: In Context missing app object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing app object.")
        self.multiLog("Starting Make Initial Commit", log)
        
        try:
            dissomniag.GitEnvironment().makeInitialCommit(self.context.app, self.job)
        except Exception as e:
            self.multiLog(str(e), log)
            raise dissomniag.taskManager.TaskFailed("Could not make initialCommit.")
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS