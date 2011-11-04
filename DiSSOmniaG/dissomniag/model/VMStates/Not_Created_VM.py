'''
Created on 01.11.2011

@author: Sebastian Wallat
'''
import lockfile
import os
import shutil
import dissomniag

import logging

log = logging.getLogger("model.VMStates.Not_Created_VM")

class Not_Created_VM(dissomniag.model.VMStates.AbstractVMState):
    '''
    classdocs
    '''
    def test(self, job):
        job.trace("VM in correct state.")
        return True
    
    def prepare(self, job):
        self.infoObj = dissomniag.model.LiveCdEnvironment()
        if not self.infoObj.prepared:
            job.trace("LiveCD Environment not prepared. No LiveCD creation possible!")
            self.vm.changeState(dissomniag.model.NodeState.PREPARE_ERROR)
            raise dissomniag.taskManager.TaskFailed("LiveCD Environment not prepared. No LiveCD creation possible!")
        
        self.patternFolder = os.path.join(dissomniag.config.dissomniag.serverFolder, dissomniag.config.dissomniag.liveCdPatternDirectory)
        
        dissomniag.getRoot()
        
        try:
            
            if not dissomniag.chDir(self.patternFolder):
                job.trace("Cannot chdir to %s" % self.patternFolder)
                self.vm.changeState(dissomniag.model.NodeState.PREPARE_ERROR)
                raise dissomniag.taskManager.TaskFailed("Could not change to pattern folder.")
            
            self.lockFile = os.path.join(self.patternFolder, dissomniag.config.dissomniag.patternLockFile)
            self.mylock = lockfile.FileLock(self.lockFile, threaded = True)
            
            with self.myLock:
                
                # 1. Copy infoXML
                
                self.versioningHash, self.liveInfoString = self.vm.liveCd.getInfoXMLwithVersionongHash(job.getUser())
                
                with open("./config/binary_local-includes/liveInfo.xml") as f:
                    f.write(self.liveInfoString)
                    
                    
                ###
                #ToDo: At other thinks to binary include like Predefined Apps
                ###
                
                #2. Make initial Build
                # Try 10 times (Solves some repository connection timeout problems)
                cmd = "lb build"
                job.trace("Make initial Build")
                success = False
                for i in range(1, 11):
                    if job._getStatePrivate() == dissomniag.taskManager.jobs.JobStates.CANCELLED:
                        job.trace("Job cancelled. Initial LivdCD build failed.")
                        self.vm.changeState(dissomniag.model.NodeState.PREPARE_ERROR)
                        raise dissomniag.taskManager.TaskFailed("Job cancelled. Initial LivdCD build failed.")
                    
                    ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
                    if ret != 0:
                        job.trace("Initial LiveCD build failed. Retry %d" % i)
                        continue
                    else:
                        success = True
                        break
                if not success:
                    job.trace("Initial LiveCD build failed finally.")
                    self.vm.changeState(dissomniag.model.NodeState.PREPARE_ERROR)
                    raise dissomniag.taskManager.TaskFailed("Initial LiveCD build failed finally.")
                
                #3. Copy iso to final Folder
                # Check if folder for image exists
                if not os.access(self.context.LiveCd.vm.getUtilityFolder(), os.F_OK):
                    os.makedirs(self.context.LiveCd.vm.getUtilityFolder())
                    
                shutil.copy2("./binary.iso", self.context.LiveCd.vm.getLocalPathToCdImage(self.job.getUser()))
                
                with open(os.path.join(self.context.LiveCd.vm.getLocalUtilityFolder(), "configHash"), 'w') as f:
                    f.write(self.versioningHash)
                
                self.vm.liveCd.imageCreated = True
            
        finally:
                if not dissomniag.resetDir():
                    job.trace("Cannot chdir to %s" % self.patternFolder)
                dissomniag.resetPermissions()
                
                self.cleanUpPrepare()
        
        job.trace("LiveCd Image created.")
        self.vm.changeState(dissomniag.model.NodeState.CREATED)
        return True
    
    def deploy(self, job):#
        if self.prepare(job):
            self.vm.runningJob.deploy(job)
        else:
            return False
    
    def start(self, job):
        if self.prepare(job):
            self.vm.runningJob.start(job)
        else:
            return False
    
    def stop(self, job):
        return True
    
    def sanityCheck(self, job):
        return True
    
    def reset(self, job):
        return True
    
    
    def cleanUpPrepare(self, job):
        
        self.patternFolder = os.path.join(dissomniag.config.dissomniag.serverFolder, dissomniag.config.dissomniag.liveCdPatternDirectory)
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
            self.multiLog("Could not exec %s correctly" % cmd, job, log)
        
        if self.stageDir.endswith("/"):
            cmd = "rm %sbinary_iso %sbinary_checksums %sbinary_local-includes" % (self.stageDir, self.stageDir, self.stageDir)
        else:
            cmd = "rm %s/binary_iso %s/binary_checksums %s/binary_local-includes" % (self.stageDir, self.stageDir, self.stageDir)
        self.multiLog("exec %s" % cmd, log)
        ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
        if ret != 0:
            self.multiLog("Could not exec %s correctly" % cmd, job, log)
        dissomniag.resetPermissions()
        return True
        