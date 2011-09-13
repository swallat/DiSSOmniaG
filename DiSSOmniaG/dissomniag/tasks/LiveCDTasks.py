# -*- coding: utf-8 -*-
"""
Created on 31.08.2011

@author: Sebastian Wallat
"""
import os, shutil
import apt
import dissomniag

import logging

log = logging.getLogger("tasks.LiveCDTasks")

class LiveCdEnvironmentChecks(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        
        infoObj = dissomniag.model.LiveCdEnvironment()
        
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
                infoObj.errorInfo.append("Could not create utility folder. %s" % e)
                infoObj.usable = False
                self.job.trace(infoObj.getErrorInfo())
                raise dissomniag.taskManager.UnrevertableFailure()
            finally:
                dissomniag.resetPermissions()
            
        #2 Check if Utility Folder is writable
        if not os.access(dissomniag.config.dissomniag.utilityFolder, os.W_OK):
            infoObj.errorInfo.append("Utility Folder is not writable.")
            infoObj.usable = False
            self.job.trace(infoObj.getErrorInfo())
            raise dissomniag.taskManager.UnrevertableFailure()
        
        if not os.access(dissomniag.config.dissomniag.serverFolder, os.W_OK):
            infoObj.errorInfo.append("Server Folder is not writable.")
            infoObj.usable = False
            self.job.trace(infoObj.getErrorInfo())
            raise dissomniag.taskManager.UnrevertableFailure()
        
        #3. Check if server has root permissions
        if not os.getuid() == 0:
            infoObj.errorInfo.append("The server needs root privileges to create live cd's.")
            infoObj.usable = False
            self.job.trace(infoObj.getErrorInfo())
            raise dissomniag.taskManager.UnrevertableFailure()
        
        #4. Check if all utilities to create live cd's are installed. Try to install them.
        cache = apt.Cache()
        
        execInstall = False
        try:
            dissomniag.getRoot()
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
            infoObj.error.append("A apt package is not available!")
            infoObj.usable = False
            self.job.trace(infoObj.getErrorInfo())
            dissomniag.resetPermissions()
            raise dissomniag.taskManager.UnrevertableFailure()
            
        if execInstall:
            if cache.commit(apt.progress.TextFetchProgress(),
                         apt.progress.InstallProgress()):
                infoObj.usable = True
                dissomniag.resetPermissions()
                return dissomniag.taskManager.TaskReturns.SUCCESS
            else:
                infoObj.error.append("Installation Error!")
                infoObj.usable = False
                self.job.trace(infoObj.getErrorInfo())
                dissomniag.resetPermissions()
                raise dissomniag.taskManager.UnrevertableFailure()
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()
    
class CheckLiveCdEnvironmentPrepared(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        infoObj = dissomniag.model.LiveCdEnvironment()
        
        patternFolder = os.path.join(dissomniag.config.dissomniag.serverFolder,
                                dissomniag.config.dissomniag.liveCdPatternDirectory)
        
        checkedFile = os.path.join(patternFolder, "CHECKED")
        
        if os.access(checkedFile, os.F_OK):
            infoObj.prepared = True
        else:
            infoObj.prepared = False
            
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS

class PrepareLiveCdEnvironment(dissomniag.taskManager.AtomicTask):
    
    def returnSuccess(self):
        log.info("LiveCD Environment prepared")
        self.job.trace("LiveCD Environment prepared")
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def run(self):
        infoObj = dissomniag.model.LiveCdEnvironment()
        if infoObj.prepared:
            return self.returnSuccess()
        
        #If the Environment is not prepared, create it.
        
        #1. Check if Pattern folder exists. 
        #    True: Delete, and recreate it
        #    False: just create it
        
        patternFolder = os.path.join(dissomniag.config.dissomniag.serverFolder,
                                dissomniag.config.dissomniag.liveCdPatternDirectory)
        
        if os.access(patternFolder, os.F_OK):
            shutil.rmtree(patternFolder)
            
        try:
            os.mkdir(patternFolder)
            os.chown(patternFolder,
                     dissomniag.config.dissomniag.userId,
                     dissomniag.config.dissomniag.groupId)
        except OSError:
            infoObj.errorInfo.append("Could not LiveCD pattern folder.")
            infoObj.usable = False
            self.job.trace(infoObj.getErrorInfo())
            raise dissomniag.taskManager.UnrevertableFailure()
        
                    
        
    
    def revert(self):
        pass
