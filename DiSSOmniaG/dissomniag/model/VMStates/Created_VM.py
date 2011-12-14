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
import libvirt
import dissomniag
from dissomniag.model.VMStates import *

import logging

log = logging.getLogger("model.VMStates.Created_VM")

class Created_VM(AbstractVMState):
    '''
    classdocs
    '''
    def test(self, job):
        session = dissomniag.Session()
        try:
            con = libvirt.open(str(self.vm.host.qemuConnector))
        except libvirt.libvirtError:
            self.vm.lastSeenCient = None
            dissomniag.saveCommit(session)
            self.vm.changeState(dissomniag.model.NodeState.RUNTIME_ERROR)
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            vm = con.lookupByName(self.vm.commonName)
        except libvirt.libvirtError:
            job.trace("VM is not Running.")
            self.vm.lastSeenCient = None
            dissomniag.saveCommit(session)
            self.vm.changeState(dissomniag.model.NodeState.RUNTIME_ERROR)
            return self.vm.runningState.sanityCheck(job)
        
        if vm.isActive() == 1:
            job.trace("VM state is correct!")
            return True
        else:
            try:
                vm.destroy()
            except libvirt.libvirtError as e:
                pass
            job.trace("VM is not Running.")
            self.vm.lastSeenCient = None
            dissomniag.saveCommit(session)
            self.vm.changestate(dissomniag.model.NodeState.RUNTIME_ERROR)
            return self.vm.runningState.sanityCheck(job)
    
    def prepare(self, job):
        job.trace("VM already created!")
        return True
    
    def deploy(self, job):
        return True
    
    def start(self, job):
        return True
    
    def stop(self, job):
        session = dissomniag.Session()
        self.vm.lastSeenCient = None
        dissomniag.saveCommit(session)
        try:
            con = libvirt.open(str(self.vm.host.qemuConnector))
        except libvirt.libvirtError:
            self.vm.changeState(dissomniag.model.NodeState.DEPLOY_ERROR)
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            vm = con.lookupByName(self.vm.commonName)
        except libvirt.libvirtError:
            self.multiLog("destroyVMOnHost: Could not find VM on host.", job, log)
        else:
            try:
                vm.destroy()
            except libvirt.libvirtError:
                self.multiLog("destroyVMOnHost: could not destroy or undefine vm", job, log)
                self.vm.changeState(dissomniag.model.NodeState.DEPLOY_ERROR)
                return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        
        self.vm.changeState(dissomniag.model.NodeState.DEPLOYED)
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def sanityCheck(self, job):
        return True
    
    def reset(self, job):
        returnMe = self.stop(job)
        session = dissomniag.Session()
        self.vm.lastSeenCient = None
        dissomniag.saveCommit(session)
        self.vm.changeState(dissomniag.model.NodeState.DEPLOYED)
        return returnMe