# -*- coding: utf-8 -*-
"""
Created on 31.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import dissomniag
    
class DeleteVM(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "node") or not isinstance(self.context.node, dissomniag.model.VM) or
            not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM) or self.context.node != self.context.vm:
            self.job.trace("DeleteInterfacesOnNode: In Context missing node object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing node object.")
        
        vm = self.context.vm
        
        if vm.liveCd != None or (vm.interfaces != None and len(vm.interfaces) != 0) or
            (vm.ipAddresses != None and len(vm.ipAddresses) != 0):
            self.job.trace("VM %s cannot be deleted securely: Make sure that the LiveCD, all Interfaces and all IP Addresses of the VM are deleted.")
            raise dissomniag.taskManager.UnrevertableFailure("Not all IPs, Interfaces or the LiveCD are deleted of the VM.")
        
        try:
            session.delete(vm)
            session.commit()
            self.context.vm = None
            self.context.node = None
        except Exception, e:
            raise dissomniag.taskManager.UnrevertableFailure("Cannot delete VM. SqlalchemyError: %s" % e)
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()
    
    