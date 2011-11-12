# -*- coding: utf-8 -*-
"""
Created on 31.08.2011

@author: Sebastian Wallat
"""
import libvirt
import dissomniag

class DeleteIpAddressesOnNetwork(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "net") or not isinstance(self.context.net, dissomniag.model.Network):
            self.job.trace("DeleteIpAddressesOnNetwork: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        
        failed = False
        for ip in self.context.net.ipAddresses:
            if ip.interface != None or ip.node != None:
                continue
            try:
                dissomniag.model.IpAddress.deleteIpAddress(self.job.getUser(), ip)
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
        if not hasattr(self.context, "net") or not isinstance(self.context.net, dissomniag.model.Network):
            self.job.trace("DeleteIpAddressesOnNetwork: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        
        if isinstance(self.context.net, dissomniag.model.generatedNetwork):
            if self.context.net.state == dissomniag.model.GenNetworkState.CREATED:
                self.job.trace("DeleteNetwork: Network is still running")
                raise dissomniag.taskManager.UnrevertableFailure()
        
        try:
            session = dissomniag.Session()
            session.delete(self.context.net)
            dissomniag.saveCommit(session)
            self.context.net = None
        except Exception, e:
            self.job.trace("Cannot delete Network. Sqlalchemy Error: %s" % e)
            raise dissomniag.taskManager.UnrevertableFailure("Cannot delete Network. Sqlalchemy Error %s" % e)
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()
    
class createNetworkOnHost(dissomniag.taskManager.AtomicTask):
    
    success = False
    
    def run(self):
        if not hasattr(self.context, "net") or not isinstance(self.context.net, dissomniag.model.generatedNetwork):
            self.job.trace("createNetwork: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        
        try:
            con = libvirt.open(str(self.context.net.getHost(self.job.getUser()).qemuConnector))
        except libvirt.libvirtError:
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            net = con.networkCreateXML  (self.context.net.getLibVirtString(self.job.getUser()))
        except libvirt.libvirtError:
            self.job.trace("CreateNetwork: Could not create network. The network is already created or there is an error.")
            try:
                net = con.networkLookupByName(self.context.net.name)
            except libvirt.libvirtError:
                self.job.trace("CreateNetwork: Could not create a network.")
                self.context.net.state = dissomniag.model.GenNetworkState.RUNTIME_ERROR
                try:
                    con.close()
                except Exception:
                    pass
                raise dissomniag.taskManager.TaskFailed("Could Not Create Net!")
        try:
            con.close()
        except Exception:
            pass
        self.success = True
        self.context.net.state = dissomniag.model.GenNetworkState.CREATED
        return dissomniag.taskManager.TaskReturns.SUCCESS
             
    
    def revert(self):
        if self.success:
            if not hasattr(self.context, "net") or not isinstance(self.context.net, dissomniag.model.generatedNetwork):
                self.job.trace("createNetwork: In Context missing net object.")
                raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
            try:
                con = libvirt.open(str(self.context.net.getHost(self.job.getUser()).qemuConnector))
            except libvirt.libvirtError:
                raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
            
            try:
                net = con.networkLookupByName(self.context.net.name)
            except libvirt.libvirtError:
                self.job.trace("CreateNetwork: Could not find network.")
                self.context.net.state = dissomniag.model.GenNetworkState.RUNTIME_ERROR
                try:
                    con.close()
                except Exception:
                    pass
                raise dissomniag.taskManager.TaskFailed("Could not find network")
            try:
                net.destroy()
            except libvirt.libvirtError:
                self.job.trace("CreateNetwork: Could not destroy network.")
                self.context.net.state = dissomniag.model.GenNetworkState.GENERAL_ERROR
                try:
                    con.close()
                except Exception:
                    pass
                raise dissomniag.taskManager.TaskFailed("Could not destroy network")
            
            try:
                con.close()
            except Exception:
                pass
            self.context.net.state = dissomniag.model.GenNetworkState.INACTIVE
            
        return dissomniag.taskManager.TaskReturns.SUCCESS

"""
Destroy and undefine network on Host
"""
class destroyNetworkOnHost(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "net") or not isinstance(self.context.net, dissomniag.model.generatedNetwork):
            self.job.trace("destroyNetwork: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        
        try:
            con = libvirt.open(str(self.context.net.getHost(self.job.getUser()).qemuConnector))
        except libvirt.libvirtError:
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            net = con.networkLookupByName(self.context.net.name)
        except libvirt.libvirtError:
            self.job.trace("destroyNetworkOnHost: Could not find network on host.")
        else:
            try:
                net.destroy()
            except libvirt.libvirtError:
                self.job.trace("destroyNetworkOnHost: could not destroy or undefine net")
                self.context.net.state = dissomniag.model.GenNetworkState.GENERAL_ERROR
                return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        
        self.context.net.state = dissomniag.model.GenNetworkState.INACTIVE
        return dissomniag.taskManager.TaskReturns.SUCCESS        
    
    def revert(self):
        raise dissomniag.taskManager.UnrevertableFailure()
    
class statusNetwork(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "net") or not isinstance(self.context.net, dissomniag.model.generatedNetwork):
            self.job.trace("getStatusNetwork: In Context missing net object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing net object.")
        session = dissomniag.Session()
        con = None
        try:
            con = libvirt.open(str(self.context.net.getHost(self.job.getUser()).qemuConnector))
        except libvirt.libvirtError:
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            net = con.networkLookupByName(self.context.net.name)
        except libvirt.libvirtError:
            if self.context.net.state == dissomniag.model.GenNetworkState.INACTIVE:
                return dissomniag.taskManager.TaskReturns.SUCCESS
            elif self.context.net.state == dissomniag.model.GenNetworkState.CREATED:
                self.context.net.state = dissomniag.model.GenNetworkState.RUNTIME_ERROR
                dissomniag.saveFlush(session)
                self.context.net.operate(self.job.getUser())
                return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
            else:
                self.context.net.state = dissomniag.model.GenNetworkState.GENERAL_ERROR
                dissomniag.saveFlush(session)
                self.context.net.operate(self.job.getUser())
                raise dissomniag.taskManager.TaskFailed("Network Status Check GENERAL_ERROR!")
        
        if net.isActive() == 1:
            if self.context.net.state == dissomniag.model.GenNetworkState.INACTIVE:
                self.context.net.state = dissomniag.model.GenNetworkState.GENERAL_ERROR
                dissomniag.saveFlush(session)
                self.context.net.operate(self.job.getUser())
                raise dissomniag.taskManager.TaskFailed("Network Status Check GENERAL_ERROR!")
            self.context.net.state = dissomniag.model.GenNetworkState.CREATED
        
        dissomniag.saveFlush(session)
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS #Do not revert State
