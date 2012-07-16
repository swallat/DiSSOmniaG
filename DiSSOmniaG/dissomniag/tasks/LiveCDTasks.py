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
import os, shutil, subprocess, shlex, re, platform
import lockfile
import apt
import tarfile
import dissomniag

import logging

log = logging.getLogger("tasks.LiveCDTasks")

class LiveCdEnvironmentChecks(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        
        self.infoObj = dissomniag.model.LiveCdEnvironment()
        
        #1. Check if Utility Folder exists
        if not os.access(dissomniag.config.dissomniag.utilityFolder, os.F_OK):
            with dissomniag.rootContext():
                try:
                    os.makedirs(dissomniag.config.dissomniag.utilityFolder)
                    os.chown(dissomniag.config.dissomniag.utilityFolder,
                             dissomniag.config.dissomniag.userId,
                             dissomniag.config.dissomniag.groupId)
                    os.makedirs(dissomniag.config.dissomniag.serverFolder)
                except OSError, e:
                    self.infoObj.errorInfo.append("Could not create utility folder. %s" % e)
                    self.infoObj.usable = False
                    self.job.trace(self.infoObj.getErrorInfo())
                    raise dissomniag.taskManager.UnrevertableFailure()
            
        #2 Check if Utility Folder is writable
        if not os.access(dissomniag.config.dissomniag.utilityFolder, os.W_OK):
            try:
                with dissomniag.rootContext():
                    os.chown(dissomniag.config.dissomniag.utilityFolder,
                             dissomniag.config.dissomniag.userId,
                             dissomniag.config.dissomniag.groupId)
            except OSError as e:
                self.infoObj.errorInfo.append("Utility Folder is not writable.")
                self.infoObj.usable = False
                self.job.trace(self.infoObj.getErrorInfo())
                raise dissomniag.taskManager.UnrevertableFailure()
        
        if not os.access(dissomniag.config.dissomniag.serverFolder, os.W_OK):
            try:
                with dissomniag.rootContext():
                    os.makedirs(dissomniag.config.dissomniag.serverFolder)
                    os.chown(dissomniag.config.dissomniag.serverFolder,
                            dissomniag.config.dissomniag.userId,
                            dissomniag.config.dissomniag.groupId)
            except OSError as e:
                self.infoObj.errorInfo.append("Server Folder is not writable.")
                self.infoObj.usable = False
                self.job.trace(self.infoObj.getErrorInfo())
                raise dissomniag.taskManager.UnrevertableFailure()
        
        if not os.access(dissomniag.config.dissomniag.vmsFolder, os.W_OK):
            try:
                with dissomniag.rootContext():
                    os.makedirs(dissomniag.config.dissomniag.vmsFolder)
                    os.chown(dissomniag.config.dissomniag.vmsFolder,
                             dissomniag.config.dissomniag.userId,
                             dissomniag.config.dissomniag.groupId)
            except OSError as e:
                self.infoObj.errorInfo.append("LiveImages Folder is not writable.")
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
        with dissomniag.rootContext():
            cache = apt.Cache()
            
            execInstall = False
            try:
                liveBuild = cache["live-build"]
                if not liveBuild.is_installed:
                    liveBuild.markInstall()
                    execInstall = True
            except KeyError:
                self.infoObj.errorInfo.append("A apt package is not available!")
                self.infoObj.usable = False
                self.job.trace(self.infoObj.getErrorInfo())
                raise dissomniag.taskManager.UnrevertableFailure()
                
            if execInstall:
                if cache.commit(apt.progress.TextFetchProgress(),
                             apt.progress.InstallProgress()):
                    self.infoObj.usable = True
                    return dissomniag.taskManager.TaskReturns.SUCCESS
                else:
                    self.infoObj.error.append("Installation Error!")
                    self.infoObj.usable = False
                    self.job.trace(self.infoObj.getErrorInfo())
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
        
        stageDirectory = os.path.join(self.patternFolder, ".build/")
        stageDirectoryExists = os.access(stageDirectory, os.F_OK)
        
        configDirectory = os.path.join(self.patternFolder, "config/")
        configDirectoryExists = os.access(configDirectory, os.F_OK)
        
        binLocalIncEmpty = True
        if configDirectoryExists:
            binaryLocalIncludesFolder = os.path.join(configDirectory, "includes.binary/")
            binaryLocalIncExists = os.access(binaryLocalIncludesFolder, os.F_OK)
            if binaryLocalIncExists and os.listdir(binaryLocalIncludesFolder) != []:
                binLocalIncEmpty = False
                
        
        autoDirectory = os.path.join(self.patternFolder, "auto/")
        autoDirectoryExists = os.access(autoDirectory, os.F_OK)
        
        chrootDirectory = os.path.join(self.patternFolder, "chroot/")
        chrootDirectoryExists = os.access(chrootDirectory, os.F_OK)
        
        
        if checkedFileExists and stageDirectoryExists and configDirectoryExists and autoDirectoryExists and chrootDirectoryExists and binLocalIncEmpty: 
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
        dissomniag.Session().flush()
    
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
                raise dissomniag.taskManager.UnrevertableFailure()
                
            
        try:
            os.mkdir(self.patternFolder)
            os.chown(self.patternFolder,
                     dissomniag.config.dissomniag.userId,
                     dissomniag.config.dissomniag.groupId)
        except OSError, e:
            self.multiLog("Could not create LiveCD pattern folder. %s" % e)
            self.infoObj.usable = False
            raise dissomniag.taskManager.UnrevertableFailure()
        
    def deleteOldDebianLiveFolders(self, patternFolder):
        folder = patternFolder
        if folder.endswith("/"):
            l = len(folder)
            folder = folder[0:(l - 1)]
        
        cmd = "rm -rf %s/binary* %s/.build %s/auto %s/config %s/cache %s/chroot" % (folder, folder, folder, folder, folder, folder)
        self.multiLog("exec %s" % cmd)
        ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
        
    def installLiveDaemon(self, patternFolder):
        
        """
        1. Copy Files
        """
        tarBall = os.path.join(dissomniag.config.dissomniag.staticLiveFolder, "liveDaemon/dissomniagLive.tar.gz")
        chrootLocalIncludesFolder = os.path.join(patternFolder, "config/includes.chroot")
        targetTarBall = os.path.join(chrootLocalIncludesFolder, "dissomniagLive.tar.gz")
        try:
            shutil.copy2(tarBall, chrootLocalIncludesFolder)
        except OSError:
            self.multiLog("Cannot copy Live Daemon Tarball", log)
            raise dissomniag.taskManager.TaskFailed()
        with tarfile.open(targetTarBall, "r|gz") as tar:
            tar.extractall(path = chrootLocalIncludesFolder)
        try:
            os.remove(targetTarBall)
        except OSError:
            self.multiLog("Cannot delete LiveDaemon Tarball", log)
            
    def installOmnet(self, patternFolder):
        
        omnetTarBall = os.path.join(dissomniag.config.dissomniag.staticLiveFolder, "omnetLibs/OMNeT.tar.gz")
        inetTarBall = os.path.join(dissomniag.config.dissomniag.staticLiveFolder, "omnetLibs/INET.tar.gz")
        chrootLocalIncludesFolder = os.path.join(patternFolder, "config/includes.chroot")
        omnetTargetTarBall = os.path.join(chrootLocalIncludesFolder, "OMNeT.tar.gz")
        inetTargetTarBall = os.path.join(chrootLocalIncludesFolder, "INET.tar.gz")
        try:
            shutil.copy2(omnetTarBall, chrootLocalIncludesFolder)
            shutil.copy2(inetTarBall, chrootLocalIncludesFolder)
        except OSError:
            self.multiLog("Cannot copy OMNeT INET", log)
            raise dissomniag.taskManager.TaskFailed()
        
        with tarfile.open(omnetTargetTarBall, "r|gz") as tar:
            tar.extractall(path = chrootLocalIncludesFolder)
        
        with tarfile.open(inetTargetTarBall, "r|gz") as tar:
            tar.extractall(path = chrootLocalIncludesFolder)
        
        try:
            os.remove(omnetTargetTarBall)
            os.remove(inetTargetTarBall)
        except OSError:
            self.multiLog("Cannot delete OMNeT INET tarball", log)
        
    def cleanUp(self):
        
        self.patternFolder = os.path.join(dissomniag.config.dissomniag.serverFolder, dissomniag.config.dissomniag.liveCdPatternDirectory)
        
        if not dissomniag.chDir(self.patternFolder):
                    self.multiLog("Cannot chdir to %s" % self.patternFolder, log)
                    raise dissomniag.taskManager.TaskFailed()
        
        with dissomniag.rootContext():
            
            #Clean to binary
            cmd = "lb clean --binary"
            self.multiLog("running %s" % cmd)
            ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
            if ret != 0:
                self.multiLog("LB clean --binary error")
                #raise dissomniag.taskManager.TaskFailed()
            
            self.stageDir = os.path.join(self.patternFolder, ".build")
            self.binLocalInc = os.path.join(self.patternFolder, "config/includes.binary/")
            
            try:
                shutil.rmtree(self.binLocalInc)
            except (OSError, IOError) as e:
                pass
                
            try:
                os.makedirs(self.binLocalInc)
            except (OSError, IOError) as e:
                self.multiLog("Cannot recreate %s" % self.binLocalInc)
                
            isolinuxCfgDir = os.path.join(dissomniag.config.dissomniag.staticLiveFolder, "includes.binary/isolinux")
            try:
                os.makedirs(os.path.join(self.patternFolder, "config/includes.binary/isolinux/"))
            except OSError:
                self.multiLog("Cannot create config/includes.binary/isolinux/")
            listings = os.listdir(isolinuxCfgDir)
            for infile in listings:
                try:
                    shutil.copy2(os.path.join(isolinuxCfgDir, infile), os.path.join(self.patternFolder, "config/includes.binary/isolinux/"))
                except OSError:
                    self.multiLog("Cannot copy includes.binary")
    
            #
            #if self.stageDir.endswith("/"):
            #    cmd = "rm %sbinary_disk %sbinary_checksums %sbinary_includes" % (self.stageDir, self.stageDir, self.stageDir)
            #else:
            #    cmd = "rm %s/binary_disk %s/binary_checksums %s/binary_includes" % (self.stageDir, self.stageDir, self.stageDir)
            #self.multiLog("exec %s" % cmd, log)
            #ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
            #if ret != 0:
            #    self.multiLog("Could not exec %s correctly" % cmd, log)
        
        
        
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
        
        with dissomniag.rootContext():
        
            self.checkIfPatternFolderExists()
            
            try:
                #3. Change current working Directory
                if not dissomniag.chDir(self.patternFolder):
                    self.multiLog("Cannot chdir to %s" % self.patternFolder, log)
                    raise dissomniag.taskManager.TaskFailed()
                
                self.deleteOldDebianLiveFolders(self.patternFolder)
                
                #2. Create File Lock for Pattern environment
                self.lockFile = os.path.join(self.patternFolder,
                                             dissomniag.config.dissomniag.patternLockFile)
                self.mylock = lockfile.FileLock(self.lockFile, threaded = True)
                
                with self.mylock:
                    
                    #3a. Make auto Directory and link config files
                    self.autoFolder = os.path.join(self.patternFolder, "auto/")
                    try:
                        os.makedirs(self.autoFolder)
                    except OSError:
                        self.multiLog("Cannot create AutoFolder")
                        raise dissomniag.taskManager.TaskFailed()
                    
                    staticAutoFolder = os.path.join(dissomniag.config.dissomniag.staticLiveFolder, "auto")
                    infiles = os.listdir(staticAutoFolder)
                    for myfile in infiles:
                        try:
                            #print os.path.join(staticAutoFolder, myfile)
                            #print os.path.join(self.autoFolder, myfile)
                            os.symlink(os.path.join(staticAutoFolder, myfile), os.path.join(self.autoFolder, myfile))
                        except OSError:
                            self.multiLog("Cannot Symlink %s" % myfile , log)
                            if myfile == "config":
                                raise dissomniag.taskManager.TaskFailed()
                            
                    #3b. Create initial stucture
                    cmd = "lb config"
                    self.multiLog("running %s" % cmd)
                    ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
                    if ret != 0:
                        self.multiLog("LB Config error")
                        raise dissomniag.taskManager.TaskFailed()
                    
                    #3c. Copy dissomniag packagelist
                    packageListFile = os.path.join(dissomniag.config.dissomniag.staticLiveFolder, "packagesLists/dissomniag.list")
                    chrootLocalPackagesListFolder = os.path.join(self.patternFolder, "config/package-lists")
                    try:
                        os.symlink(os.path.abspath(packageListFile), os.path.join(chrootLocalPackagesListFolder, "dissomniag.list"))
                    except OSError:
                        self.multiLog("Cannot Symlink dissomniag.list")
                        raise dissomniag.taskManager.TaskFailed()
                    
                    #3d. Copy all chroot_local files
                    chrootLocalFilesDir = os.path.join(dissomniag.config.dissomniag.staticLiveFolder, "chroot_local-includes")
                    listings = os.listdir(chrootLocalFilesDir)
                    for infile in listings:
                        try:
                            shutil.copytree(os.path.join(chrootLocalFilesDir, infile), os.path.join(self.patternFolder, "config/includes.chroot/" + infile), symlinks = True)
                        except OSError:
                            src = os.path.join(chrootLocalFilesDir, infile)
                            dst = os.path.join(self.patternFolder, "config/includes.chroot/" + infile)
                            self.multiLog("Cannot copy an includes.chroot, src= %s , dst= %s" % (src,dst), log)
                    
                    #3e. Copy all chroot_local hooks
                    hooksFilesDir = os.path.join(dissomniag.config.dissomniag.staticLiveFolder, "hooks")
                    listings = os.listdir(hooksFilesDir)
                    for infile in listings:
                        try:
                            shutil.copy2(os.path.join(hooksFilesDir, infile), os.path.join(self.patternFolder, "config/hooks/"))
                        except OSError:
                            self.multiLog("Cannot copy an chroot_local-hook")
                            
                    tasksFilesDir = os.path.join(dissomniag.config.dissomniag.staticLiveFolder, "task-lists/")
                    listings = os.listdir(tasksFilesDir)
                    for infile in listings:
                        try:
                            shutil.copy2(os.path.join(tasksFilesDir, infile), os.path.join(self.patternFolder, "config/task-lists/"))
                        except OSError:
                            self.multiLog("Cannot copy an chroot_local-hook")
                    
                    #4. Install Live Daemon
                    
                    self.installLiveDaemon(self.patternFolder)
                    
                    #5. Copy needed files. (like OMNeT binaries)
                    
                    self.installOmnet(self.patternFolder)
                    
                    #5b Copy syslinux Debian package
                    packagesChrootStaticDir = os.path.join(dissomniag.config.dissomniag.staticLiveFolder, "packages.chroot")
                    listings = os.listdir(packagesChrootStaticDir)
                    for infile in listings:
                        try:
                            shutil.copy2(os.path.join(packagesChrootStaticDir, infile), os.path.join(self.patternFolder, "config/packages.chroot/"))
                        except OSError:
                            self.multiLog("Cannot copy packages.chroot")
                            
                    #6c Copy isolinux cfg
                    isolinuxCfgDir = os.path.join(dissomniag.config.dissomniag.staticLiveFolder, "includes.binary/isolinux")
                    try:
                        os.makedirs(os.path.join(self.patternFolder, "config/includes.binary/isolinux/"))
                    except OSError:
                        self.multiLog("Cannot create config/includes.binary/isolinux/")
                    listings = os.listdir(isolinuxCfgDir)
                    for infile in listings:
                        try:
                            shutil.copy2(os.path.join(isolinuxCfgDir, infile), os.path.join(self.patternFolder, "config/includes.binary/isolinux/"))
                        except OSError:
                            self.multiLog("Cannot copy includes.binary")
                      
                    #6. Init debian live environment
                    cmd = "lb config"
                    self.multiLog("running %s" % cmd)
                    ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
                    if ret != 0:
                        self.multiLog("LB Config error")
                        raise dissomniag.taskManager.TaskFailed() 
                    
                    #7. Make bootstrap
                    # Try 10 times (Solves some repository connection timeout problems)
                    cmd = "lb bootstrap"
                    self.multiLog("Run lb bootstrap", log)
                    ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
                    if ret != 0:
                        self.multiLog("LB bootstrap error")
                        raise dissomniag.taskManager.TaskFailed() 
                    
                    #8. Make chrooot
                    # Try 10 times (Solves some repository connection timeout problems)
                    cmd = "lb chroot"
                    self.multiLog("Run lb chroot", log)
                    ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
                    if ret != 0:
                        self.multiLog("LB chroot error")
                        raise dissomniag.taskManager.TaskFailed()
                    
                    #9. Make binary
                    # Try 10 times (Solves some repository connection timeout problems)
                    cmd = "lb binary"
                    self.multiLog("Run lb binary", log)
                    ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
                    if ret != 0:
                        self.multiLog("LB binary error")
                        raise dissomniag.taskManager.TaskFailed()   
                    
                    #8. 
                    #cmd = "lb build"
                    #self.multiLog("Run lb build", log)
                    #ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
                    #success = False
                    #for i in range(1, 11):
                    #    if self.job._getStatePrivate() == dissomniag.taskManager.jobs.JobStates.CANCELLED:
                    #        self.multiLog("Job cancelled. Initial LivdCD build failed. (lb build")
                    #        raise dissomniag.taskManager.TaskFailed("Job cancelled. Initial LivdCD build failed.")
                    #    
                    #    ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
                    #    if ret != 0:
                    #        self.multiLog("Initial LiveCD build failed. Retry %d" % i, log)
                    #        continue
                    #    else:
                    #        success = True
                    #        break
                    #if not success:
                    #   self.multiLog("Initial LiveCD build failed finally.", log)
                    #    raise dissomniag.taskManager.TaskFailed("Initial LiveCD build failed finally.")
                    
                    #8.
    
                    #7. Mark environment as Prepared
                    preparedFile = os.path.join(self.patternFolder, "CHECKED")
                    myFile = open(preparedFile, 'w')
                    myFile.write("CHECKED")
                    myFile.close()
                    self.infoObj.usable = True
                    self.infoObj.prepared = True
                    self.returnSuccess()
            finally:
                    if not dissomniag.resetDir():
                        self.multiLog("Cannot chdir to %s" % self.patternFolder, log)
                    
                    self.cleanUp()

    def revert(self):
        
        self.patternFolder = os.path.join(dissomniag.config.dissomniag.serverFolder,
                                dissomniag.config.dissomniag.liveCdPatternDirectory)
        self.chrootFolder = os.path.join(self.patternFolder, "chroot")
        with dissomniag.rootContext():
            self.cleanUp()
        return dissomniag.taskManager.TaskReturns.SUCCESS


class CreateLiveCd(dissomniag.taskManager.AtomicTask):
    
    def cleanUp(self):
        
        self.patternFolder = os.path.join(dissomniag.config.dissomniag.serverFolder, dissomniag.config.dissomniag.liveCdPatternDirectory)

        if not dissomniag.chDir(self.patternFolder):
                    self.multiLog("Cannot chdir to %s" % self.patternFolder, log)
                    raise dissomniag.taskManager.TaskFailed()
                
                        
        with dissomniag.rootContext():
            
            #Clean to binary
            cmd = "lb clean --binary"
            self.multiLog("running %s" % cmd)
            ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
            if ret != 0:
                self.multiLog("LB clean --binary error")
                #raise dissomniag.taskManager.TaskFailed()
        
            self.stageDir = os.path.join(self.patternFolder, ".build")
            self.binLocalInc = os.path.join(self.patternFolder, "config/includes.binary/")
            
            try:
                shutil.rmtree(self.binLocalInc)
            except (OSError, IOError) as e:
                pass
                
            try:
                os.makedirs(self.binLocalInc)
            except (OSError, IOError) as e:
                self.multiLog("Cannot recreate %s" % self.binLocalInc)
                
            isolinuxCfgDir = os.path.join(dissomniag.config.dissomniag.staticLiveFolder, "includes.binary/isolinux")
            try:
                os.makedirs(os.path.join(self.patternFolder, "config/includes.binary/isolinux/"))
            except OSError:
                self.multiLog("Cannot create config/includes.binary/isolinux/")
            listings = os.listdir(isolinuxCfgDir)
            for infile in listings:
                try:
                    shutil.copy2(os.path.join(isolinuxCfgDir, infile), os.path.join(self.patternFolder, "config/includes.binary/isolinux/"))
                except OSError:
                    self.multiLog("Cannot copy includes.binary")
    
            
            #if self.stageDir.endswith("/"):
            #    cmd = "rm %sbinary_disk %sbinary_checksums %sbinary_includes" % (self.stageDir, self.stageDir, self.stageDir)
            #else:
            #    cmd = "rm %s/binary_disk %s/binary_checksums %s/binary_includes" % (self.stageDir, self.stageDir, self.stageDir)
            #self.multiLog("exec %s" % cmd, log)
            #ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
            #if ret != 0:
            #    self.multiLog("Could not exec %s correctly" % cmd, log)
    
    def run(self):
        if (not hasattr(self.context, "LiveCd")):
            self.multiLog("No LiveCd Object in Context", log)
            raise dissomniag.taskManager.TaskFailed("No VM Object in Context")
        
        self.infoObj = dissomniag.model.LiveCdEnvironment()
        if not self.infoObj.prepared:
            self.multiLog("LiveCD Environment not prepared. No LiveCD creation possible!", log)
            raise dissomniag.taskManager.TaskFailed("LiveCD Environment not prepared. No LiveCD creation possible!")
        
        self.patternFolder = os.path.join(dissomniag.config.dissomniag.serverFolder,
                                dissomniag.config.dissomniag.liveCdPatternDirectory)
        
        with dissomniag.rootContext():
        
            try:
                
                if not dissomniag.chDir(self.patternFolder):
                    self.multiLog("Cannot chdir to %s" % self.patternFolder, log)
                    raise dissomniag.taskManager.TaskFailed()
                
                self.lockFile = os.path.join(self.patternFolder,
                                             dissomniag.config.dissomniag.patternLockFile)
                self.mylock = lockfile.FileLock(self.lockFile, threaded = True)
                
                with self.myLock:
                    
                    # 1. Copy infoXML
                    
                    self.versioningHash, self.liveInfoString = self.context.VM.getInfoXMLwithVersionongHash(self.job.getUser())
                    
                    with open("./config/includes.binary/liveInfo.xml") as f:
                        f.write(self.liveInfoString)
                        
                        
                    ###
                    #ToDo: At other thinks to binary include like Predefined Apps
                    ###
                    
                    #2. Make initial Build
                    # Try 10 times (Solves some repository connection timeout problems)
                    #cmd = "lb build"
                    #self.multiLog("Make initial build", log)
                    cmd = "lb binary"
                    self.multiLog("lb binary", log)
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
                    
                    #3. Copy iso to final Folder
                    # Check if folder for image exists
                    if not os.access(self.context.LiveCd.vm.getUtilityFolder(), os.F_OK):
                        os.makedirs(self.context.LiveCd.vm.getUtilityFolder())
                        
                    shutil.copy2("./binary.iso", self.context.LiveCd.vm.getLocalPathToCdImage(self.job.getUser()))
                    
                    with open(os.path.join(self.context.LiveCd.vm.getLocalUtilityFolder(), "configHash"), 'w') as f:
                        f.write(self.versioningHash)
                    
                    self.context.LiveCd.imageCreated = True
                
            finally:
                    if not dissomniag.resetDir():
                        self.multiLog("Cannot chdir to %s" % self.patternFolder, log)
                    
                    self.cleanUp()
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
            
    def revert(self):
        self.cleanUp()
        try:
            shutil.rmtree(os.path.join(self.context.LiveCd.vm.getUtilityFolder(), "configHash"))
        except OSError, IOError:
            pass
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    
class copyCdImage(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "liveCd"):
            self.multiLog("No LiveCd in Context", log)
            raise dissomniag.taskManager.TaskFailed("No LiveCd in Context")
        
        # 1. Check if Image on local hd exists
        if not os.access(self.context.liveCd.vm.getLocalPathToCdImage(self.job.getUser()), os.F_OK) or not os.access(os.path.join(self.context.liveCd.vm.getLocalUtilityFolder(self.job.getUser()), "configHash"), os.F_OK):
            
            self.multiLog("No local image exists for copy!")
            raise dissomniag.taskManager.TaskFailed("No local image exists for copy!")
        
        # 2. Create destination directory:
        cmd = "mkdir -p %s" % self.context.liveCd.vm.getRemoteUtilityFolder
        sshCmd = dissomniag.utils.SSHCommand(cmd, self.context.liveCd.vm.host.getMaintainanceIP(), self.context.liveCd.vm.host.administrativeUserName)
        ret, output = sshCmd.callAndGetOutput()
        self.multiLog("Creation of RemoteUtilityFolder with cmd %s results to: res: %d, output: %s" % (cmd, ret, output))
        
        # 3. Sync Files
        
        for i in range(1,5):
            rsyncCmd = dissomniag.utils.RsyncCommand(self.context.liveCd.vm.getLocalUtilityFolder(self.job.getUser()),\
                                                 self.context.liveCd.vm.getRemoteUtilityFolder(self.job.getUser()), \
                                                 self.context.liveCd.vm.host.getMaintainanceIP(), \
                                                 self.context.liveCd.vm.host.administrativeUserName)
            ret, output = rsyncCmd.callAndGetOutput()
            self.multiLog("Rsync LiveCD ret: %d, output: %s" % (ret, output), log)
            if ret == 0:
                break
            if i == 4 and ret != 0:
                self.context.liveCd.onRemoteUpToDate = False
                self.multiLog("Could not rsync LiveCd Image.", log)
                raise dissomniag.taskManager.TaskFailed("Could not rsync LiveCd Image.")
            
        self.context.liveCd.onRemoteUpToDate = True
        return dissomniag.taskManager.TaskReturns.SUCCESS
         

    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    

class deleteLiveCd(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "liveCd"):
            self.multiLog("deleteLiveCd: No LiveCd in Context", log)
            raise dissomniag.taskManager.TaskFailed("deleteLiveCd: No LiveCd in Context")
        
        # 1. Delete Local Image
        self.multiLog("Delete local LiveCd image.", log)
        try:
            shutil.rmtree(self.context.liveCd.vm.getLocalUtilityFolder(self.job.getUser()))
        except OSError:
            self.multiLog("Cannot delete local LiveCd image.", log)
            
        # 2. Delete Remote Image
        cmd = "rm -rf %s" % self.context.liveCd.vm.getRemoteUtilityFolder(self.job.getUser())
        sshCmd = dissomniag.utils.SSHCommand(cmd, \
                                             self.context.liveCd.vm.host.getMaintainanceIP(), \
                                             self.context.liveCd.vm.host.administrativeUserName)
        ret, output = sshCmd.callAndGetOutput()
        self.multiLog("Delete LiveCd image remote. ret: %d, output: %s" % (ret, output))
        
        session = dissomniag.Session()
    
        try:
            session.delete(self.context.liveCd)
            dissomniag.saveCommit(session)
        except Exception:
            failed = True
        else:
            failed = False
        
        if not failed:
            return dissomniag.taskManager.TaskReturns.SUCCESS
        else:
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class checkUptODateOnHd(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "liveCd"):
            self.multiLog("No LiveCd in Context", log)
            raise dissomniag.taskManager.TaskFailed("No LiveCd in Context")
        try:
            self.context.liveCd.checkOnHdUpToDate(self.job.getUser(), refresh = True)
        except Exception as e:
            self.multiLog(e.message, log)
            raise dissomniag.taskManager.TaskFailed(e.message)
            
        return dissomniag.taskManager.TaskReturns.SUCCESS        
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class checkUpToDateOnRemote(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "liveCd"):
            self.multiLog("No LiveCd in Context", log)
            raise dissomniag.taskManager.TaskFailed("No LiveCd in Context")
        
        self.cmd = "cat %s" % (os.path.join(self.context.liveCd.vm.getRemoteUtilityFolder, "configHash"))
        sshCmd = dissomniag.utils.SSHCommand(self.cmd, \
                                             self.context.liveCd.vm.host.getMaintainanceIP(), \
                                             self.context.liveCd.vm.host.administrativeUserName)
        ret, myHash = sshCmd.callAndGetOutput()
        if ret == 0 and myHash == self.context.hashConfig(self.job.getUser()):
            self.context.LiveCd.onRemoteUpToDate = True
        else:
            self.context.LiveCd.onRemoteUpToDate = False
            
        return dissomniag.taskManager.TaskReturns.SUCCESS 
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class addAllCurrentAppsOnRemote(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "liveCd"):
            self.multiLog("No LiveCd in Context", log)
            raise dissomniag.taskManager.TaskFailed("No LiveCd in Context")
        
        try:
            self.multiLog("Try to add all current apps on Remote", log)
            self.context.liveCd.addAllCurrentAppsOnRemote(self.job.getUser())
        except Exception as e:
            self.multiLog("Try to add all current apps on Remote FAILED: %s" % str(e), log)
            
        return dissomniag.taskManager.TaskReturns.SUCCESS 
        
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS