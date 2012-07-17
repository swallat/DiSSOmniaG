# -*- coding: utf-8 -*-
# DiSSOmniaG (Distributed Simulation Service wit OMNeT++ and Git)
# Copyright (C) 2011, 2012 Sebastian Wallat, University Duisburg-Essen
# 
# Based on an idea of:
# Sebastian Wallat <sebastian.wallat@uni-due.de, University Duisburg-Essen
# Hakim Adhari <hakim.adhari@iem.uni-due.de>, University Duisburg-Essen
# Martin Becke <martin.becke@iem.uni-due.de>, University Duisburg-Essen
#
# DiSSOmniaG is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DiSSOmniaG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DiSSOmniaG. If not, see <http://www.gnu.org/licenses/>
import os
import pwd, grp
import git
import subprocess
import shlex
import ConfigParser
import time
import shutil
import re
import tempfile
import dissomniag
import logging
import StringIO
import hashlib
import threading, thread
import pyinotify
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from dissomniag.utils.wrapper import synchronized
import dissomniag

log = logging.getLogger("GitEnvironment")

GitEnvironmentLock = threading.RLock()

class GitEventHandler(pyinotify.ProcessEvent):
    
    def process_IN_CREATE(self, event):
        log.error("GIT(EVENT) %s" % event.pathname)
        filename = event.pathname
        time.sleep(1)
        
        lines = None
        with dissomniag.rootContext():
            try:
                with open(filename, 'r') as f:
                    lines = f.readlines()
            except Exception as e:
                log.error("GitEventHandler: Cannot read file %s." % filename)
                return
        
        session = dissomniag.Session()
        
        if lines != None:
            for line in lines:
                try:
                    splitted = line.split("=")
                    appName = splitted[0].strip()
                    branchName = splitted[1].strip()
                    
                    try:
                        app = session.query(dissomniag.model.App).filter(dissomniag.model.App.name == appName).one()
                        vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == branchName).one()
                        liveCd = vm.liveCd
                        rel = session.query(dissomniag.model.AppLiveCdRelation).filter(dissomniag.model.AppLiveCdRelation.liveCd == liveCd).filter(dissomniag.model.AppLiveCdRelation.app == app).one()
                        rel.createRefreshAndResetJob(dissomniag.getIdentity().getAdministrativeUser())
                        log.info("App %s auto git update executed on branch %s." % (appName, branchName))
                    except Exception as e:
                        log.error("SKIPPED App %s auto git update executed on branch %s. Exception: %s" % (appName, branchName, str(e)))
                except Exception as e:
                    log.error("process_GIT_EVENT: No valid request.")
        with dissomniag.rootContext():
            try:
                os.remove(filename)
            except OSError as e:
                log.error("Could not delete file %s in git event handler." % filename)
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
        if not '_ready' in dir(self):
            self._ready = True
            self._setUpGitFileChangeListener()
            
    def _setUpGitFileChangeListener(self):
        if os.access(dissomniag.config.git.scriptSyncFolder, os.F_OK):
            with dissomniag.rootContext():
                try:
                    shutil.rmtree(dissomniag.config.git.scriptSyncFolder)
                except Exception as e:
                    pass
            
        self.multiLog("No %s Folder. Try to create it." % dissomniag.config.git.scriptSyncFolder)
        with dissomniag.rootContext():
            try:
                os.makedirs(dissomniag.config.git.scriptSyncFolder)
                uid, gid = self._getGitUserGroup()
                os.chown(dissomniag.config.git.scriptSyncFolder, uid, gid)
            except OSError, e:
                self.multiLog("Could not create script Sync folder. %s" % e)
                self.isAdminUsable = False
                return
            
        self.multiLog("Adding Watch to %s" % dissomniag.config.git.scriptSyncFolder)
        self.wm = pyinotify.WatchManager()
        mask = pyinotify.IN_CREATE
        
        self.notifier = pyinotify.ThreadedNotifier(self.wm, GitEventHandler())
        self.notifier.start()
        
        self.wdd = self.wm.add_watch(dissomniag.config.git.scriptSyncFolder, mask, rec = False)
        return True
        
        
    
    def multiLog(self, msg, job = None):
        log.info(msg)
        if job != None:
            job.trace(msg)
        
    def createCheckJob(self):
        context = dissomniag.taskManager.Context()
        user = dissomniag.getIdentity().getAdministrativeUser()
        job = dissomniag.taskManager.Job(context, "Makce initial check git environment", user = user)
        job.addTask(dissomniag.tasks.CheckGitEnvironment())
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user, self, job)
        return True
    
    @synchronized(GitEnvironmentLock)
    def _checkAdmin(self, job = None):
        #1. Check if Utility Folder exists
        if job != None:
            job.trace("Start _checkAdmin in GitEnvironment")
        
        ### FIX: Delete every time before creation. Not clean but it works. So git repo doesn't get unusable
        #try:
        #    if os.access(dissomniag.config.git.pathToLocalUtilFolder, os.F_OK):
        #        dissomniag.getRoot()
        #        shutil.rmtree(dissomniag.config.git.dissomniag.config.git.scriptSyncFolderpathToLocalUtilFolder)
        #except Exception as e:
        #    if job != None:
        #        self.multiLog("INITIAL DELETE ERROR %s" % str(e), job)
        #finally:
        #    dissomniag.resetPermissions()
        
        try:
            if not os.access(dissomniag.config.git.scriptSyncFolder, os.F_OK):
                if job != None:
                    self.multiLog("No %s Folder. Try to create it." % dissomniag.config.git.scriptSyncFolder, job)
                with dissomniag.rootContext():
                    try:
                        os.makedirs(dissomniag.config.git.scriptSyncFolder)
                        uid, gid = self._getGitUserGroup()
                        os.chown(dissomniag.config.git.scriptSyncFolder,
                             uid,
                             gid)
                    except OSError, e:
                        if job != None:
                            self.multiLog("Could not create script Sync folder. %s" % e, job)
                        self.isAdminUsable = False
                        return
                    

            
            if not os.access(dissomniag.config.git.pathToLocalUtilFolder, os.F_OK):
                if job != None:
                    self.multiLog("No %s Folder. Try to create it." % dissomniag.config.git.pathToLocalUtilFolder, job)
                with dissomniag.rootContext():
                    try:
                        os.makedirs(dissomniag.config.git.pathToLocalUtilFolder)
                        os.chown(dissomniag.config.git.pathToLocalUtilFolder,
                                 dissomniag.config.dissomniag.userId,
                                 dissomniag.config.dissomniag.groupId)
                    except OSError, e:
                        if job != None:
                            self.multiLog("Could not create utility folder. %s" % e, job)
                        self.isAdminUsable = False
                        return
                
                if self._makeInitialCheckout(job):
                    self.isAdminUsable = True
                    try:
                        self.adminRepo = git.Repo(dissomniag.config.git.pathToLocalUtilFolder)
                        self.update(job)
                    except Exception as e:
                        if job != None:
                            self.multiLog(str(e), job)
                        self.isAdminUsable = False
                        return False
                else:
                    self.isAdminUsable = False
            else:
                try:
                    self.adminRepo = git.Repo(dissomniag.config.git.pathToLocalUtilFolder)
                except Exception as e:
                    if job != None:
                        self.multiLog(str(e), job)
                    self.isAdminUsable = False
                    return False
                self._pull(job)
                self.isAdminUsable = True
                if not self._checkRunningConfig(job):
                    log.info("Config needs update")
                    self.update(job)
                    
                
                return True
                
        except Exception as e:
            if job != None:
                self.multiLog("GENERAL ERROR %s" % e, job)
            return False
        
    @synchronized(GitEnvironmentLock)
    def update(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
        
        if not self.isAdminUsable:
            return False
        with dissomniag.rootContext():
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
            self._addKeys(config, job)
            
            #3d) calc hdKeyList - usedKeyList
            #3e) delete not used keys (5.) on Hd
            self._deleteNotLongerUsedKeys(config, job = None)
            
            #5. commit repo
            self._commit(job)
            
            #6. push repo
            self._push(job)
        
    @synchronized(GitEnvironmentLock)
    def makeInitialCommit(self, app, job = None):
        skeletonFolder, skeletonRepo = self._getSkeletonFolder(job)
        if skeletonFolder == None:
            self.multiLog("Could not create tmp skeleton folder", job)
            raise dissomniag.taskManager.TaskFailed("Could not create tmp skeleton folder")
        with dissomniag.rootContext():
            try:
                gitosisRepo = str("%s@%s:%s.git" % (dissomniag.config.git.gitUser, dissomniag.config.git.gitosisHost, app.name))
                skeletonRepo.create_remote("origin", gitosisRepo)
                skeletonRepo.git.push("origin", "master:refs/heads/master")
                self.addUpdateScript(app, job)
            except Exception as e:
                self.multiLog("Cannot push to origin repo. %s, Exception: %s" % (gitosisRepo, str(e)), job)
                raise dissomniag.taskManager.TaskFailed("Cannot push to origin repo. %s" % gitosisRepo)
            finally:
                try:
                    del(skeletonRepo)
                    shutil.rmtree(skeletonFolder)
                except Exception as e:
                    pass
        return True
    
    @synchronized(GitEnvironmentLock)
    def addUpdateScript(self, app, job = None):
        log.info("Trying to add Upadte Hook.")
        targetFile = os.path.join(dissomniag.config.git.pathToGitRepositories, "%s.git/hooks/update" % app.name)
        with dissomniag.rootContext():
            try:
                with open(targetFile, 'w') as f:
                    f.write(self.getScriptPattern(str(app.name)))
            except OSError as e:
                log.error("Could not create update Script.")
                return False
        with dissomniag.rootContext():
            try:
                uid, gid = self._getGitUserGroup()
                os.chown(targetFile, uid, gid)
                os.chmod(targetFile, 0o755)
            except OSError as e:
                try:
                    shutil.rmtree(targetFile)
                    log.error("Cannot change User for update hook.")
                except Exception as e:
                    log.error("Cannot delete update hook.")

        return True
    
    @synchronized(GitEnvironmentLock)
    def _getSkeletonFolder(self, job = None):
        directory_name = tempfile.mkdtemp()
        skeletonFolder = os.path.join(directory_name, "git-skeleton")
        #if os.access(dissomniag.config.git.pathToSkeleton, os.F_OK):
        #    try:
        #        shutil.rmtree(dissomniag.config.git.pathToSkeleton)
        #    except Exception as e:
        #        self.multiLog("Could not delete git Skeleton folder %s" % dissomniag.config.git.pathToSkeleton, job)
        #        self.isSkeletonUsable = False
        #        return False
        try:
            shutil.copytree(dissomniag.config.git.pathToStaticSkeleton, skeletonFolder)
            os.chown(skeletonFolder,
                     dissomniag.config.dissomniag.userId,
                     dissomniag.config.dissomniag.groupId)
            repo = git.Repo.init(skeletonFolder)
            commitableFiles = []
            for dirname, dirnames, filenames in os.walk(skeletonFolder):
                for subdirname in dirnames:
                    fullpath = os.path.join(dirname, subdirname)
                    os.chown(fullpath,
                             dissomniag.config.dissomniag.userId,
                             dissomniag.config.dissomniag.groupId)
                for filename in filenames:
                    fullpath = os.path.join(dirname, filename)
                    pathToFile = os.path.relpath(fullpath, skeletonFolder)
                    os.chown(fullpath,
                             dissomniag.config.dissomniag.userId,
                             dissomniag.config.dissomniag.groupId)
                    if not pathToFile.startswith(".git"):
                        commitableFiles.append(pathToFile)
                        
                        
            repo.index.add(commitableFiles)
            repo.index.commit("Initial Commit")
            repo.commit()
            return directory_name, repo
        except OSError, e:
            if job != None:
                self.multiLog("Could not create skeleton folder. %s" % e, job)
            return None, None
        finally:
            pass
    
    @synchronized(GitEnvironmentLock)
    def _checkRunningConfig(self, job = None):
        inFile = None
        with dissomniag.rootContext():
            try:
                with open(dissomniag.config.git.pathToConfigFile, 'r') as f:
                    inFile = f.read()
            except Exception:
                pass
        config = self._getNewConfig(job)
        actualConfig = StringIO.StringIO()
        config.write(actualConfig)
        actualConfig = actualConfig.getvalue()
        
        inHash = hashlib.sha256()
        inHash.update(inFile)
        
        actHash = hashlib.sha256()
        actHash.update(actualConfig)
        
        if not ((self._getConfigKeySet(config, job) <= self._getHdKeySet(job)) and (self._getConfigKeySet(config, job) <= self._getHdKeySet(job))):
            log.info("HD Keys and Config Keys differ!")
            return False
        grp.getgrnam(str(dissomniag.config.git.gitGroup)).gr_gid
        if inHash.hexdigest() == actHash.hexdigest():
            return True
        else:
            return False
        
    @synchronized(GitEnvironmentLock)            
    def _makeInitialCheckout(self, job = None):
        if job != None:
            self.multiLog("Entering git._makeInitialCheckout", job)
        self._disableStrictServerKeyChecking(dissomniag.config.git.gitosisHost)
        gitosisAdminRepo = ("%s@%s:gitosis-admin.git" % (dissomniag.config.git.gitUser, dissomniag.config.git.gitosisHost))
        if job != None:
            self.multiLog("GitosisAdminRepo %s" % gitosisAdminRepo, job)
        try:
            origRepo = git.Repo.clone_from(gitosisAdminRepo, dissomniag.config.git.pathToLocalUtilFolder)
        except Exception as e:
            if job != None:
                self.multiLog(str(e), job)
                self.multiLog("Could not clone gitosis-admin Repository. Please add DiSSOmniag ssh_key file to the gitosis-admin group!", job)
            try:
                shutil.rmtree(dissomniag.config.git.pathToLocalUtilFolder)
            except Exception:
                pass
            return False
        else:
            return True
        
    @synchronized(GitEnvironmentLock)
    def _disableStrictServerKeyChecking(self, hostOrIp="localhost"):
        with dissomniag.rootContext():
            sshFileName = "/etc/ssh/ssh_config"
            
            if os.path.isfile(sshFileName):
                lines = None
                pattern = ("^Host %s$" % hostOrIp)
                prog = re.compile(pattern)
                with open(sshFileName, 'r') as f:
                    lines = f.readlines()
                foundHosts = []
                for line in lines:
                    if prog.match(line):
                        return True
                    
                
            if not os.path.isfile(sshFileName):
                try:
                    with open(sshFileName, mode='w') as f:
                        f.write("")
                    os.chmod(sshFileName, 0o644)
                except OSError:
                    pass
            
            with open(sshFileName, 'a') as f:
                f.write("Host %s\n" % hostOrIp)
                f.write("\tStrictHostKeyChecking no\n\n")
        
    @synchronized(GitEnvironmentLock)
    def _checkRepoFolder(self, job = None):
        try:
            if not os.access(dissomniag.config.git.pathToGitRepositories, os.W_OK):
                self.isRepoFolderUsable = False
            else:
                self.isRepoFolderUsable = True
        except Exception as e:
            if job != None:
                job.trace("GENERAL ERROR %s" % e)
                log.info("GENERAL ERROR %s" % e)
            self.isRepoFolderUsable = False
            return
                        
    @synchronized(GitEnvironmentLock)
    def _getNewConfig(self, job = None):
        if job != None:
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
                config.set(sectionName, "writable", repoName)
                keys = adminUserKeys
                #Add user keys
                for user in app.users:
                    if user.publicKeys != None:
                        keys = keys.union(self._getMembersSet(user.publicKeys))
                        
                #Add Admin LiveCd Node Keys
                for relation in app.AppLiveCdRelations:
                    keys.add(str(relation.liveCd.vm.sshKey.getUserHostString()))
                
                config.set(sectionName, "members", " ".join(keys))
                        
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
    def _getAppsFromConfig(self, config, job = None):
        apps = set()
        prog = re.compile("group (.*)")
        for section in config.sections():
            result = prog.match(section)
            if result:
                apps.add(str(result.group(1)))
                continue
        return apps
    
    @synchronized(GitEnvironmentLock)
    def _getKeysFromSection(self, config, sectionName, job = None):
        keys = set()
        try:
            sectionName = "group %s" % sectionName
            my_keys = config.get(sectionName, 'members')
            my_keys = my_keys.split(" ")
            for mKey in my_keys:
                keys.add(str(mKey))
        except Exception:
            pass
        return keys
    
    @synchronized(GitEnvironmentLock)
    def _getConfigKeySet(self, config, job = None):
        """
        Get all keys used in config
        """
        keys = set()
        sections = self._getAppsFromConfig(config, job)
        for section in sections:
            keys = keys.union(self._getKeysFromSection(config, str(section), job))
        return keys
    
    @synchronized(GitEnvironmentLock)
    def _getHdKeySet(self, job = None):
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
    def _getKeysToAdd(self, config, job = None):
        """
        return _getConfigKeys - _getHdKeys
        """
        inConfig = self._getConfigKeySet(config, job)
        onHd = self._getHdKeySet(job)
        return inConfig.difference(onHd)
    
    @synchronized(GitEnvironmentLock)
    def _getKeysToDelete(self, config, job = None):
        """
        return _getHdKeys - _getConfigKeys
        """
        inConfig = self._getConfigKeySet(config, job)
        onHd = self._getHdKeySet(job)
        return onHd.difference(inConfig)
    
    @synchronized(GitEnvironmentLock)
    def _deleteNotLongerUsedKeys(self, config, job = None):
        if job != None:
            self.multiLog("Entering git._deleteNotLongerUsedKeys", job)
        deleteSet = self._getKeysToDelete(config, job)
        for key in deleteSet:
            filename = ("%s.pub" % key)
            fullFileName = os.path.join(dissomniag.config.git.pathToKeyFolder, filename)
            try:
                os.remove(fullFileName)
            except OSError as e:
                msg = "Could not delete a key:  %s." % filename
                log.info(msg)
                if job != None:
                    job.trace(msg)
            else:
                msg = "Deleted key %s" % filename
                log.info(msg)
                if job != None:
                    job.trace(msg)
                
    @synchronized(GitEnvironmentLock)
    def _addKeys(self, config, job = None):
        if job != None:
            self.multiLog("Entering git._addKeys", job)
        addSet = self._getKeysToAdd(config, job)
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
        with dissomniag.rootContext():
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
    def _commit(self, job = None, commitMessage = None):
        with dissomniag.rootContext():
            if job != None:
                self.multiLog("Entering git._commit", job)
            if commitMessage == None:
                commitMessage = str(time.strftime("%d.%m.%Y, %H:%M:%S"))
            index = self.adminRepo.index
            if job != None:
                self.multiLog("Commit gitosis-admin Repo %s" % commitMessage, job)
            ret = index.commit(commitMessage)
            self.adminRepo.commit()
            return True

    @synchronized(GitEnvironmentLock)
    def _pull(self, job = None):
        with dissomniag.rootContext():
            if job != None:
                self.multiLog("Entering git._pull", job)
            if self.adminRepo.is_dirty():
                self._commit(job, "Dirty repo commit")
            origin = self.adminRepo.remotes.origin
            dissomniag.getIdentity().refreshSSHEnvironment()
            try:
                origin.pull()
            except Exception:
                dissomniag.getIdentity().refreshSSHEnvironment()
                if job != None:
                    self.multiLog("Entering git._pull AGAIN", job)
                origin.pull()
            return True
    
    @synchronized(GitEnvironmentLock)
    def _push(self, job = None):
        with dissomniag.rootContext():
            if job != None:
                self.multiLog("Entering git._push", job)
            origin = self.adminRepo.remotes.origin
            dissomniag.getIdentity().refreshSSHEnvironment()
            try:
                origin.push()
            except Exception:
                dissomniag.getIdentity().refreshSSHEnvironment()
                if job != None:
                    self.multiLog("Entering git._push AGAIN", job)
                origin.push()
            return True
    
    @synchronized(GitEnvironmentLock)
    def _getGitUserGroup(self):
        user = pwd.getpwnam(str(dissomniag.config.git.gitUser))
        uid = user.pw_uid
        gid = user.pw_gid
        return uid, gid 
    
    @synchronized(GitEnvironmentLock)
    def getScriptPattern(self, appName):
        return ("""#!/usr/bin/env python
# -*- coding: utf-8 -*-
# DiSSOmniaG (Distributed Simulation Service wit OMNeT++ and Git)
# Copyright (C) 2011, 2012 Sebastian Wallat, University Duisburg-Essen
# 
# Based on an idea of:
# Sebastian Wallat <sebastian.wallat@uni-due.de, University Duisburg-Essen
# Hakim Adhari <hakim.adhari@iem.uni-due.de>, University Duisburg-Essen
# Martin Becke <martin.becke@iem.uni-due.de>, University Duisburg-Essen
#
# DiSSOmniaG is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DiSSOmniaG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DiSSOmniaG. If not, see <http://www.gnu.org/licenses/>
import sys, os, time

args = sys.argv
fullBranch = args[1]
splittedBranch = fullBranch.split("/")
branch = splittedBranch[len(splittedBranch)-1].strip()

scriptSyncFolder = "%s"
appName = "%s"
filename = "".join((appName, "_", str(time.time())))
myFile = os.path.join(scriptSyncFolder, filename)

try:
    with open(myFile, 'w') as f:
        f.write("".join((appName, " = ", branch, "")))
except Exception as e:
    print("".join(("Cannot write to file ", myFile, ". ", str(e))))
    
sys.exit(0)
        """ % (dissomniag.config.git.scriptSyncFolder, appName))