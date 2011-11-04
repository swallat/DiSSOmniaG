'''
Created on 01.11.2011

@author: Sebastian Wallat
'''
import os
import libvirt
import dissomniag

import logging

log = logging.getLogger("model.VMStates.Deployed_VM")

class Deployed_VM(dissomniag.model.VMStates.AbstractVMState):
    '''
    classdocs
    '''
    def test(self, job):
        cmd = "cat %s" % (os.path.join(self.vm.getRemoteUtilityFolder, "configHash"))
        sshCmd = dissomniag.utils.SSHCommand(self.cmd, \
                                             self.context.liveCd.vm.host.getMaintainanceIP(), \
                                             self.context.liveCd.vm.host.administrativeUserName)
        ret, myHash = sshCmd.callAndGetOutput()
        if ret == 0 and myHash == self.vm.liveCd.hashConfig(job.getUser()):
            self.vm.liveCd.onRemoteUpToDate = True
            job.trace("VM in correct state!")
            return True
        else:
            self.vm.liveCd.onRemoteUpToDate = False
            job.trace("VM not deployed!")
            self.vm.changeState(dissomniag.model.NodeState.DEPLOY_ERROR)
            return self.vm.runningState.sanityCheck(job)

    def prepare(self, job):
        job.trace("VM already prepared!")
        return True
        
    
    def deploy(self, job):
        # 1. Check if Image on local hd exists
        if not os.access(self.vm.getLocalPathToCdImage(self.job.getUser()), os.F_OK) or not os.access(os.path.join(self.vm.getLocalUtilityFolder(job.getUser()), "configHash"), os.F_OK):
            
            self.multiLog("No local image exists for copy!", job, log)
            raise dissomniag.taskManager.TaskFailed("No local image exists for copy!", job, log)
        
        # 2. Create destination directory:
        cmd = "mkdir -p %s" % self.vm.getRemoteUtilityFolder
        sshCmd = dissomniag.utils.SSHCommand(cmd, self.vm.host.getMaintainanceIP(), self.vm.host.administrativeUserName)
        ret, output = sshCmd.callAndGetOutput()
        self.multiLog("Creation of RemoteUtilityFolder with cmd %s results to: res: %d, output: %s" % (cmd, ret, output), job, log)
        
        # 3. Sync Files
        
        for i in range(1,5):
            rsyncCmd = dissomniag.utils.RsyncCommand(self.context.liveCd.vm.getLocalUtilityFolder(self.job.getUser()),\
                                                 self.context.liveCd.vm.getRemoteUtilityFolder(self.job.getUser()), \
                                                 self.context.liveCd.vm.host.getMaintainanceIP(), \
                                                 self.context.liveCd.vm.host.administrativeUserName)
            ret, output = rsyncCmd.callAndGetOutput()
            self.multiLog("Rsync LiveCD ret: %d, output: %s" % (ret, output), log)
            if ret == 0:
                break
            if i == 4 and ret != 0:
                self.context.liveCd.onRemoteUpToDate = False
                self.multiLog("Could not rsync LiveCd Image.", log)
                raise dissomniag.taskManager.TaskFailed("Could not rsync LiveCd Image.")
            
        self.context.liveCd.onRemoteUpToDate = True
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def start(self, job):
        try:
            con = libvirt.open(str(self.vm.host.qemuConnector))
        except libvirt.libvirtError:
            self.vm.changeState(dissomniag.model.NodeState.DEPLOY_ERROR)
            raise dissomniag.taskManager.TaskFailed("Could Not Connect to Libvirt Host!")
        
        try:
            vm = con.createXML(self.context.vm.getLibVirtString(self.job.getUser()), 0)
        except libvirt.libvirtError:
            job.trace("CreateVM: Could not create vm. The network is already created or there is an error.")
            try:
                vm = con.lookupByName(self.context.vm.commonName)
                vm.destroy()
            except libvirt.libvirtError:
                pass
            
            job.trace("CreateVM: Could not create a vm.")
            self.vm.changeState(dissomniag.model.NodeState.RUNTIME_ERROR)
            raise dissomniag.taskManager.TaskFailed("Could Not Create VM!")
        finally:
            con.close()
        
        job.trace("VM created!")
        self.vm.changeState(dissomniag.model.NodeState.CREATED)
        return True
    
    def stop(self, job):
        raise NotImplementedError()
    
    def sanityCheck(self, job):
        raise NotImplementedError()
    
    def reset(self, job):
        raise NotImplementedError()