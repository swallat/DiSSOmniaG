# -*- coding: utf-8 -*-
"""
Created on 10.08.2011

@author: Sebastian Wallat
"""
import dissomniag

class DeleteTopologyConnections(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "topology") or  type(self.context.topology) != dissomniag.model.Topology:
            self.job.trace("CheckHostUpTask: In Context missing topology object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing topology object.")
        try:
            for connection in self.context.topology.connections:
                dissomniag.model.TopologyConnection.deleteConnectionUnsafe(self.user, connection)
        except Exception:
            self.job.trace("Sqlalchemy Error: Cannot delete Connection of a Topology.")
            raise dissomniag.taskManager.UnrevertableFailure("Sqlalchemy Error: Cannot delete Connection of a Topology.")
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()

class DeleteVMsOfTopology(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "topology") or  type(self.context.topology) != dissomniag.model.Topology:
            self.job.trace("CheckHostUpTask: In Context missing topology object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing topology object.")
        failed = False
        for vm in self.context.topology.virtualMachines:
            if not dissomniag.model.VM.deleteVM(vm):
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
            self.job.trace("CheckHostUpTask: In Context missing topology object.")
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
            self.job.trace("CheckHostUpTask: In Context missing topology object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing topology object.")
        if (self.context.topology.generatedNetworks != None and len(self.context.topology.generatedNetworks) != 0) or
                (self.context.topology.virtualMachines != None and len(self.context.topology.virtualMachines != 0)):
            self.job.trace("Topology %s cannot be deleted securely: Make sure that all networks and all VM's of the Topology are deleted.")
            raise dissomniag.taskManager.UnrevertableFailure("Not all VM's or Nets are deleted in Topology")
         
        try:
            session = dissomniag.Session()
            session.delete(self.context.topology)
            session.commit()
            self.context.topology = None
        except Exception,e 
            raise dissomniag.taskManager.UnrevertableFailure("Cannot delete Topology. SqlalchemyError: %s" % e)
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
        
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()