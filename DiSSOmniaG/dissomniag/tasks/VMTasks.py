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
        if (not hasattr(self.context, "node") or not isinstance(self.context.node, dissomniag.model.VM) or
            not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM) or self.context.node != self.context.vm):
            self.job.trace("DeleteInterfacesOnNode: In Context missing node object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing node object.")
        
        vm = self.context.vm
        
        if (vm.liveCd != None or (vm.interfaces != None and len(vm.interfaces) != 0) or
            (vm.ipAddresses != None and len(vm.ipAddresses) != 0)):
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
    
    
class createVMOnHost(dissomniag.taskManager.AtomicTask):
    
    success = False
    
    def run(self):
        if not hasattr(self.context, "vm") or not isinstance(self.context.net, dissomniag.model.VM):
            self.job.trace("createVM: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        
        try:
            con = libvirt.open(str(self.context.vm.host(self.job.getUser()).qemuConnector))
        except libvirt.libvirtError:
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            vm = con.createXML(self.context.vm.getLibVirtString(self.job.getUser()))
        except libvirt.libvirtError:
            self.job.trace("CreateVM: Could not create vm. The network is already created or there is an error.")
            try:
                vm = con.lookupByName(self.context.vm.name)
            except libvirt.libvirtError:
                self.job.trace("CreateVM: Could not create a vm.")
                self.context.vm.state = dissomniag.model.NodeState.CREATION_ERROR
                try:
                    con.close()
                except Exception:
                    pass
                raise dissomniag.taskManager.TaskFailed("Could Not Create VM!")
        try:
            con.close()
        except Exception:
            pass
        self.success = True
        self.context.vm.state = dissomniag.model.NodeState.CREATED
        return dissomniag.taskManager.TaskReturns.SUCCESS
             
    
    def revert(self):
        if self.success:
            if not hasattr(self.context, "vm") or not isinstance(self.context.net, dissomniag.model.VM):
                self.job.trace("createVM: In Context missing net object.")
                raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
            try:
                con = libvirt.open(str(self.context.vm.host(self.job.getUser()).qemuConnector))
            except libvirt.libvirtError:
                raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
            
            try:
                vm = con.lookupByName(self.context.vm.name)
            except libvirt.libvirtError:
                self.job.trace("CreateNetwork: Could not find network.")
                self.context.vm.state = dissomniag.model.NodeState.CREATION_ERROR
                try:
                    con.close()
                except Exception:
                    pass
                raise dissomniag.taskManager.TaskFailed("Could not find vm")
            try:
                vm.destroy()
            except libvirt.libvirtError:
                self.job.trace("CreateNetwork: Could not destroy vm.")
                self.context.vm.state = dissomniag.model.NodeState.RUNNTIME_ERROR
                try:
                    con.close()
                except Exception:
                    pass
                raise dissomniag.taskManager.TaskFailed("Could not destroy vm")
            
            try:
                con.close()
            except Exception:
                pass
            self.context.vm.state = dissomniag.model.NodeState.NOT_CREATED
            
        return dissomniag.taskManager.TaskReturns.SUCCESS

"""
Destroy and undefine network on Host
"""
class destroyVMOnHost(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "vm") or not isinstance(self.context.net, dissomniag.model.VM):
            self.job.trace("destroyVM: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        
        try:
            con = libvirt.open(str(self.context.vm.host(self.job.getUser()).qemuConnector))
        except libvirt.libvirtError:
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            vm = con.lookupByName(self.context.vm.name)
        except libvirt.libvirtError:
            self.job.trace("destroyVMOnHost: Could not find VM on host.")
        else:
            try:
                vm.destroy()
            except libvirt.libvirtError:
                self.job.trace("destroyVMOnHost: could not destroy or undefine vm")
                self.context.vm.state = dissomniag.model.NodeState.RUNNTIME_ERROR
                return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        
        self.context.vm.state = dissomniag.model.NodeState.NOT_CREATED
        return dissomniag.taskManager.TaskReturns.SUCCESS        
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()
    
class statusVM(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "vm") or not isinstance(self.context.net, dissomniag.model.VM):
            self.job.trace("statusVM: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        session = dissomniag.Session()
        con = None
        try:
            con = libvirt.open(str(self.context.vm.host(self.job.getUser()).qemuConnector))
        except libvirt.libvirtError:
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            vm = con.lookupByName(self.context.vm.name)
        except libvirt.libvirtError:
            if self.context.vm.state == dissomniag.model.NodeState.NOT_CREATED:
                return dissomniag.taskManager.TaskReturns.SUCCESS
            elif self.context.vm.state == dissomniag.model.NodeState.CREATED:
                self.context.vm.state = dissomniag.model.NodeState.RUNNTIME_ERROR
                session.flush()
                self.context.vm.operate(self.job.getUser())
                return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
            else:
                self.context.vm.state = dissomniag.model.NodeState.RUNNTIME_ERROR
                session.flush()
                self.context.vm.operate(self.job.getUser())
                raise dissomniag.taskManager.TaskFailed("VM Status Check RUNTIME_ERROR!")
        
        if vm.isActive() == 1:
            if self.context.vm.state == dissomniag.model.NodeState.NOT_CREATED:
                self.context.vm.state = dissomniag.model.NodeState.RUNTIME_ERROR
                session.flush()
                self.context.vm.operate(self.job.getUser())
                raise dissomniag.taskManager.TaskFailed("VM Status Check RUNTIME_ERROR!")
            self.context.vm.state = dissomniag.model.NodeState.CREATED
        
        session.flush()
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS #Do not revert State
    
