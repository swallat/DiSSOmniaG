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
            
        try:
            appLiveCdRel.deleteAppOnRemote(self.job.getUser())
        except Exception as e:
            self.multiLog("DeleteAppOnLiveCdRemote: Generall Exception %s" % str(e), log)
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
                
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
    
class addAllAppsOnRemote(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "liveCd") or  type(self.context.liveCd) != dissomniag.model.LiveCd:
            self.job.trace("addAppOnRemote: In Context missing liveCd object. REVERT")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing liveCd object. REVERT")
        
        self.multiLog("Adding all apps on Remote %s" % (self.context.liveCd.vm.commonName), log)
        
        try:
            ret = self.context.liveCd.addAllCurrentAppsOnRemote(self.job.getUser())
        except dissomniag.NoMaintainanceIp:
            self.multiLog("Add app on Remote. No Maintainance IP resolvable.", log)
            raise dissomniag.taskManager.TaskFailed("Add app on Remote. No Maintainance IP resolvable.")
        except Exception as e:
            self.multiLog("GENERAL EXCEPTION while adding all apps on Remote %s" % (self.context.liveCd.vm.commonName), log)
            raise dissomniag.taskManager.TaskFailed("GENERAL EXCEPTION while adding apps.")
        if ret != 0:
            self.multiLog("Remote error while adding all apps on Remote %s" % (self.context.liveCd.vm.commonName), log)
            raise dissomniag.taskManager.TaskFailed("Remote error while adding apps.")
        
        self.multiLog("Adding all apps on Remote %s SUCCEDED" % (self.context.liveCd.vm.commonName), log)
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
        
        
    
class addAppOnRemote(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "app") or  type(self.context.app) != dissomniag.model.App:
            self.job.trace("addAppOnRemote: In Context missing app object. REVERT")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing app object. REVERT")
        
        if not hasattr(self.context, "liveCd") or  type(self.context.liveCd) != dissomniag.model.LiveCd:
            self.job.trace("addAppOnRemote: In Context missing liveCd object. REVERT")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing liveCd object. REVERT")
        
        session = dissomniag.Session()
        try:
            appLiveCdRel = session.query(dissomniag.model.AppLiveCdRelation).filter(dissomniag.model.AppLiveCdRelation.app == self.context.app).filter(dissomniag.model.AppLiveCdRelation.liveCd == self.context.liveCd).one()
        except NoResultFound:
            self.job.trace("addAppOnRemote: No Relation object found. REVERT")
            raise dissomniag.taskManager.UnrevertableFailure("No Relation object found. REVERT")
        except MultipleResultsFound:
            appLiveCdRel = appLiveCdRel[0]
            
            
        self.multiLog("Adding app %s on Remote %s" % (self.context.app.name, self.context.liveCd.vm.commonName), log)
        
        try:
            ret = appLiveCdRel.addAppOnRemote(self.job.getUser())
        except dissomniag.NoMaintainanceIp:
            self.multiLog("Add app on Remote. No Maintainance IP resolvable.", log)
            raise dissomniag.taskManager.TaskFailed("Add app on Remote. No Maintainance IP resolvable.")
        except Exception as e:
            self.multiLog("GENERAL EXCEPTION while adding app %s on Remote %s" % (self.context.app.name, self.context.liveCd.vm.commonName), log)
            raise dissomniag.taskManager.TaskFailed("GENERAL EXCEPTION while adding app.")
        if ret != 0:
            self.multiLog("Remote error while adding app %s on Remote %s" % (self.context.app.name, self.context.liveCd.vm.commonName), log)
            raise dissomniag.taskManager.TaskFailed("Remote error while adding app.")
        
        self.multiLog("Adding app %s on Remote %s SUCCEDED" % (self.context.app.name, self.context.liveCd.vm.commonName), log)
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    

class operateOnApp(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "app") or  type(self.context.app) != dissomniag.model.App:
            self.job.trace("operateOnApp: In Context missing app object. REVERT")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing app object. REVERT")
        
        if not hasattr(self.context, "liveCd") or  type(self.context.liveCd) != dissomniag.model.LiveCd:
            self.job.trace("operateOnApp: In Context missing liveCd object. REVERT")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing liveCd object. REVERT")
        
        session = dissomniag.Session()
        try:
            appLiveCdRel = session.query(dissomniag.model.AppLiveCdRelation).filter(dissomniag.model.AppLiveCdRelation.app == self.context.app).filter(dissomniag.model.AppLiveCdRelation.liveCd == self.context.liveCd).one()
        except NoResultFound:
            self.job.trace("operateOnApp: No Relation object found. REVERT")
            raise dissomniag.taskManager.UnrevertableFailure("No Relation object found. REVERT")
        except MultipleResultsFound:
            appLiveCdRel = appLiveCdRel[0]
            
            
        if not hasattr(self.context, "action") or not dissomniag.model.AppActions.isValid(self.context.action):
            self.job.trace("Operate on app: In Context missing action.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing action.")
        
        
        self.multiLog("Starting Action %s over App %s on Remote %s" % (dissomniag.model.AppActions.getName(self.context.action), self.context.app.name, self.context.liveCd.vm.commonName), log)
        
        scriptName = None
        if hasattr(self.context, "scriptName"):
            scriptName = self.context.scriptName
        
        tagOrCommit = None
        if hasattr(self.context, "tagOrCommit"):
            tagOrCommit = self.context.tagOrCommit
        try:
            result = appLiveCdRel.operateOnRemote(self.job.getUser, self.context.action, scriptName = scriptName, tagOrCommit = tagOrCommit, job = self.job)
        except dissomniag.InvalidAction as e:
            self.multiLog("No valid action provided by operateOnApp. %s" % str(e), log)
            return dissomniag.taskManager.TaskFailed("No valid action provided by operateOnApp.")
        except dissomniag.NoMaintainanceIp as e:
            self.multiLog("NoMaintainanceIp resolvable %s" % str(e), log)
            return dissomniag.taskManager.TaskFailed("NoMaintainanceIp resolvable .")
        except Exception as e:
            self.multiLog("Execute exception %s" % str(e), log)
            return dissomniag.taskManager.TaskFailed("Execute exception %s" % str(e))
        else:
            if result == True:
                self.multiLog("Action succeded %s over App %s on Remote %s" % (dissomniag.model.AppActions.getName(self.context.action), self.context.app.name, self.context.liveCd.vm.commonName), log)
                return dissomniag.taskManager.TaskReturns.SUCCESS
            else:
                self.multiLog("Action FAILED %s over App %s on Remote %s" % (dissomniag.model.AppActions.getName(self.context.action), self.context.app.name, self.context.liveCd.vm.commonName), log)
                return dissomniag.taskManager.TaskFailed("Action FAILED %s over App %s on Remote %s" % (dissomniag.model.AppActions.getName(self.context.action), self.context.app.name, self.context.liveCd.vm.commonName))

    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
        pass