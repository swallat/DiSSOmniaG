# -*- coding: utf-8 -*-
"""
Created on 31.08.2011

@author: Sebastian Wallat
"""

import dissomniag

class DeleteIpAddressesOnNetwork(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "net") or not isinstance(self.context.net, dissomniag.model.Topology):
            self.job.trace("DeleteIpAddressesOnNetwork: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        
        failed = False
        for ip in self.context.net.ipAddresses:
            if ip.interface != None or ip.host != None:
                continue
            try:
                dissomniag.model.IpAddress.deleteIpAddress(self.user, ip)
            except Exception, e:
                self.job.trace("Cannot delete IP %s in Network %s. SqlalchemyError: %s" % (str(ip.addr), str(self.context.net.name), e))
                failed = True
        
        if failed:
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        else:
            return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()
    
class DeleteNetwork(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "net") or not isinstance(self.context.net, dissomniag.model.Topology):
            self.job.trace("DeleteIpAddressesOnNetwork: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        
        if isinstance(self.context.net, dissomniag.model.generatedNetwork):
            pass
        
        try:
            session = dissomniag.Session()
            session.delete(self.context.net)
            session.commit()
            self.context.net = None
        except Exception, e:
            self.job.trace("Cannot delete Network. Sqlalchemy Error: %s" % e)
            raise dissomniag.taskManager.UnrevertableFailure("Cannot delete Network. Sqlalchemy Error %s" % e)
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure() 