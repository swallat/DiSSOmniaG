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
import lockfile
import thread
import os
import shutil
import dissomniag
from dissomniag.model.VMStates import *

import logging

log = logging.getLogger("model.VMStates.Not_Created_VM")

class Not_Created_VM(AbstractVMState):
    '''
    classdocs
    '''
    def test(self, job):
        self.multiLog("VM in correct state.", job, log)
        return True
    
    def prepare(self, job):
        self.infoObj = dissomniag.model.LiveCdEnvironment()
        if not self.infoObj.prepared:
            self.multiLog("LiveCD Environment not prepared. No LiveCD creation possible!", job, log)
            self.vm.changeState(dissomniag.model.NodeState.PREPARE_ERROR)
            raise dissomniag.taskManager.TaskFailed("LiveCD Environment not prepared. No LiveCD creation possible!")
        
        self.patternFolder = os.path.join(dissomniag.config.dissomniag.serverFolder, dissomniag.config.dissomniag.liveCdPatternDirectory)
        
        with dissomniag.rootContext():
            try:
                
                if not dissomniag.chDir(self.patternFolder):
                    self.multiLog("Cannot chdir to %s" % self.patternFolder, job, log)
                    self.vm.changeState(dissomniag.model.NodeState.PREPARE_ERROR)
                    raise dissomniag.taskManager.TaskFailed("Could not change to pattern folder.")
                
                self.lockFile = os.path.join(self.patternFolder, dissomniag.config.dissomniag.patternLockFile)
                self.myLock = lockfile.FileLock(self.lockFile, threaded = True)
                
                with self.myLock:
                    
                    # 1. Copy infoXML
                    self.liveInfoString, self.versioningHash = self.liveCd.getInfoXMLwithVersionongHash(job.getUser())
                    lifeInfoFile = os.path.join(self.patternFolder, "config/includes.binary/liveInfo.xml")
                    self.multiLog(str(lifeInfoFile), job, log)
                    with open(lifeInfoFile, 'w') as f:
                        f.write(self.liveInfoString)
                        
                        
                    ###
                    #ToDo: At other thinks to binary include like Predefined Apps
                    ###
                    
                    #2. Make initial Build
                    # Try 10 times (Solves some repository connection timeout problems)
                    #cmd = "lb build"
                    #self.multiLog("Make initial Build", job, log)
                    cmd = "lb binary"
                    self.multiLog("lb binary", job, log)
                    success = False
                    for i in range(1, 11):
                        if job._getStatePrivate() == dissomniag.taskManager.jobs.JobStates.CANCELLED:
                            self.multiLog("Job cancelled. Initial LivdCD build failed.", job, log)
                            self.vm.changeState(dissomniag.model.NodeState.PREPARE_ERROR)
                            raise dissomniag.taskManager.TaskFailed("Job cancelled. Initial LivdCD build failed.")
                        
                        ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
                        if ret != 0:
                            self.multiLog("Initial LiveCD build failed. Retry %d" % i, job, log)
                            continue
                        else:
                            success = True
                            break
                    if not success:
                        self.multiLog("Initial LiveCD build failed finally.", job, log)
                        self.vm.changeState(dissomniag.model.NodeState.PREPARE_ERROR)
                        raise dissomniag.taskManager.TaskFailed("Initial LiveCD build failed finally.")
                    
                    #3. Copy iso to final Folder
                    # Check if folder for image exists
                    if not os.access(self.vm.getLocalUtilityFolder(job.getUser()), os.F_OK):
                        os.makedirs(self.vm.getLocalUtilityFolder(job.getUser()))
                    shutil.copy2("./binary.iso", self.vm.getLocalPathToCdImage(job.getUser()))
                    
                    with open(os.path.join(self.vm.getLocalUtilityFolder(job.getUser()), "configHash"), 'w') as f:
                        f.write(self.versioningHash)
                    
                    self.liveCd.imageCreated = True
                
            finally:
                    if not dissomniag.resetDir():
                        self.multiLog("Cannot chdir to %s" % self.patternFolder, job, log)
                    
                    self.cleanUpPrepare(job)
        
        self.multiLog("LiveCd Image created.", job, log)
        self.vm.changeState(dissomniag.model.NodeState.PREPARED)
        return True
    
    def deploy(self, job):#
        if self.prepare(job):
            self.vm.runningState.deploy(job)
        else:
            return False
    
    def start(self, job):
        if self.prepare(job):
            self.vm.runningState.start(job)
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
            #
            #if self.stageDir.endswith("/"):
            #    cmd = "rm %sbinary_disk %sbinary_checksums %sbinary_includes" % (self.stageDir, self.stageDir, self.stageDir)
            #else:
            #    cmd = "rm %s/binary_disk %s/binary_checksums %s/binary_includes" % (self.stageDir, self.stageDir, self.stageDir)
            #self.multiLog("exec %s" % cmd, job, log)
            #ret, output = dissomniag.utils.StandardCmd(cmd, log).run()
            #if ret != 0:
            #    self.multiLog("Could not exec %s correctly" % cmd, job, log)
        return True
        