# -*- coding: utf-8 -*-
"""
Created on 10.08.2011

@author: Sebastian Wallat
"""
import datetime
import libvirt
import os
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
            self.context.host.changeState(self.job.getUser(), dissomniag.model.NodeState.UP)
        else:
            self.context.host.changeState(self.job.getUser(), dissomniag.model.NodeState.DOWN)
    
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
            dissomniag.saveCommit(session)
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
        code, output = sshCmd.callAndGetOutput(withError = False)
        if code != 0:
            self.job.trace("checkLibvirtVersionOnHost: Could not execute 'virsh --version'!")
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        self.context.host.changeState(self.job.getUser(), dissomniag.model.NodeState.UP)
        self.context.host.libvirtVersion = output[0]
        self.context.host.lastChecked = datetime.datetime.now()
        session = dissomniag.Session()
        dissomniag.saveFlush(session)
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS

class checkKvmOnHost(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "host") or  type(self.context.host) != dissomniag.model.Host:
            self.job.trace("chekKvmOnHost: In Context missing host object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing host object.")
        
        maintainanceIp = self.context.host.getMaintainanceIP().addr
        self.job.trace("chekKvmOnHost: (Host: %s) egrep vmx --color=always /proc/cpuinfo" % self.context.host.commonName)
        sshCmd1 = dissomniag.utils.SSHCommand("egrep vmx --color=always /proc/cpuinfo", hostOrIp = maintainanceIp, username = self.context.host.administrativeUserName)
        code1, output1 = sshCmd1.callAndGetOutput()
        sshCmd2 = dissomniag.utils.SSHCommand("egrep svm --color=always /proc/cpuinfo", hostOrIp = maintainanceIp, username = self.context.host.administrativeUserName)
        code2, output2 = sshCmd2.callAndGetOutput()
        if code1 != 0 and code2 != 0:
            out = "\n".join(output1 + output2)
            self.job.trace("checkLibvirtVersionOnHost: Could not execute 'egrep vmx --color=always /proc/cpuinfo' %s!" % out)
            self.context.host.kvmUsable = False
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        self.context.host.changeState(self.job.getUser(), dissomniag.model.NodeState.UP)
        self.context.host.kvmUsable = True
        self.context.host.lastChecked = datetime.datetime.now()
        session = dissomniag.Session()
        dissomniag.saveFlush(session)
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class getFreeDiskSpaceOnHost(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "host") or  type(self.context.host) != dissomniag.model.Host:
            self.job.trace("getFreeDiskSpaceOnHost: In Context missing host object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing host object.")
        
        maintainanceIp = self.context.host.getMaintainanceIP().addr
        
        folder = "/" #self.context.host.utilityFolder
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
        self.context.host.changeState(self.job.getUser(), dissomniag.model.NodeState.UP)
        session = dissomniag.Session()
        dissomniag.saveFlush(session)
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
        self.context.host.ramCapacity = str(int(line[1]) / 1024) + "MB" # The second fieled in this line is interesting
        self.context.host.lastChecked = datetime.datetime.now()
        self.context.host.changeState(self.job.getUser(), dissomniag.model.NodeState.UP)
        session = dissomniag.Session()
        dissomniag.saveFlush(session)
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class checkUtilityDirectory(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "host") or  type(self.context.host) != dissomniag.model.Host:
            self.job.trace("checkUtilityDirectory: In Context missing host object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing host object.")
        
        session = dissomniag.Session()
        self.success = False
        self.job.trace("IN CHECK UTILITY DIRECTORY")
        
        maintainanceIp = self.context.host.getMaintainanceIP().addr
        self.job.trace("UtilityFolder: %s" % self.context.host.utilityFolder)
        checkUtilityFolderExistsCmd = dissomniag.utils.SSHCommand("[ -d '%s' ]" % self.context.host.utilityFolder, hostOrIp = maintainanceIp, username = self.context.host.administrativeUserName)
        code, output = checkUtilityFolderExistsCmd.callAndGetOutput()
        if code != 0:
            #Directory does not exists. Try to create it.
            fullpath = os.path.join(self.context.host.utilityFolder, dissomniag.config.hostConfig.vmSubdirectory)
            self.job.trace("Make Utility Directory! %s" % fullpath)
            createUtilityFolderCmd = dissomniag.utils.SSHCommand("mkdir -p %s" % fullpath, hostOrIp = maintainanceIp, username = self.context.host.administrativeUserName)
            code, output = createUtilityFolderCmd.callAndGetOutput()
            if code != 0 :
                self.job.trace("createUtilityFolder: Unable To create Utility Folder.")
                self.context.host.configurationMissmatch = True
                dissomniag.saveFlush(session)
                self.success = False
                raise dissomniag.taskManager.UnrevertableFailure("Could not operate on Host!")
        #everything is ok.
        self.context.host.configurationMissmatch = False
        dissomniag.saveFlush(session)
        self.success = True
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        if self.success == True:
            if not hasattr(self.context, "host") or  type(self.context.host) != dissomniag.model.Host:
                self.job.trace("checkUtilityDirectory: In Context missing host object.")
                raise dissomniag.taskManager.UnrevertableFailure("In Context missing host object.")
            maintainanceIp = self.context.host.getMaintainanceIP().addr
            
            deleteCmd = dissomniag.utils.SSHCommand("rm -rf %s" % self.context.host.utilityFolder, hostOrIp = maintainanceIp, username = self.context.host.administrativeUserName)
            code, output = deleteCmd.callAndGetOutput()
            if code != 0:
                self.job.trace("checkUtilityDirectory: Cannot revert! Output: %s" % output)
                raise dissomniag.taskManager.TaskFailed("Could not revert task Check Utility Folder! (Could not delete it!)")
            return dissomniag.taskManager.TaskReturns.SUCCESS
        
class gatherLibvirtCapabilities(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "host") or  type(self.context.host) != dissomniag.model.Host:
            self.job.trace("gatherLibvirtCapabilities: In Context missing host object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing host object.")
        
        try:
            con = libvirt.open(str(self.context.host.qemuConnector))
        except libvirt.libvirtError:
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            self.context.host.libvirtCapabilities = con.getCapabilities()
        except libvirt.libvirtError:
            return dissomniag.taskManager.TaskReturns.FAILED_BUT_GO_AHEAD
        
        session = dissomniag.Session()
        dissomniag.saveFlush(session)
        return dissomniag.taskManager.TaskReturns.SUCCESS
             
    
    def revert(self):
        if not hasattr(self.context, "host") or  type(self.context.host) != dissomniag.model.Host:
            self.job.trace("gatherLibvirtCapabilities: In Context missing host object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing host object.")
        self.context.host.libvirtCapabilities = None
        session = dissomniag.Session()
        dissomniag.saveFlush(session)
        return dissomniag.taskManager.TaskReturns.SUCCESS
        
    
