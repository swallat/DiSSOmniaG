# -*- coding: utf-8 -*-
"""
Created on 31.08.2011

@author: Sebastian Wallat
"""
import os
import apt
import dissomniag

class LiveCdEnvironmentChecks(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        infoObj = dissomniag.model.LiveCdEnvironment()
        
        #1. Check if Utility Folder exists
        if not os.access(dissomniag.config.dissomniag.utilityFolder, os.F_OK):
            try:
                os.mkdir(dissomniag.config.dissomniag.utilityFolder)
            except OSError:
                infoObj.errorInfo.append("Could not create utility folder.")
                infoObj.usable = False
                self.job.trace(infoObj.getErrorInfo())
                raise dissomniag.taskManager.UnrevertableFailure()
            
        #2 Check if Utility Folder is writable
        if not os.access(dissomniag.config.dissomniag.utilityFolder, os.W_OK):
            infoObj.errorInfo.append("Utility Folder is not writable.")
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
            raise dissomniag.taskManager.UnrevertableFailure()
            
        if execInstall:
            if cache.commit(apt.progress.TextFetchProgress(), 
                         apt.progress.InstallProgress()):
                infoObj.usable = True
                return dissomniag.taskManager.TaskReturns.SUCCESS
            else:
                infoObj.error.append("Installation Error!")
                infoObj.usable = False
                self.job.trace(infoObj.getErrorInfo())
                raise dissomniag.taskManager.UnrevertableFailure()
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()

