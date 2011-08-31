# -*- coding: utf-8 -*-
"""
Created on 10.08.2011

@author: Sebastian Wallat
"""
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import dissomniag

class CheckHostUpTask(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "host") or  type(self.context.host) != dissomniag.model.Host:
            self.job.trace("CheckHostUpTask: In Context missing host object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing host object.")
        ip = str(self.context.host.getMaintainanceIP().addr)
        if dissomniag.utils.PingUtils.isIpPingable(ip):
            self.context.host.changeState(self.context.user, dissomniag.model.NodeState.UP)
        else:
            self.context.host.changeState(self.context.user, dissomniag.model.NodeState.DOWN)
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()
            
    
class DeleteExistingVMsOnHost(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "host") or  type(self.context.host) != dissomniag.model.Host:
            self.job.trace("CheckHostUpTask: In Context missing host object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing host object.")
        
        oneFailed = False
        for vm in self.context.host.virtualMachines:
            if not dissomniag.model.VM.deleteNode(vm):
                oneFailed = True
                self.job.trace("VM %s is not deletable by User %s" % (str(vm.commonName), str(self.user.username)))
                
        if oneFailed:
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        else:
            return dissomniag.taskManager.TaskReturns.SUCCESS
        
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()
    
class DeleteExistingNetsOnHost(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "host") or  type(self.context.host) != dissomniag.model.Host:
            self.job.trace("CheckHostUpTask: In Context missing host object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing host object.")
        failure = False
        for net in self.context.host.networks:
            if not dissomniag.model.Network.deleteNetwork(self.user, net):
                failure = True
                self.job.trace("Net %s is not deletable by User %s" % (str(net.name), str(self.user.username)))
        
        if failure:
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        else:
            return dissomniag.taskManager.TaskReturns.SUCCESS
        
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()
    
class DeleteHost(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "host") or  type(self.context.host) != dissomniag.model.Host:
            self.job.trace("CheckHostUpTask: In Context missing host object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing host object.")
        
        if (self.context.host.networks != None and len(self.context.host.networks) != 0) or 
                    (self.context.host.virtualMachines != None and len(self.context.host.virtualMachines) != 0):
             self.job.trace("Host %s cannot be deleted securely: Make sure that all networks and all VM's on the Host are deleted.")
             raise dissomniag.taskManager.UnrevertableFailure("Not all VM's or Nets are deleted on Host")
        try: 
            session = dissomniag.Session()
            session.delete(self.context.host)
            session.commit()
            self.context.host = None
        except Exception, e:
            raise dissomniag.taskManager.UnrevertableFailure("Cannot delete Host. SqlalchemyError: %s" % e)
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()