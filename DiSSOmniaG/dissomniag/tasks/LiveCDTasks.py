# -*- coding: utf-8 -*-
"""
Created on 31.08.2011

@author: Sebastian Wallat
"""
import os, shutil, subprocess, shlex, re, platform
import lockfile
import apt
import dissomniag

import logging

log = logging.getLogger("tasks.LiveCDTasks")

class LiveCdEnvironmentChecks(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        
        self.infoObj = dissomniag.model.LiveCdEnvironment()
        
        #1. Check if Utility Folder exists
        if not os.access(dissomniag.config.dissomniag.utilityFolder, os.F_OK):
            try:
                dissomniag.getRoot()
                os.mkdir(dissomniag.config.dissomniag.utilityFolder)
                os.chown(dissomniag.config.dissomniag.utilityFolder,
                         dissomniag.config.dissomniag.userId,
                         dissomniag.config.dissomniag.groupId)
                os.mkdir(dissomniag.config.dissomniag.serverFolder)
                os.chown(dissomniag.config.dissomniag.serverFolder,
                         dissomniag.config.dissomniag.userId,
                         dissomniag.config.dissomniag.groupId)
            except OSError, e:
                self.infoObj.errorInfo.append("Could not create utility folder. %s" % e)
                self.infoObj.usable = False
                self.job.trace(self.infoObj.getErrorInfo())
                raise dissomniag.taskManager.UnrevertableFailure()
            finally:
                dissomniag.resetPermissions()
            
        #2 Check if Utility Folder is writable
        if not os.access(dissomniag.config.dissomniag.utilityFolder, os.W_OK):
            self.infoObj.errorInfo.append("Utility Folder is not writable.")
            self.infoObj.usable = False
            self.job.trace(self.infoObj.getErrorInfo())
            raise dissomniag.taskManager.UnrevertableFailure()
        
        if not os.access(dissomniag.config.dissomniag.serverFolder, os.W_OK):
            self.infoObj.errorInfo.append("Server Folder is not writable.")
            self.infoObj.usable = False
            self.job.trace(self.infoObj.getErrorInfo())
            raise dissomniag.taskManager.UnrevertableFailure()
        
        #3. Check if server has root permissions
        if not os.getuid() == 0:
            self.infoObj.errorInfo.append("The server needs root privileges to create live cd's.")
            self.infoObj.usable = False
            self.job.trace(self.infoObj.getErrorInfo())
            raise dissomniag.taskManager.UnrevertableFailure()
        
        #4. Check if all utilities to create live cd's are installed. Try to install them.
        dissomniag.getRoot()
        cache = apt.Cache()
        
        execInstall = False
        try:
            liveBuild = cache["live-build"]
            if not liveBuild.isInstalled:
                liveBuild.markInstall()
                execInstall = True
                
            debootstrap = cache["debootstrap"]
            if not debootstrap.isInstalled:
                debootstrap.markInstall()
                execInstall = True
                
            syslinux = cache["syslinux"]
            if not syslinux.isInstalled:
                syslinux.markInstall()
                execInstall = True
                
            squashfsTools = cache["squashfs-tools"]
            if not squashfsTools.isInstalled:
                squashfsTools.markInstall()
                execInstall = True
                
            genisoimage = cache["genisoimage"]
            if not genisoimage.isInstalled:
                genisoimage.markInstall()
                execInstall = True
            
            sbm = cache["sbm"]
            if not sbm.isInstalled:
                sbm.markInstall()
                execInstall = True
        except KeyError:
            self.infoObj.error.append("A apt package is not available!")
            self.infoObj.usable = False
            self.job.trace(self.infoObj.getErrorInfo())
            dissomniag.resetPermissions()
            raise dissomniag.taskManager.UnrevertableFailure()
            
        if execInstall:
            if cache.commit(apt.progress.TextFetchProgress(),
                         apt.progress.InstallProgress()):
                self.infoObj.usable = True
                dissomniag.resetPermissions()
                return dissomniag.taskManager.TaskReturns.SUCCESS
            else:
                self.infoObj.error.append("Installation Error!")
                self.infoObj.usable = False
                self.job.trace(self.infoObj.getErrorInfo())
                dissomniag.resetPermissions()
                raise dissomniag.taskManager.UnrevertableFailure()
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()
    
class CheckLiveCdEnvironmentPrepared(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        self.infoObj = dissomniag.model.LiveCdEnvironment()
        
        self.patternFolder = os.path.join(dissomniag.config.dissomniag.serverFolder,
                                dissomniag.config.dissomniag.liveCdPatternDirectory)
        
        
        checkedFile = os.path.join(self.patternFolder, "CHECKED")
        checkedFileExists = os.access(checkedFile, os.F_OK)
        
        stageDirectory = os.path.join(self.patternFolder, ".stage/")
        stageDirectoryExists = os.access(stageDirectory, os.F_OK)
        
        if stageDirectoryExists:
            binaryIso = os.path.join(stageDirectory, "binary_iso")
            binaryIsoExists = os.access(binaryIso, os.F_OK)
        else:
            binaryIsoExists = False
        
        configDirectory = os.path.join(self.patternFolder, "config/")
        configDirectoryExists = os.access(configDirectory, os.F_OK)
        
        binLocalIncEmpty = True
        if configDirectoryExists:
            binaryLocalIncludesFolder = os.path.join(configDirectory, "binary_local-includes/")
            binaryLocalIncExists = os.access(binaryLocalIncludesFolder, os.F_OK)
            if binaryLocalIncExists and os.listdir(binaryLocalIncludesFolder) != []:
                binLocalIncEmpty = False
                
        
        autoDirectory = os.path.join(self.patternFolder, "auto/")
        autoDirectoryExists = os.access(autoDirectory, os.F_OK)
        
        chrootDirectory = os.path.join(self.patternFolder, "chroot/")
        chrootDirectoryExists = os.access(chrootDirectory, os.F_OK)
        
        
        if checkedFileExists and stageDirectoryExists and configDirectoryExists and autoDirectoryExists and chrootDirectoryExists and binLocalIncEmpty and binaryIsoExists:
            self.infoObj.prepared = True
        else:
                self.infoObj.prepared = False
            
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS

class PrepareLiveCdEnvironment(dissomniag.taskManager.AtomicTask):
    
    def multiLog(self, msg, log = log):
        super(PrepareLiveCdEnvironment, self).multiLog(msg, log)
        self.infoObj.errorInfo.append(msg)
    
    def returnSuccess(self):
        self.multiLog("LiveCD Environment prepared!")
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def checkIfPatternFolderExists(self):
        if os.access(self.patternFolder, os.F_OK):
            try:
                shutil.rmtree(self.patternFolder)
            except OSError, e:
                self.multiLog("Could not delete Pattern folder. %s" % e)
                self.infoObj.usable = False
                dissomniag.resetPermissions()
                raise dissomniag.taskManager.UnrevertableFailure()
                
            
        try:
            os.mkdir(self.patternFolder)
            os.chown(self.patternFolder,
                     dissomniag.config.dissomniag.userId,
                     dissomniag.config.dissomniag.groupId)
        except OSError, e:
            self.multiLog("Could not create LiveCD pattern folder. %s" % e)
            self.infoObj.usable = False
            dissomniag.resetPermissions()
            raise dissomniag.taskManager.UnrevertableFailure()
        
    def deleteOldDebianLiveFolders(self, patternFolder):
        
        folder = patternFolder
        if folder.endswith("/"):
            l = len(folder)
            folder = folder[0:(l - 1)]
        
        cmd = "rm -rf %s/binary* %s/.stage %s/auto %s/config %s/cache %s/chroot" % (folder, folder, folder, folder, folder, folder)
        self.multiLog("exec %s" % cmd)
        ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
        
        
    def cleanUp(self):
        
        self.patternFolder = os.path.join(dissomniag.config.dissomniag.serverFolder,
                                dissomniag.config.dissomniag.liveCdPatternDirectory)
        dissomniag.getRoot()
        
        self.stageDir = os.path.join(self.patternFolder, ".stage")
        self.binLocalInc = os.path.join(self.patternFolder, "config/binary_local-includes")
        
        if self.binLocalInc.endswith("/"):
            cmd = "rm -rf %s/*" % self.binLocalInc
        else:
            cmd = "rm -rf %s*" % self.binLocalInc
        self.multiLog("exec %s" % cmd, log)
        ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
        if ret != 0:
            self.multiLog("Could not exec %s correctly" % cmd, log)
        
        if self.stageDir.endswith("/"):
            cmd = "rm %sbinary_iso %sbinary_checksums %sbinary_local-includes" % (self.stageDir, self.stageDir, self.stageDir)
        else:
            cmd = "rm %s/binary_iso %s/binary_checksums %s/binary_local-includes" % (self.stageDir, self.stageDir, self.stageDir)
        self.multiLog("exec %s" % cmd, log)
        ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
        if ret != 0:
            self.multiLog("Could not exec %s correctly" % cmd, log)
        
        
        
    def run(self):
        self.infoObj = dissomniag.model.LiveCdEnvironment()
        if self.infoObj.prepared:
            return self.returnSuccess()
        
        #If the Environment is not prepared, create it.
        
        #1. Check if Pattern folder exists. 
        #    True: Delete, and recreate it
        #    False: just create it
        self.patternFolder = os.path.join(dissomniag.config.dissomniag.serverFolder,
                                dissomniag.config.dissomniag.liveCdPatternDirectory)
        dissomniag.getRoot()

        
        self.checkIfPatternFolderExists()
        
        try:
            #3. Change current working Directory
            if not dissomniag.chDir(self.patternFolder):
                self.multiLog("Cannot chdir to %s" % self.patternFolder, log)
                dissomniag.resetPermissions()
                raise dissomniag.taskManager.TaskFailed()
            
            self.deleteOldDebianLiveFolders(self.patternFolder)
            
            #2. Create File Lock for Pattern environment
            self.lockFile = os.path.join(self.patternFolder,
                                         dissomniag.config.dissomniag.patternLockFile)
            self.mylock = lockfile.FileLock(self.lockFile, threaded = True)
            
            with self.mylock:
                
                #4. Make auto Directory
                self.autoFolder = os.path.join(self.patternFolder, "auto/")
                #5. Init debian live environment
                cmd = "lb config"
                self.multiLog("running %s" % cmd)
                ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
                if ret != 0:
                    self.multiLog("LB Config error")
                    dissomniag.resetPermissions()
                    raise dissomniag.taskManager.TaskFailed()
                
                #6. Copy conif.sh
                configFile = os.path.join(dissomniag.config.dissomniag.staticLiveFolder,
                                          "config")
                try:
                    shutil.copy2(configFile, self.autoFolder)
                except OSError, e:
                    self.multiLog("Could not copy LiveCD config file. %s" % e)
                    self.infoObj.usable = False
                    raise dissomniag.taskManager.UnrevertableFailure()
                
                cmd = "lb config"
                self.multiLog("running %s" % cmd)
                ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
                if ret != 0:
                    self.multiLog("LB Config error")
                    dissomniag.resetPermissions()
                    raise dissomniag.taskManager.TaskFailed()                
                
                #..... Insert other steps ....
                
                #7. Make initial Build
                # Try 10 times
                cmd = "lb build"
                self.multiLog("Make initial Build", log)
                success = False
                for i in range(1, 11):
                    if self.job._getStatePrivate() == dissomniag.taskManager.jobs.JobStates.CANCELLED:
                        self.multiLog("Job cancelled. Initial LivdCD build failed.")
                        raise dissomniag.taskManager.TaskFailed("Job cancelled. Initial LivdCD build failed.")
                    
                    ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
                    if ret != 0:
                        self.multiLog("Initial LiveCD build failed. Retry %d" % i, log)
                        continue
                    else:
                        success = True
                        break
                if not success:
                    self.multiLog("Initial LiveCD build failed finally.", log)
                    raise dissomniag.taskManager.TaskFailed("Initial LiveCD build failed finally.")

                #7. Mark environment as Prepared
                preparedFile = os.path.join(self.patternFolder, "CHECKED")
                myFile = open(preparedFile, 'w')
                myFile.write("CHECKED")
                myFile.close()
                self.returnSuccess()
        finally:
                if not dissomniag.resetDir():
                    self.multiLog("Cannot chdir to %s" % self.patternFolder, log)
                dissomniag.resetPermissions()
                
                self.cleanUp()
    
    def revert(self):
        
        self.patternFolder = os.path.join(dissomniag.config.dissomniag.serverFolder,
                                dissomniag.config.dissomniag.liveCdPatternDirectory)
        self.chrootFolder = os.path.join(self.patternFolder, "chroot")
        dissomniag.getRoot()
        self.cleanUp()
        dissomniag.resetPermissions()
        return dissomniag.taskManager.TaskReturns.SUCCESS
