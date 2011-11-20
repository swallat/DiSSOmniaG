# -*- coding: utf-8 -*-
'''
Created on 16.11.2011

@author: Sebastian Wallat
'''
import os
import git
import subprocess
import shlex
import ConfigParser
import time
import shutil
import re
import dissomniag
import logging
import threading, thread
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
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
    adminRepo = None
    
        
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
    
    def multiLog(self, msg, job):
        log.info(msg)
        job.trace(msg)
        
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
                self.multiLog("No %s Folder. Try to create it." % dissomniag.config.git.pathToLocalUtilFolder, job)
                try:
                    dissomniag.getRoot()
                    os.makedirs(dissomniag.config.git.pathToLocalUtilFolder)
                    os.chown(dissomniag.config.git.pathToLocalUtilFolder,
                             dissomniag.config.dissomniag.userId,
                             dissomniag.config.dissomniag.groupId)
                except OSError, e:
                    self.multiLog("Could not create utility folder. %s" % e, job)
                    self.isAdminUsable = False
                    return
                finally:
                    dissomniag.resetPermissions()
                
                if self._makeInitialCheckout(job):
                    self.isAdminUsable = True
                    try:
                        self.adminRepo = git.Repo(dissomniag.config.git.pathToLocalUtilFolder)
                        self.update(job)
                    except Exception as e:
                        self.multiLog(str(e), job)
                        self.isAdminUsable = False
                        return False
                else:
                    self.isAdminUsable = False
            else:
                try:
                    self.adminRepo = git.Repo(dissomniag.config.git.pathToLocalUtilFolder)
                except Exception as e:
                    self.multiLog(str(e), job)
                    self.isAdminUsable = False
                    return False
                self._pull(job)
                return True
                
        except Exception as e:
            self.multiLog("GENERAL ERROR %s" % e, job)
            return
        
    @synchronized(GitEnvironmentLock)
    def update(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
        
        if not self.isAdminUsable:
            return False
        self.multiLog("Entering git.update", job)
        #1. git pull
        self._pull(job)
        
        #2. getNewConfig
        config = self._getNewConfig(job)
        with open(dissomniag.config.git.pathToConfigFile, 'w') as f:
            config.write(f)
        index = self.adminRepo.index
        index.add(["gitosis.conf"])
        
        #3a) getUsedKeyList
        #3b) getHdKeyList
        #3c) addNewKeys
        self._addKeys(job, config)
        
        #3d) calc hdKeyList - usedKeyList
        #3e) delete not used keys (5.) on Hd
        self._deleteNotLongerUsedKeys(job, config)
        
        #5. commit repo
        self._commit(job)
        
        #6. push repo
        self._push(job)
        
    @synchronized(GitEnvironmentLock)            
    def _makeInitialCheckout(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
        self.multiLog("Entering git._makeInitialCheckout", job)
        gitosisAdminRepo = ("%s@%s:gitosis-admin.git" % (dissomniag.config.git.gitUser, dissomniag.config.git.gitosisHost))
        job.trace("GitosisAdminRepo %s" % gitosisAdminRepo)
        try:
            origRepo = git.Repo.clone_from(gitosisAdminRepo, dissomniag.config.git.pathToLocalUtilFolder)
        except Exception as e:
            job.trace(str(e))
            job.trace("Could not clone gitosis-admin Repository. Please add DiSSOmniag ssh_key file to the gitosis-admin group!")
            try:
                shutil.rmtree(dissomniag.config.git.pathToLocalUtilFolder)
            except Exception:
                pass
            return False
        else:
            return True
        
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
    def _getNewConfig(self, job):
        self.multiLog("Entering git._getNewConfig", job)
        session = dissomniag.Session()
        config = ConfigParser.SafeConfigParser()
        
        config.add_section("gitosis")
        config.add_section("group gitosis-admin")
        adminUser = dissomniag.getIdentity().getAdministrativeUser()
        keys = adminUser.publicKeys
        adminUserKeys = self._getMembersSet(keys)
        try:
            adminUsers = session.query(dissomniag.auth.User).filter(dissomniag.auth.User.isAdmin == True).all()
            for user in adminUsers:
                if user.publicKeys != None:
                    adminUserKeys = adminUserKeys.union(self._getMembersSet(user.publicKeys))
        except NoResultFound:
            pass
        
        
        config.set("group gitosis-admin", "members", " ".join(adminUserKeys))
        config.set("group gitosis-admin", "writable", "gitosis-admin")
        
        try:
            apps = session.query(dissomniag.model.App).all()
            
            for app in apps:
                repoName = app.name
                sectionName = "group %s" % repoName
                config.add_section(sectionName)
                config.add(sectionName, "writable", repoName)
                keys = adminUserKeys
                #Add user keys
                for user in app.users:
                    if user.publicKeys != None:
                        keys = keys.union(self._getMembersSet(user.publicKeys))
                        
                #Add Admin LiveCd Node Keys
                for relation in app.AppLiveCdRelations:
                    keys.add(str(relation.liveCd.vm.sshKey.getUserHostString()))
                
                config.add(sectionName, "members", " ".join(keys))
                        
        except NoResultFound as e:
            pass
        
        return config
    
    @synchronized(GitEnvironmentLock)
    def _getMembersSet(self, keys):
        keyIds = set()
        for key in keys:
            keyIds.add(str(key.getUserHostString()))
        return keyIds
    
    @synchronized(GitEnvironmentLock)
    def _getAppsFromConfig(self, job, config):
        apps = set()
        prog = re.compile("group (.*)")
        for section in config.sections():
            result = prog.match(section)
            if result:
                apps.add(str(result.group(1)))
                continue
        return apps
    
    @synchronized(GitEnvironmentLock)
    def _getKeysFromSection(self, job, config, sectionName):
        keys = set()
        try:
            my_keys = config.get(sectionName, 'members')
            my_keys = my_keys.split(" ")
            for mKey in my_keys:
                keys.add(str(mKey))
        except Exception:
            pass
        return keys
    
    @synchronized(GitEnvironmentLock)
    def _getConfigKeySet(self, job, config):
        """
        Get all keys used in config
        """
        keys = set()
        sections = self._getAppsFromConfig(job, config)
        for section in sections:
            keys = keys.union(self._getKeysFromSection(job, config, section))
        return keys
    
    @synchronized(GitEnvironmentLock)
    def _getHdKeySet(self, job):
        """
        Get all Keys used on Hd
        """
        hdKeys = set()
        prog = re.compile("(.*).pub")
        for dirname, dirnames, filenames in os.walk(dissomniag.config.git.pathToKeyFolder):
            for filename in filenames:
                result = prog.match(filename)
                if result:
                    hdKeys.add(str(result.group(1)))
        return hdKeys
    
    @synchronized(GitEnvironmentLock)
    def _getKeysToAdd(self, job, config):
        """
        return _getConfigKeys - _getHdKeys
        """
        inConfig = self._getConfigKeySet(job, config)
        onHd = self._getHdKeySet(job)
        return inConfig.difference(onHd)
    
    @synchronized(GitEnvironmentLock)
    def _getKeysToDelete(self, job, config):
        """
        return _getHdKeys - _getConfigKeys
        """
        inConfig = self._getConfigKeySet(job, config)
        onHd = self._getHdKeySet(job)
        return onHd.difference(inConfig)
    
    def _deleteNotLongerUsedKeys(self, job, config):
        self.multiLog("Entering git._deleteNotLongerUsedKeys", job)
        deleteSet = self._getKeysToDelete(job, config)
        for key in deleteSet:
            filename = ("%s.pub" % key)
            fullFileName = os.path.join(dissomniag.config.pathToKeyFolder, filename)
            try:
                os.remove(fullFileName)
            except OSError as e:
                msg = "Could not delete a key:  %s." % filename
                log.info(msg)
                job.trace(msg)
            else:
                msg = "Deleted key %s" % filename
                log.info(msg)
                job.trace(msg)
    @synchronized(GitEnvironmentLock)#
    def _addKeys(self, job, config):
        self.multiLog("Entering git._addKeys", job)
        addSet = self._getKeysToAdd(job, config)
        keys = set()
        session = dissomniag.Session()
        index = self.adminRepo.index
        #Get User Keys
        try:
            mkeys = session.query(dissomniag.auth.PublicKey).all()
            for key in mkeys:
                if key.getUserHostString() in addSet:
                    keys.add(key)
        except NoResultFound:
            pass
        
        #GetNodeKeys
        try:
            mkeys = session.query(dissomniag.model.SSHNodeKey).all()
            for key in mkeys:
                if key.getUserHostString() in addSet:
                    keys.add(key)
        except NoResultFound:
            pass
        
        for key in keys:
            localFileName = "keydir/%s" % key.getPublicFileString()
            pathToFile = os.path.join(dissomniag.config.git.pathToKeyFolder, key.getPublicFileString())
            try:
                with open(pathToFile, 'w') as f:
                    f.write(key.publicKey)
            except Exception:
                pass
            index.add([localFileName])
        return
            
        
    @synchronized(GitEnvironmentLock)
    def _commit(self, job, commitMessage = None):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
        self.multiLog("Entering git._commit", job)
        if commitMessage == None:
            commitMessage = time.strftime("%d.%m.%Y, %H:%M:%S")
        index = self.adminRepo.index
        msg = ("Commit gitosis-admin Repo %s" % commitMessage)
        log.info(msg)
        job.trace(msg)
        ret = index.commit(commitMessage)
        return True

    @synchronized(GitEnvironmentLock)
    def _pull(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
        self.multiLog("Entering git._pull", job)
        if self.adminRepo.is_dirty():
            self._commit(job, "Dirty repo commit")
        origin = self.adminRepo.remotes.origin
        try:
            origin.pull()
        except Exception:
            dissomniag.getIdentity().refreshSSHEnvironment()
            self.multiLog("Entering git._pull AGAIN", job)
            origin.pull()
        return True
    
    @synchronized(GitEnvironmentLock)
    def _push(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject() 
        self.multiLog("Entering git._push", job)
        origin = self.adminRepo.remotes.origin
        try:
            origin.push()
        except Exception:
            dissomniag.getIdentity().refreshSSHEnvironment()
            self.multiLog("Entering git._push AGAIN", job)
            origin.push()
        return True