# -*- coding: utf-8 -*-
"""
Created on 10.08.2011

@author: Sebastian Wallat
"""
import datetime
import shlex
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
                self.job.trace("VM %s is not deletable by User %s" % (str(vm.commonName), str(self.job.getUser().username)))
                
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
            if not dissomniag.model.Network.deleteNetwork(self.job.getUser(), net):
                failure = True
                self.job.trace("Net %s is not deletable by User %s" % (str(net.name), str(self.job.getUser().username)))
        
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
        
        if ((self.context.host.networks != None and len(self.context.host.networks) != 0) or (self.context.host.virtualMachines != None and len(self.context.host.virtualMachines) != 0)):
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
    
class checkLibvirtVersionOnHost(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "host") or  type(self.context.host) != dissomniag.model.Host:
            self.job.trace("chekLibvirtVersionOnHost: In Context missing host object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing host object.")
        
        maintainanceIp = self.context.host.getMaintainanceIP().addr
        self.job.trace("checkLibvirtVersionOnHost: (Host: %s) virsh --version" % self.context.host.commonName)
        
        sshCmd = dissomniag.utils.SSHCommand("virsh --version", hostOrIp = maintainanceIp, username = self.context.host.administrativeUserName)
        code, output = sshCmd.callAndGetOutput()
        if code != 0:
            self.job.trace("checkLibvirtVersionOnHost: Could not execute 'virsh --version'!")
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        self.context.host.libvirtVersion = output[0]
        self.context.host.lastChecked = datetime.datetime.now()
        session = dissomniag.Session()
        session.flush()
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS

class checkKvmOnHost(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "host") or  type(self.context.host) != dissomniag.model.Host:
            self.job.trace("chekKvmOnHost: In Context missing host object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing host object.")
        
        maintainanceIp = self.context.host.getMaintainanceIP().addr
        self.job.trace("chekKvmOnHost: (Host: %s) kvm-ok" % self.context.host.commonName)
        sshCmd = dissomniag.utils.SSHCommand("kvm-ok", hostOrIp = maintainanceIp, username = self.context.host.administrativeUserName)
        code, output = sshCmd.callAndGetOutput()
        if code != 0:
            out = "\n".join(output)
            self.job.trace("checkLibvirtVersionOnHost: Could not execute 'kvm-ok' %s!" % out)
            self.context.host.kvmUsable = False
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        self.context.host.kvmUsable = True
        self.context.host.lastChecked = datetime.datetime.now()
        session = dissomniag.Session()
        session.flush()
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class getFreeDiskSpaceOnHost(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "host") or  type(self.context.host) != dissomniag.model.Host:
            self.job.trace("getFreeDiskSpaceOnHost: In Context missing host object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing host object.")
        
        maintainanceIp = self.context.host.getMaintainanceIP().addr
        
        folder = self.context.host.utilityFolder
        if folder == None:
            folder = "/"
        self.job.trace("getFreeDiskSpaceOnHost: (Host: %s) df -h %s" % (self.context.host.commonName, folder))
        sshCmd = dissomniag.utils.SSHCommand(("df -h %s" % folder), hostOrIp = maintainanceIp, username = self.context.host.administrativeUserName)
        code, output = sshCmd.callAndGetOutput()
        if code != 0:
            self.job.trace("getFreeDiskSpaceOnHost: Unable to get FreeDiskSpace on Host %s" % self.context.host.commonName)
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        
        line = output[1] # First line is Description, Second Line is Info Line of df
        freeSpace = shlex.split(line)[3] # Third object in Line if info about Free Diskspace
        self.context.host.freeDiskspace = freeSpace
        self.context.host.lastChecked = datetime.datetime.now()
        session = dissomniag.Session()
        session.flush()
        return dissomniag.taskManager.TaskReturns.SUCCESS
        
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class getRamCapacityOnHost(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "host") or  type(self.context.host) != dissomniag.model.Host:
            self.job.trace("getRamCapacityOnHost: In Context missing host object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing host object.")
        
        maintainanceIp = self.context.host.getMaintainanceIP().addr
        self.job.trace("getRamCapacityOnHost: (Host: %s) at /proc/meminfo | head -n 1 | awk '/[0-9]/ {print $2}'" % self.context.host.commonName)
        sshCmd = dissomniag.utils.SSHCommand("cat /proc/meminfo", hostOrIp = maintainanceIp, username = self.context.host.administrativeUserName)
        code, output = sshCmd.callAndGetOutput()
        if code != 0:
            self.job.trace("getRamCapacityOnHost: Unable to get RAM Capacity.")
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        line = shlex.split(output[0]) #The first line is the only interesting line
        self.context.host.ramCapacity = str(int(line[1])/1024) + "MB" # The second fieled in this line is interesting
        self.context.host.lastChecked = datetime.datetime.now()
        session = dissomniag.Session()
        session.flush()
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    