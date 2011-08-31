# -*- coding: utf-8 -*-
"""
Created on 31.08.2011

@author: Sebastian Wallat
"""

import dissomniag
    
class DeleteIpAddressesOnNode(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "node") or not isinstance(self.context.node, dissomniag.model.AbstractNode):
            self.job.trace("DeleteInterfacesOnNode: In Context missing node object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing node object.")
        failed = False
        for ipAddress in self.context.node.ipAddresses:
            try:
                dissomniag.model.IpAddress.deleteIpAddress(self.user, ipAddress)
            except Exception, e:
                self.job.trace("Cannot delete IpAddress %s on Node %s. Sqlalchemy Exception: " % (str(ipAddress.addr), str(self.context.node.commonName), e))
                failed = True
        if failed:
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        else:
            return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()