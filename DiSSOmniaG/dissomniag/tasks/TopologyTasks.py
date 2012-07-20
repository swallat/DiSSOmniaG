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
import dissomniag

class DeleteVMsOfTopology(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "topology") or  type(self.context.topology) != dissomniag.model.Topology:
            self.job.trace("DeleteVMsOfTopology: In Context missing topology object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing topology object.")
        failed = False
        for vm in self.context.topology.vms:
            if not dissomniag.model.VM.deleteVm(vm):
                failed = True
                self.job.trace("Could not delete VM %s in Topology %s." % (str(vm.commonName), str(self.context.topology.name)))
        if failed:
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        else:
            return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()
    
class DeleteNetworksOfTopology(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "topology") or  type(self.context.topology) != dissomniag.model.Topology:
            self.job.trace("DeleteNetworksOfTopology: In Context missing topology object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing topology object.")
        
        failed = False
        for net in self.context.topology.generatedNetworks:
            if not dissomniag.model.generatedNetwork.deleteNetwork(net):
                failed = True
                self.job.trace("Could not delete Net %s in Topology %s." % (str(net.name), str(self.context.topology.name)))
        if failed:
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        else:
            return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()
    
class DeleteTopology(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "topology") or  type(self.context.topology) != dissomniag.model.Topology:
            self.job.trace("DeleteTopology: In Context missing topology object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing topology object.")
        if ((self.context.topology.generatedNetworks != None and len(self.context.topology.generatedNetworks) != 0) or
                (self.context.topology.vms != None and len(self.context.topology.vms) != 0)):
            self.job.trace("Topology %s cannot be deleted securely: Make sure that all networks and all VM's of the Topology are deleted.")
            raise dissomniag.taskManager.UnrevertableFailure("Not all VM's or Nets are deleted in Topology")
         
        try:
            session = dissomniag.Session()
            session.delete(self.context.topology)
            dissomniag.saveCommit(session)
            self.context.topology = None
        except Exception, e: 
            raise dissomniag.taskManager.UnrevertableFailure("Cannot delete Topology. SqlalchemyError: %s" % e)
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
        
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()