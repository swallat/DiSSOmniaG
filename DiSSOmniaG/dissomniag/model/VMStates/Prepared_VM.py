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
import shutil
import dissomniag
from dissomniag.model.VMStates import *

import logging

log = logging.getLogger("model.VMStates.Prepared_VM")

class Prepared_VM(AbstractVMState):
    '''
    classdocs
    '''
    
    def test(self, job):
        try:
            upToDate = self.liveCd.checkOnHdUpToDate(job.getUser(), refresh = True)
        except Exception as e:
            job.trace(str(e))
            self.vm.changeState(dissomniag.model.NodeState.PREPARE_ERROR)
            return self.vm.runningState.sanityCheck(job)
        else:
            if upToDate:
                job.trace("VM in correct state!")
                return True
            else:
               self.vm.changeState(dissomniag.model.NodeState.PREPARE_ERROR)
               return self.vm.runningState.sanityCheck(job)
    
    def prepare(self, job):
        job.trace("VM already created.")
        return True
    
    def deploy(self, job):
        # 1. Check if Image on local hd exists
        if not os.access(self.vm.getLocalPathToCdImage(job.getUser()), os.F_OK) or not os.access(os.path.join(self.vm.getLocalUtilityFolder(job.getUser()), "configHash"), os.F_OK):
            
            self.multiLog("No local image exists for copy!", job, log)
            self.vm.changeState(dissomniag.model.NodeState.DEPLOY_ERROR)
            raise dissomniag.taskManager.TaskFailed("No local image exists for copy!", job, log)
        
        # 2. Create destination directory:
        cmd = "mkdir -p %s" % self.vm.getRemoteUtilityFolder(job.getUser())
        sshCmd = dissomniag.utils.SSHCommand(cmd, self.vm.host.getMaintainanceIP().addr, self.vm.host.administrativeUserName)
        ret, output = sshCmd.callAndGetOutput()
        self.multiLog("Creation of RemoteUtilityFolder with cmd %s results to: res: %d, output: %s" % (cmd, ret, output), job, log)
        
        # 3. Sync Files
        
        for i in range(1,3):
            rsyncCmd = dissomniag.utils.RsyncCommand(self.vm.getLocalUtilityFolder(job.getUser()),\
                                                 os.path.join(self.vm.host.utilityFolder, dissomniag.config.hostConfig.vmSubdirectory), \
                                                 self.vm.host.getMaintainanceIP().addr, \
                                                 self.vm.host.administrativeUserName)
            ret, output = rsyncCmd.callAndGetOutput()
            self.multiLog("Rsync LiveCD ret: %d, output: %s" % (ret, output), job, log)
            if ret == 0:
                break
            if i == 2 and ret != 0:
                self.liveCd.onRemoteUpToDate = False
                self.multiLog("Could not rsync LiveCd Image.", job, log)
                self.vm.changeState(dissomniag.model.NodeState.DEPLOY_ERROR)
                raise dissomniag.taskManager.TaskFailed("Could not rsync LiveCd Image.")
            
        self.liveCd.onRemoteUpToDate = True
        self.vm.changeState(dissomniag.model.NodeState.DEPLOYED)
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def start(self, job):
        if self.deploy(job):
            return self.vm.runningState.start(job)
        else:
            return False
    
    def stop(self, job):
        return True
    
    def sanityCheck(self, job):
        return True
    
    def reset(self, job):
        # 1. Delete Local Image
        self.multiLog("Delete local LiveCd image.", job, log)
        self.multiLog("Rmtree %s" % self.vm.getLocalUtilityFolder(job.getUser()), job, log)
        with dissomniag.rootContext():
            try:
                shutil.rmtree(self.vm.getLocalUtilityFolder(job.getUser()))
            except (IOError, OSError) as e:
                self.multiLog("Cannot delete local LiveCd image. LocalFolder: %s " % self.vm.getLocalUtilityFolder(job.getUser()), job, log)
                self.vm.changeState(dissomniag.model.NodeState.NOT_CREATED)
            else:
                self.vm.changeState(dissomniag.model.NodeState.NOT_CREATED)
        return True
    
    def cleanUpDeploy(self, job):    
        # 1. Delete Remote Image
        cmd = "rm -rf %s" % self.vm.getRemoteUtilityFolder(job.getUser())
        sshCmd = dissomniag.utils.SSHCommand(cmd, \
                                             self.vm.host.getMaintainanceIP().addr, \
                                             self.vm.host.administrativeUserName)
        ret, output = sshCmd.callAndGetOutput()
        self.multiLog("Delete LiveCd image remote. ret: %d, output: %s" % (ret, output), job, log)
        self.vm.changeState(dissomniag.model.NodeState.PREPARED)
        if ret != 0:
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        else:
            return dissomniag.taskManager.TaskReturns.SUCCESS