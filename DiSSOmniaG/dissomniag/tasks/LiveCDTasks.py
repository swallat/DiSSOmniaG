# -*- coding: utf-8 -*-
"""
Created on 31.08.2011

@author: Sebastian Wallat
"""
import os, shutil, subprocess, shlex
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
        
        if os.access(checkedFile, os.F_OK):
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
                dissomniag.getRoot()
                shutil.rmtree(self.patternFolder)
            except OSError, e:
                self.multiLog("Could not delete Pattern folder. %s" % e)
                self.infoObj.usable = False
                raise dissomniag.taskManager.UnrevertableFailure()
            finally:
                dissomniag.resetPermissions()
            
        try:
            os.mkdir(self.patternFolder)
            os.chown(self.patternFolder,
                     dissomniag.config.dissomniag.userId,
                     dissomniag.config.dissomniag.groupId)
        except OSError:
            self.multiLog("Could not LiveCD pattern folder.")
            self.infoObj.usable = False
            raise dissomniag.taskManager.UnrevertableFailure()
    
    def createChrootFolder(self):
        if os.access(self.chrootFolder, os.F_OK):
            shutil.rmtree(self.patternFolder)
            
        try:
            os.mkdir(self.chrootFolder)
            os.chown(self.chrootFolder,
                     dissomniag.config.dissomniag.userId,
                     dissomniag.config.dissomniag.groupId)
        except OSError:
            self.multiLog("Could not LiveCD pattern folder.")
            self.infoObj.usable = False
            raise dissomniag.taskManager.UnrevertableFailure()
        
    def debootStrap(self):
        arch = "amd64"
        release = "stable"

        debootCmd = "debootstrap --arch=%s %s %s" % (arch, release, self.chrootFolder)
        self.multiLog("Running %s" % debootCmd)
        
        dissomniag.getRoot()
        proc = self.callSubprocessAndLog(debootCmd, log)
        
        if proc.returncode != 0:
            self.multiLog("Could not run debootstrap.")
            dissomniag.resetPermissions()
            raise dissomniag.taskManager.TaskFailed("Could not run debootstrap")
        
        self.multiLog("debootstrab success")
        
    def cleanUp(self):
        
        #1. Delete Machine Id
        cmd = "chroot %s rm /var/lib/dbus/machine-id" % self.chrootFolder
        self.multiLog("Running %s" % cmd)
        proc = self.callSubprocessAndLog(cmd, log)
        
        if proc.returncode != 0:
            self.multiLog("Cmd Failure %s Returncode: %d" % (cmd, proc.returncode), log)
        
        #2. Remove /sbin/initctl
        cmd = "chroot %s dpkg-divert --rename --remove /sbin/initctl" % self.chrootFolder
        self.multiLog("Running %s" % cmd)
        proc = self.callSubprocessAndLog(cmd, log)
        
        if proc.returncode != 0:
            self.multiLog("Cmd Failure %s Returncode: %d" % (cmd, proc.returncode), log)
        
        #3. Make apt-clean
        cmd = "chroot %s apt-get clean" % self.chrootFolder
        self.multiLog("Running %s" % cmd)
        proc = self.callSubprocessAndLog(cmd, log)
        
        if proc.returncode != 0:
            self.multiLog("Cmd Failure %s Returncode: %d" % (cmd, proc.returncode), log)
            
        #4. Delete /tmp
        cmd = "chroot %s rm -rf /tmp/*" % self.chrootFolder
        self.multiLog("Running %s" % cmd)
        proc = self.callSubprocessAndLog(cmd, log)
        
        if proc.returncode != 0:
            self.multiLog("Cmd Failure %s Returncode: %d" % (cmd, proc.returncode), log)
            
        #5. Remove /etc/resolv.conf
        cmd = "chroot %s rm /etc/resolv.conf" % self.chrootFolder
        self.multiLog("Running %s" % cmd)
        proc = self.callSubprocessAndLog(cmd, log)
        
        if proc.returncode != 0:
            self.multiLog("Cmd Failure %s Returncode: %d" % (cmd, proc.returncode), log)
            
        #6. Umount /proc
        cmd = "chroot %s umount -lf /proc" % self.chrootFolder
        self.multiLog("Running %s" % cmd)
        proc = self.callSubprocessAndLog(cmd, log)
        
        if proc.returncode != 0:
            self.multiLog("Cmd Failure %s Returncode: %d" % (cmd, proc.returncode), log)
            
        #7. Umount /sys
        cmd = "chroot %s umount -lf /sys" % self.chrootFolder
        self.multiLog("Running %s" % cmd)
        proc = self.callSubprocessAndLog(cmd, log)
        
        if proc.returncode != 0:
            self.multiLog("Cmd Failure %s Returncode: %d" % (cmd, proc.returncode), log)
            
        #8. Umount /dev/pts
        cmd = "chroot %s umount -lf /dev/pts" % self.chrootFolder
        self.multiLog("Running %s" % cmd)
        proc = self.callSubprocessAndLog(cmd, log)
        
        if proc.returncode != 0:
            self.multiLog("Cmd Failure %s Returncode: %d" % (cmd, proc.returncode), log)
            
        #9. Umount /dev
        cmd = "umount -l %s/dev" % self.chrootFolder
        self.multiLog("Running %s" % cmd)
        proc = self.callSubprocessAndLog(cmd, log)
        
        if proc.returncode != 0:
            self.multiLog("Cmd Failure %s Returncode: %d" % (cmd, proc.returncode), log)
            
        self.multiLog("Cleanup completed.")
        
    def callStandardOnCmdHandler(self, cmd, cmdHandler):
        self.multiLog("Running %s" % cmd, log)
        ret = cmdHandler.callCmd(cmd)
        if ret != 0:
            self.multiLog("Cannot %s" % cmd, log)
            dissomniag.resetPermissions()
            cmdHandler.close()
            raise dissomniag.taskManager.TaskFailed("Cannot %s" % cmd)
        
        
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
        
        #self.checkIfPatternFolderExists()
        
        #2. Create chroot folder
        self.chrootFolder = os.path.join(self.patternFolder, "chroot")
        #self.createChrootFolder()
        
        raise dissomniag.taskManager.TaskFailed()
        #3. Debootstrab in chroot directory
        #self.debootStrap()
        
        #4. Prepare the chroot folder to install packages
        
        # a) Mount /dev
        devDir = os.path.join(self.chrootFolder, "dev")
        cmd = "mount --bind /dev %s" % devDir
        self.multiLog("Running %s" % cmd)
        
        proc = self.callSubprocessAndLog(cmd, log)
        
        if proc.returncode != 0:
            self.multiLog("Could not mount /dev.")
            dissomniag.resetPermissions()
            raise dissomniag.taskManager.TaskFailed("Could not mount /dev.")
        
        # b) copy /etc/hosts
        
        try:
            shutil.copy2("/etc/hosts", os.path.join(self.chrootFolder, "etc/"))
        except IOError, e:
            self.multiLog("Could not copy /etc/hosts. %s" % e)
            dissomniag.resetPermissions()
            raise dissomniag.taskManager.TaskFailed("Could not copy /etc/hosts. %s" % e)
        
        # c) copy /etc/resolv.conf
        
        try:
            shutil.copy2("/etc/resolv.conf", os.path.join(self.chrootFolder, "etc/"))
        except IOError, e:
            self.multiLog("Could not copy /etc/resolv.conf. %s" % e)
            dissomniag.resetPermissions()
            raise dissomniag.taskManager.TaskFailed("Could not copy /etc/resolv.conf. %s" % e)
        
        # d) copy /etc/apt/sources.list
        
        try:
            shutil.copy2("/etc/apt/sources.list", os.path.join(self.chrootFolder, "etc/apt/"))
        except IOError, e:
            self.multiLog("Could not copy /etc/apt/sources.list. %s" % e)
            dissomniag.resetPermissions()
            raise dissomniag.taskManager.TaskFailed("Could not copy /etc/apt/sources.list. %s" % e)
        
        
        # e) mount /proc in chroot Environment
        
        cmd = "chroot %s mount none -t proc /proc" % self.chrootFolder
        self.multiLog("Running %s" % cmd)
        
        proc = self.callSubprocessAndLog(cmd, log)
        
        if proc.returncode != 0:
            self.multiLog("Could not mount /proc.")
            dissomniag.resetPermissions()
            raise dissomniag.taskManager.TaskFailed("Could not mount /proc.")
        
        # f) mount /sys in chroot Environment
        
        cmd = "chroot %s mount none -t sysfs /sys" % self.chrootFolder
        log.info("Running %s" % cmd)
        
        proc = self.callSubprocessAndLog(cmd, log)
        
        if proc.returncode != 0:
            self.multiLog("Could not mount /sys.")
            dissomniag.resetPermissions()
            raise dissomniag.taskManager.TaskFailed("Could not mount /sys.")
        
        # g) mount /dev/pts in chroot Environment
        
        cmd = "chroot %s mount none -t devpts /dev/pts" % self.chrootFolder
        self.multiLog("Running %s" % cmd)
        
        proc = self.callSubprocessAndLog(cmd, log)
        
        if proc.returncode != 0:
            self.multiLog("Could not mount /dev/pts.")
            dissomniag.resetPermissions()
            raise dissomniag.taskManager.TaskFailed("Could not mount /dev/pts.")
        
        
        #5. Install main components
        
        # Create SubprocessCommand
        cmdHandler = dissomniag.utils.InteractiveCommand("chroot %s" % self.chrootFolder, log)
        cmdHandler.init()
        
        # a) export HOME
        self.callStandardOnCmdHandler("export HOME=/root", cmdHandler)
        
        # b) export LC_ALL
        self.callStandardOnCmdHandler("export LC_ALL=de_DE.utf8", cmdHandler)
        
        # c) export LANG
        self.callStandardOnCmdHandler("export LANG=de_DE.utf8", cmdHandler)
        
        # d) add apt key
        self.callStandardOnCmdHandler("apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 12345678", cmdHandler)
        
        # e) add apt update
        self.callStandardOnCmdHandler("apt-get update", cmdHandler)
        
        # f) add install dbus
        self.callStandardOnCmdHandler("apt-get install --yes dbus", cmdHandler)
        
        # g) create dbus uuid
        self.callStandardOnCmdHandler("dbus-uuidgen > /var/lib/dbus/machine-id", cmdHandler)
        
        # h) create add /sbin/initctl
        self.callStandardOnCmdHandler("dpkg-divert --local --rename --add /sbin/initctl", cmdHandler)
        
        # i) Install standard environment
        self.callStandardOnCmdHandler("apt-get install --yes ubuntu-standard casper lupin-casper", cmdHandler)
        
        # j) Install additions a
        self.callStandardOnCmdHandler("apt-get install --yes discover1 laptop-detect os-prober", cmdHandler)
        
        # k) Install additions b
        self.callStandardOnCmdHandler("apt-get install --yes linux-generic", cmdHandler)
        
        # l) Install additions c
        self.callStandardOnCmdHandler("apt-get install --yes grub2 plymouth-x11", cmdHandler)
        
        # m) Install additions d
        self.callStandardOnCmdHandler("apt-get install --yes ubuntu-desktop language-selector language-pack-de language-pack-de-base language-support-de", cmdHandler)
        
        # n) Close cmdHandler
        cmdHandler.close()
        
        #6. Leave the chroot environment and cleanup
        self.cleanUp()
        
        dissomniag.resetPermissions()
        
        
            
        
        
    
    def revert(self):
        
        self.patternFolder = os.path.join(dissomniag.config.dissomniag.serverFolder,
                                dissomniag.config.dissomniag.liveCdPatternDirectory)
        self.chrootFolder = os.path.join(self.patternFolder, "chroot")
        dissomniag.getRoot()
        self.cleanUp()
        dissomniag.resetPermissions()
        return dissomniag.taskManager.TaskReturns.SUCCESS
