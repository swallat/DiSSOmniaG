# -*- coding: utf-8 -*-
'''
Created on 16.11.2011

@author: Sebastian Wallat
'''
import os
import git
import subprocess
import shlex
import dissomniag
import logging
import threading, thread
from dissomniag.utils.wrapper import synchronized

log = logging.getLogger("GitEnvironment")

GitEnvironmentLock = threading.RLock()


class GitEnvironment(object):
    '''
    classdocs
    '''
    isAdminUsable = False
    isRepoFolderUsable = False
    lock = threading.RLock()
    
        
    def __new__(cls, *args, **kwargs):
        # Store instance on cls._instance_dict with cls hash
        key = str(hash(cls))
        if not hasattr(cls, '_instance_dict'):
            cls._instance_dict = {}
        if key not in cls._instance_dict:
            cls._instance_dict[key] = \
                super(GitEnvironment, cls).__new__(cls, *args, **kwargs)
        return cls._instance_dict[key]

    def __init__(self):
        pass
        
    def createCheckJob(self):
        context = dissomniag.taskManager.Context()
        user = dissomniag.getIdentity().getAdministrativeUser()
        job = dissomniag.taskManager.Job(context, "Make initial check git environment", user = user)
        job.addTask(dissomniag.tasks.CheckGitEnvironment())
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user, self, job)
        return True
    
    @synchronized(GitEnvironmentLock)
    def _checkAdmin(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
        #1. Check if Utility Folder exists
        job.trace("Start _checkAdmin in GitEnvironment")
        try:
            if not os.access(dissomniag.config.git.pathToLocalUtilFolder, os.F_OK):
                job.trace("No %s Folder. Try to create it." % dissomniag.config.git.pathToLocalUtilFolder)
                try:
                    dissomniag.getRoot()
                    os.makedirs(dissomniag.config.git.pathToLocalUtilFolder)
                    os.chown(dissomniag.config.git.pathToLocalUtilFolder,
                             dissomniag.config.dissomniag.userId,
                             dissomniag.config.dissomniag.groupId)
                except OSError, e:
                    job.trace("Could not create utility folder. %s" % e)
                    log.info("Could not create utility folder. %s" % e)
                    self.isAdminUsable = False
                    return
                finally:
                    dissomniag.resetPermissions()
                
                if self._makeInitialCheckout(job):
                    self.isAdminUsable = True
                else:
                    self.isAdminUsable = False
            else:
                self.pull(job)
                
        except Exception as e:
            job.trace("GENERAL ERROR %s" % e)
            log.info("GENERAL ERROR %s" % e)
            return      
        
    @synchronized(GitEnvironmentLock)            
    def _makeInitialCheckout(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
        
        gitosisPath = os.path.join(dissomniag.config.git.pathToGitRepositories, "gitosis-admin.git")
        job.trace("GitosisPath %s" % gitosisPath)
        try:
            origRepo = git.Repo(gitosisPath)
            origRepo.clone(dissomniag.config.git.pathToLocalUtilFolder)
        except Exception as e:
            job.trace(str(e))
            return False
        else:
            return True
        
        cmd = shlex.split("git clone %s %s" %(gitosisPath, dissomniag.config.git.pathToLocalUtilFolder))
        proc = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        job.multiLog(str(proc.communicate()))
        returnCode = proc.returncode
        if returnCode == 0:
            return True
        else:
            return False
        
    @synchronized(GitEnvironmentLock)
    def _checkRepoFolder(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
        try:
            if not os.access(dissomniag.config.git.pathToGitRepositories, os.W_OK):
                self.isRepoFolderUsable = False
            else:
                self.isRepoFolderUsable = True
        except Exception as e:
            job.trace("GENERAL ERROR %s" % e)
            log.info("GENERAL ERROR %s" % e)
            self.isRepoFolderUsable = False
            return
        
    @synchronized(GitEnvironmentLock)
    def prepare(self):
        pass
    
    @synchronized(GitEnvironmentLock)
    def isUpTodate(self):
        pass
    
    @synchronized(GitEnvironmentLock)
    def getNewConfig(self):
        pass
    
    @synchronized(GitEnvironmentLock)
    def getConfigAndHash(self):
        pass
    
    @synchronized(GitEnvironmentLock)
    def getUserApps(self, user):
        """
        Get all sections in config where user is used
        """
        pass
    
    @synchronized(GitEnvironmentLock)
    def commit(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
    
    @synchronized(GitEnvironmentLock)
    def addKeyToKeyDir(self, job, pubKeyString):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
    
    @synchronized(GitEnvironmentLock)
    def updateConfig(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
    
    @synchronized(GitEnvironmentLock)
    def pull(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
        repo = git.Repo(dissomniag.config.git.pathToLocalUtilFolder)
        assert repo.bare == False
        if repo.is_dirty():
            self.commit(job)
        origin = repo.remotes.origin
        origin.pull()
        return
    
    @synchronized(GitEnvironmentLock)
    def push(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject() 