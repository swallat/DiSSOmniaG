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
import libvirt
import dissomniag
from dissomniag.model.VMStates import *

import logging

log = logging.getLogger("model.VMStates.Deployed_VM")

class Deployed_VM(AbstractVMState):
    '''
    classdocs
    '''
    def test(self, job):
        cmd = "cat %s" % (os.path.join(self.vm.getRemoteUtilityFolder(job.getUser()), "configHash"))
        sshCmd = dissomniag.utils.SSHCommand(cmd, \
                                             self.vm.host.getMaintainanceIP().addr, \
                                             self.vm.host.administrativeUserName)
        ret, myHash = sshCmd.callAndGetOutput()
        if ret == 0 and str(myHash[0]) == str(self.liveCd.hashConfig(job.getUser())):
            self.liveCd.onRemoteUpToDate = True
            job.trace("VM in correct state!")
            return True
        else:
            self.liveCd.onRemoteUpToDate = False
            job.trace("VM not deployed!remoteHash: %s localHash: %s Compared: %s" % (str(myHash[0]), str(self.liveCd.hashConfig(job.getUser())), str(str(myHash[0]) == str(self.liveCd.hashConfig(job.getUser())))))
            self.vm.changeState(dissomniag.model.NodeState.DEPLOY_ERROR)
            return self.vm.runningState.sanityCheck(job)

    def prepare(self, job):
        job.trace("VM already prepared!")
        return True
        
    def deploy(self, job):
        return True
    
    def start(self, job):
        try:
            con = libvirt.open(str(self.vm.host.qemuConnector))
        except libvirt.libvirtError:
            self.vm.changeState(dissomniag.model.NodeState.DEPLOY_ERROR)
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            vm = con.createXML(self.vm.getLibVirtString(job.getUser()), 0)
        except libvirt.libvirtError:
            job.trace("CreateVM: Could not create vm. The network is already created or there is an error.")
            try:
                vm = con.lookupByName(self.vm.commonName)
                vm.destroy()
            except libvirt.libvirtError:
                pass
            
            job.trace("CreateVM: Could not create a vm.")
            self.vm.changeState(dissomniag.model.NodeState.RUNTIME_ERROR)
            raise dissomniag.taskManager.TaskFailed("Could Not Create VM!")
        finally:
            con.close()
        
        job.trace("VM created!")
        self.vm.changeState(dissomniag.model.NodeState.CREATED)
        return True
    
    def stop(self, job):
        return True
    
    def sanityCheck(self, job):
        return True
    
    def reset(self, job):
        cmd = "rm -rf %s" % self.vm.getRemoteUtilityFolder(job.getUser())
        sshCmd = dissomniag.utils.SSHCommand(cmd, self.vm.host.getMaintainanceIP().addr, self.vm.host.administrativeUserName)
        ret, output = sshCmd.callAndGetOutput()
        self.multiLog("Deletion of RemoteUtilityFolder with cmd %s results to: res: %d, output: %s" % (cmd, ret, output), job, log)
        
        self.vm.changeState(dissomniag.model.NodeState.PREPARED)
        return self.vm.runningState.reset(job)