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
        return True
    
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
        return True
    
    def sanityCheck(self, job):
        return True
    
    def reset(self, job):
        self.vm.changeState(dissomniag.model.NodeState.PREPARED)
        return self.vm.runningState.cleanUpDeploy(job)