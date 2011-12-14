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
import sqlalchemy as sa
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import xmlrpclib
import traceback, sys

import dissomniag
    
class DeleteVM(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if (not hasattr(self.context, "node") or not isinstance(self.context.node, dissomniag.model.VM) or
            not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM) or self.context.node != self.context.vm):
            self.job.trace("DeleteVM: In Context missing vm object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing vm object.")
        
        vm = self.context.vm
        self.job.trace("IN DELETE")
        
        if (vm.liveCd != None or (len(vm.interfaces) != 0) or
            ( len(vm.ipAddresses) != 0)):
            self.job.trace("VM %s cannot be deleted securely: Make sure that the LiveCD, all Interfaces and all IP Addresses of the VM are deleted." % vm.commonName)
            raise dissomniag.taskManager.UnrevertableFailure("Not all IPs, Interfaces or the LiveCD are deleted of the VM.")
        
        try:
            session = dissomniag.Session()
            session.delete(vm.sshKey)
            session.delete(vm)
            dissomniag.saveCommit(session)
            self.context.vm = None
            self.context.node = None
        except Exception, e:
            raise dissomniag.taskManager.UnrevertableFailure("Cannot delete VM. SqlalchemyError: %s" % e)
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()
    
class sanityDeleteVM(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if (not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM)):
            self.job.trace("DeleteInterfacesOnNode: In Context missing node object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing node object.")
        
        vm = self.context.vm
        dissomniag.model.VM.deleteVm(self.job.getUser(), vm)
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class statusVM(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
            self.job.trace("statusVM: In Context missing vm object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        try:
            self.context.vm.test(self.job.getUser(), self.job)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)
            self.job.trace(str(e))
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class prepareVM(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
            self.job.trace("prepareVM: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        try:
            self.job.trace("In PrepareVM Task.")
            self.context.vm.prepare(self.job.getUser(), self.job)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)
            self.job.trace(str(e))
            raise dissomniag.taskManager.TaskFailed("Prepare VM failed!")
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        #if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
        #    self.job.trace("prepareVM: In Context missing net object.")
        #    raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        #try:
        #    self.context.vm.reset(self.job.getUser(), self.job)
        #except Exception as e:
        #    exc_type, exc_value, exc_traceback = sys.exc_info()
        #    traceback.print_tb(exc_traceback)
        #    self.job.trace(str(e))
        #    raise dissomniag.taskManager.TaskFailed("Reset VM failed!")
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class deployVM(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
            self.job.trace("deployVM: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        try:
            self.context.vm.deploy(self.job.getUser(), self.job)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)
            self.job.trace(str(e))
            raise dissomniag.taskManager.TaskFailed("Deploy VM failed!")
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        #if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
        #    self.job.trace("deployVM: In Context missing net object.")
        #    raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        #try:
        #    self.context.vm.reset(self.job.getUser(), self.job)
        #except Exception as e:
        #    exc_type, exc_value, exc_traceback = sys.exc_info()
        #    traceback.print_tb(exc_traceback)
        #    self.job.trace(str(e))
        #    raise dissomniag.taskManager.TaskFailed("Reset VM failed!")
        #
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class startVM(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
            self.job.trace("startVM: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        try:
            self.context.vm.start(self.job.getUser(), self.job)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)
            self.job.trace(str(e))
            raise dissomniag.taskManager.TaskFailed("Start VM failed!")
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        #if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
        #    self.job.trace("startVM: In Context missing net object.")
        #    raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        #try:
        #    self.context.vm.reset(self.job.getUser(), self.job)
        #except Exception as e:
        #    exc_type, exc_value, exc_traceback = sys.exc_info()
        #    traceback.print_tb(exc_traceback)
        #    self.job.trace(str(e))
        #    raise dissomniag.taskManager.TaskFailed("Reset VM failed!")
        
        return dissomniag.taskManager.TaskReturns.SUCCESS

class stopVM(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
            self.job.trace("stopVM: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        try:
            self.context.vm.stop(self.job.getUser(), self.job)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)
            self.job.trace(str(e))
            raise dissomniag.taskManager.TaskFailed("Stop VM failed!")
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        #if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
        #    self.job.trace("stopVM: In Context missing net object.")
        #    raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        #try:
        #    self.context.vm.reset(self.job.getUser(), self.job)
        #except Exception as e:
        #    exc_type, exc_value, exc_traceback = sys.exc_info()
        #    traceback.print_tb(exc_traceback)
        #    self.job.trace(str(e))
        #    raise dissomniag.taskManager.TaskFailed("Reset VM failed!")
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class resetVM(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
            self.job.trace("resetVM: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        try:
            self.context.vm.reset(self.job.getUser(), self.job)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)
            self.job.trace(str(e))
            raise dissomniag.taskManager.TaskFailed("Stop VM failed!")
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class totalResetVM(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
            self.job.trace("resetVM: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        
        cycleCounter = 0
        session = dissomniag.Session()
        session.expire(self.context.vm)
        while((self.context.vm.state != dissomniag.model.NodeState.NOT_CREATED) and (cycleCounter <= 4)):
            try:
                self.context.vm.reset(self.job.getUser(), self.job)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_tb(exc_traceback)
                self.job.trace(str(e))
                pass
            
            cycleCounter = cycleCounter + 1
            session.expire(self.context.vm)
        
        if self.context.vm.state == dissomniag.model.NodeState.NOT_CREATED:
            return dissomniag.taskManager.TaskReturns.SUCCESS
        else:
            raise dissomniag.taskManager.UnrevertableFailure("Could not reset VM!")
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class updateLiveClientVM(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
            self.job.trace("udateLiveClientVM: In Context missing vm object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing vm object.")
        try:
            proxy = xmlrpclib.ServerProxy(self.context.vm.getRPCUri(self.user))
        except dissomniag.NoMaintainanceIp as e:
            self.job.trace("No MaintainanceIp for VM available. Wait until it has fully started.")
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        except Exception as e:
            self.job.trace("General RPC Error. Wait until Vm has fully started.")
        
        try:
            xml = proxy.update(self.context.vm.liveCd.getInfoXml(self.job.getUser()))
            self.context.vm.recvUpdateLiveClient(self.job.getUser(), xml)
        except Exception as e:
            self.job.trace("Could not gather informations about a VM.")
            session = dissomniag.Session()
            self.context.vm.lastSeenClient = None
            dissomniag.saveCommit(session)
        
        
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    
"""    
class createVMOnHost(dissomniag.taskManager.AtomicTask):
    
    success = False
    
    def run(self):
        if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
            self.job.trace("createVM: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        
        try:
            con = libvirt.open(str(self.context.vm.host.qemuConnector))
        except libvirt.libvirtError:
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            vm = con.createXML(self.context.vm.getLibVirtString(self.job.getUser()), 0)
        except libvirt.libvirtError:
            self.job.trace("CreateVM: Could not create vm. The network is already created or there is an error.")
            try:
                vm = con.lookupByName(self.context.vm.commonName)
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
            if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
                self.job.trace("createVM: In Context missing net object.")
                raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
            try:
                con = libvirt.open(str(self.context.vm.host.qemuConnector))
            except libvirt.libvirtError:
                raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
            
            try:
                vm = con.lookupByName(self.context.vm.commonName)
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
#Destroy and undefine network on Host
"""
class destroyVMOnHost(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
            self.job.trace("destroyVM: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        
        try:
            con = libvirt.open(str(self.context.vm.host.qemuConnector))
        except libvirt.libvirtError:
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            vm = con.lookupByName(self.context.vm.commonName)
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
        if not hasattr(self.context, "vm") or not isinstance(self.context.vm, dissomniag.model.VM):
            self.job.trace("statusVM: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        session = dissomniag.Session()
        con = None
        try:
            con = libvirt.open(str(self.context.vm.host.qemuConnector))
        except libvirt.libvirtError:
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            vm = con.lookupByName(self.context.vm.commonName)
        except libvirt.libvirtError:
            if self.context.vm.state == dissomniag.model.NodeState.NOT_CREATED:
                return dissomniag.taskManager.TaskReturns.SUCCESS
            elif self.context.vm.state == dissomniag.model.NodeState.CREATED:
                self.context.vm.state = dissomniag.model.NodeState.RUNNTIME_ERROR
                dissomniag.saveFlush(session)
                self.context.vm.operate(self.job.getUser())
                return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
            else:
                self.context.vm.state = dissomniag.model.NodeState.RUNNTIME_ERROR
                dissomniag.saveFlush(session)
                self.context.vm.operate(self.job.getUser())
                raise dissomniag.taskManager.TaskFailed("VM Status Check RUNTIME_ERROR!")
        
        if vm.isActive() == 1:
            if self.context.vm.state == dissomniag.model.NodeState.NOT_CREATED:
                self.context.vm.state = dissomniag.model.NodeState.RUNTIME_ERROR
                dissomniag.saveFlush(session)
                self.context.vm.operate(self.job.getUser())
                raise dissomniag.taskManager.TaskFailed("VM Status Check RUNTIME_ERROR!")
            self.context.vm.state = dissomniag.model.NodeState.CREATED
        
        dissomniag.saveFlush(session)
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS #Do not revert State

"""
