# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import lxml
from lxml import etree
import os
import sqlalchemy as sa
import sqlalchemy.orm as orm
from abc import ABCMeta, abstractmethod
import datetime
import thread

import dissomniag
from dissomniag.model import *
from logging import thread
from xml.etree import ElementTree
        

class VM(AbstractNode):
    __tablename__ = 'vms'
    __mapper_args__ = {'polymorphic_identity': 'vm'}
    vm_id = sa.Column('id', sa.Integer, sa.ForeignKey('nodes.id'), primary_key = True)
    ramSize = sa.Column(sa.String, default = "1024MB", nullable = False)
    hdSize = sa.Column(sa.String, default = "5GB")
    isHdCreated = sa.Column(sa.Boolean, default = False, nullable = False)
    useHD = sa.Column(sa.Boolean, default = False, nullable = False)
    enableVNC = sa.Column(sa.Boolean, default = False, nullable = False)
    vncPort = sa.Column(sa.String)
    vncPassword = sa.Column(sa.String(40))
    dynamicAptList = sa.Column(sa.String)
    lastSeenClient = sa.Column(sa.DateTime
                               )
    topology_id = sa.Column(sa.Integer, sa.ForeignKey('topologies.id'))
    host_id = sa.Column(sa.Integer, sa.ForeignKey('hosts.id'))    # The characters to make up the random password
    host = orm.relationship("Host", primaryjoin = "VM.host_id == Host.host_id", backref = "virtualMachines")
    liveCd_id = sa.Column(sa.Integer, sa.ForeignKey('livecds.id'))
    #liveCd = orm.relationship("LiveCd", backref = orm.backref('livecds', uselist = False))
    #liveCd = orm.relationship("LiveCd", backref = "vm")
    liveCd = orm.relationship("LiveCd", backref=orm.backref("vm", uselist=False))
    maintainUser_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    maintainUser = orm.relationship("User", backref=orm.backref("VM", uselist=False))
    runningState = None
    
    """
    classdocs
    """
    
    #def __new__(self, *args, **kwargs):
    
    #    self.createdState = dissomniag.model.VMStates.Created_VM(self)
    #    self.deployErrorState = dissomniag.model.VMStates.Deploy_Error_VM(self)
    #    self.deployedState = dissomniag.model.VMStates.Deployed_VM(self)
    #    self.notCreatedState = dissomniag.model.VMStates.Not_Created_VM(self)
    #    self.prepareErrorState = dissomniag.model.VMStates.Prepare_Error_VM(self)
    #    self.preparedState = dissomniag.model.VMStates.Prepared_VM(self)
    #    self.runtimeErrorState = dissomniag.model.VMStates.Runtime_Error_VM(self)
    #    #return super(VM, self).__new__(self, *args, **kwargs)
    #    return super(VM, self).__new__(self)

    def changeState(self, nextState):
        if not dissomniag.model.NodeState.checkIn(nextState):
            raise TypeError()
        else:
            session = dissomniag.Session()
            if nextState == dissomniag.model.NodeState.NOT_CREATED:
                self.runningState = self.notCreatedState
                self.state = dissomniag.model.NodeState.NOT_CREATED
            elif nextState == dissomniag.model.NodeState.CREATED:
                self.runningState = self.createdState
                self.state = dissomniag.model.NodeState.CREATED
            elif nextState == dissomniag.model.NodeState.PREPARED:
                self.runningState = self.preparedState
                self.state = dissomniag.model.NodeState.PREPARED
            elif nextState == dissomniag.model.NodeState.PREPARE_ERROR:
                self.runningState = self.prepareErrorState
                self.state = dissomniag.model.NodeState.PREPARE_ERROR
            elif nextState == dissomniag.model.NodeState.DEPLOYED:
                self.runningState = self.deployedState
                self.state = dissomniag.model.NodeState.DEPLOYED
            elif nextState == dissomniag.model.NodeState.DEPLOY_ERROR:
                self.runningState = self.deployErrorState
                self.state = dissomniag.model.NodeState.DEPLOY_ERROR
            elif nextState == dissomniag.model.NodeState.RUNTIME_ERROR:
                self.runningState = self.runtimeErrorState
                self.state = dissomniag.model.NodeState.RUNTIME_ERROR
            dissomniag.saveCommit(session)
                
    def selectInitialStateActor(self):
        #if self.runningState == None:
        #    self.createdState = dissomniag.model.VMStates.Created_VM(self, self.liveCd)
        #    self.deployErrorState = dissomniag.model.VMStates.Deploy_Error_VM(self, self.liveCd)
        #    self.deployedState = dissomniag.model.VMStates.Deployed_VM(self, self.liveCd)
        #    self.notCreatedState = dissomniag.model.VMStates.Not_Created_VM(self, self.liveCd)
        #    self.prepareErrorState = dissomniag.model.VMStates.Prepare_Error_VM(self, self.liveCd)
        #    self.preparedState = dissomniag.model.VMStates.Prepared_VM(self, self.liveCd)
        #    self.runtimeErrorState = dissomniag.model.VMStates.Runtime_Error_VM(self, self.liveCd)
        #    self.changeState(self.state)
        #return
        session = dissomniag.Session()
        if self.liveCd != None:
            session.expire(self.liveCd)
        self.runningState = None
        self.createdState = dissomniag.model.VMStates.Created_VM(self, self.liveCd)
        self.deployErrorState = dissomniag.model.VMStates.Deploy_Error_VM(self, self.liveCd)
        self.deployedState = dissomniag.model.VMStates.Deployed_VM(self, self.liveCd)
        self.notCreatedState = dissomniag.model.VMStates.Not_Created_VM(self, self.liveCd)
        self.prepareErrorState = dissomniag.model.VMStates.Prepare_Error_VM(self, self.liveCd)
        self.preparedState = dissomniag.model.VMStates.Prepared_VM(self, self.liveCd)
        self.runtimeErrorState = dissomniag.model.VMStates.Runtime_Error_VM(self, self.liveCd)
        self.changeState(self.state)
        # The characters to make up the random password
    def __init__(self, user, commonName, host):
        
        if host != None and isinstance(host, dissomniag.model.Host):
            self.host = host
        
        sshKey = SSHNodeKey.generateVmKey(commonName, user="user")
        
        super(VM, self).__init__(user, commonName, sshKey = sshKey, state = dissomniag.model.NodeState.NOT_CREATED)
        self.selectInitialStateActor()
        self.vncPort = self.getFreeVNCPortOnHost(user, host)
        self.vncPassword = dissomniag.utils.random_password()
        
        interface = self.addInterface(user, "maintain")
        interface.maintainanceInterface = True
            
        self.liveCd = dissomniag.model.LiveCd(self)
        self.maintainUser = dissomniag.auth.User(username = self.commonName, password = self.uuid, isAdmin = False, loginRPC = True, loginSSH = False, loginManhole = False, maintain= True)
        
        session = dissomniag.Session()    
        dissomniag.saveCommit(session)
    
    def getLibVirtXML(self, user):
        self.authUser(user)
        domain = etree.Element("domain")
        domainAttrib = domain.attrib
        domainAttrib['type'] = "kvm"
        name = etree.SubElement(domain, "name")
        name.text = self.commonName
        uuid = etree.SubElement(domain, "uuid")
        uuid.text = str(self.uuid)
        memory = etree.SubElement(domain, "memory")
        memory.text = str(self.getRamSize(user))
        currentMemory = etree.SubElement(domain, "currentMemory")
        currentMemory.text = str(self.getRamSize(user))
        vcpu = etree.SubElement(domain, "vcpu")
        vcpu.text = "1"
        
        os = etree.SubElement(domain, "os")
        type = etree.SubElement(os, "type")
        typeAttrib = type.attrib
        typeAttrib["arch"] = "x86_64"
        type.text = "hvm"
        boot = etree.SubElement(os, "boot")
        bootAttrib = boot.attrib
        bootAttrib['dev'] = "cdrom"
        bootmenu = etree.SubElement(os, "bootmenu")
        bootmenuAttrib = bootmenu.attrib
        bootmenuAttrib["enable"] = "no"
        
        features = etree.SubElement(domain, "features")
        acpi = etree.SubElement(features, "acpi")
        apic = etree.SubElement(features, "apic")
        pae = etree.SubElement(features, "pae")
        
        clock = etree.SubElement(domain, "clock")
        clockAttrib = clock.attrib
        clockAttrib["offset"] = "utc"
        
        on_poweroff = etree.SubElement(domain, "on_poweroff")
        on_poweroff.text = "destroy"
            # The characters to make up the random password
        on_reboot = etree.SubElement(domain, "on_reboot")
        on_reboot.text = "restart"
        
        on_crash = etree.SubElement(domain, "on_crash")
        on_crash.text = "restart"
        
        devices = etree.SubElement(domain, "devices")
        
        emulator = etree.SubElement(devices, "emulator")
        emulator.text = str(self.getEmulator(user))
        
        #1. Insert cdrom drive
        cdromDisk = etree.SubElement(devices, "disk")
        cdromDiskAttrib = cdromDisk.attrib
        cdromDiskAttrib["type"] = "file"
        cdromDiskAttrib["device"] = "cdrom"
        
        cdromDriver = etree.SubElement(cdromDisk, "driver")
        cdromDriverAttrib = cdromDriver.attrib
        cdromDriverAttrib["name"] = "qemu"
        cdromDriverAttrib["type"] = "raw"
        
        cdromSource = etree.SubElement(cdromDisk, "source")
        cdromSourceAttrib = cdromSource.attrib
        cdromSourceAttrib["file"] = str(self.getRemotePathToCdImage(user))
            # The characters to make up the random password
        cdromTarget = etree.SubElement(cdromDisk, "target")
        cdromTargetAttrib = cdromTarget.attrib
        cdromTargetAttrib["dev"] = "hda"
        cdromTargetAttrib["bus"] = "ide"
        
        cdromReadonly = etree.SubElement(cdromDisk, "readonly")
        
        #2. Insert hd drive
        if self.useHD:
            hdDisk = etree.SubElement(devices, "disk")
            hdDiskAttrib = hdDisk.attrib
            hdDiskAttrib["type"] = "file"
            hdDiskAttrib["device"] = "disk"
            
            hdDiskDriver = etree.SubElement(hdDisk, "driver")
            hdDiskDriverAttrib = hdDiskDriver.attrib
            hdDiskDriverAttrib["name"] = "qemu"
            hdDiskDriverAttrib["type"] = "qcow2"
            
            hdSource = etree.SubElement(hdDisk, "source")
            hdSourceAttrib = hdSource.attrib
            hdSourceAttrib["file"] = str(self.getPathToHdImage(user))
            
            hdTarget = etree.SubElement(hdDisk, "target")
            hdTargetAttrib = hdTarget.attrib
            hdTargetAttrib["dev"] = "vdb"
            hdTargetAttrib["bus"] = "virtio"
            
        
        #3. Insert maintainance network interface
        maintainanceInterface = self.getMaintainanceInterface(user)
        
        bridgeInterface = etree.SubElement(devices, "interface")
        bridgeInterfaceAttrib = bridgeInterface.attrib
        bridgeInterfaceAttrib["type"] = "bridge"
        
        bridgeIfMac = etree.SubElement(bridgeInterface, "mac")
        bridgeIfMacAttrib = bridgeIfMac.attrib
        bridgeIfMacAttrib["address"] = str(maintainanceInterface.macAddress)
        
        bridgeIfSource = etree.SubElement(bridgeInterface, "source")
        bridgeIfSourceAttrib = bridgeIfSource.attrib
        bridgeIfSourceAttrib["bridge"] = str(self.host.bridgedInterfaceName)
        
        bridgeIfModel = etree.SubElement(bridgeInterface, "model")
        bridgeIfModelAttrib = bridgeIfModel.attrib
        bridgeIfModelAttrib["type"] = "virtio"
        
        #4. Insert additional network interfaces
        
        for interface in self.interfaces:
            
            if interface.ipAddresses == [] or \
                interface.ipAddresses[0].network == None or \
                not isinstance(interface.ipAddresses[0].network, dissomniag.model.generatedNetwork) or \
                interface.ipAddresses[0].network.state != dissomniag.model.GenNetworkState.CREATED:
                
                continue
            
            interf = etree.SubElement(devices, "interface")
            interfAttrib = interf.attrib
            interfAttrib["type"] = "network"
            
            interfMac = etree.SubElement(interf, "mac")
            interfMacAttrib = interfMac.attrib
            interfMacAttrib["address"] = interface.macAddress
            
            interfSource = etree.SubElement
            (interf, "source")
            interfSourceAttrib = interfSource.attrib
            interfSourceAttrib["network"] = interface.ipAddresses[0].network.name
            
            interfModel = etree.SubElement(interf, "model")
            interfModelAttrib = interfModel.attrib
            interfModelAttrib["type"] = "virtio"
            
        
        #serial = etree.SubElement(devices, "serial")
        #serialAttrib = serial.attrib
        #serialAttrib["type"] = "pty"
        
        #serialTarget = etree.SubElement(serial, "target")
        #serialTargetAttrib = serialTarget.attrib
        #serialTargetAttrib["port"] = "0"
        
        #console = etree.SubElement(devices, "console")
        #consoleAttrib = console.attrib
        #consoleAttrib["type"] = "pty"
        
        #consoleTarget = etree.SubElement(console, "target")
        #consoleTargetAttrib = consoleTarget.attrib
        #consoleTargetAttrib["type"] = "serial"
        #consoleTargetAttrib["port"] = "0"
        
        input = etree.SubElement(devices, "input")
        inputAttrib = input.attrib
        inputAttrib["type"] = "mouse"
        inputAttrib["bus"] = "ps2"
        
        vnc = etree.SubElement(devices, "graphics")
        vncAttrib = vnc.attrib
        vncAttrib["type"] = "vnc"
        vncAttrib["port"] = str(self.vncPort)
        vncAttrib["passwd"] = str(self.vncPassword)
        #vncAttrib["keymap"] = "de"
        listen = etree.SubElement(vnc, "listen")
        listenAttrib = listen.attrib
        listenAttrib["type"] = "address"
        listenAttrib["address"] = "0.0.0.0"
        
        sound = etree.SubElement(devices, "sound")
        soundAttrib = sound.attrib
        soundAttrib["model"] = "ac97"
        
        video = etree.SubElement(devices, "video")
        videoModel = etree.SubElement(video, "model")
        videoModelAttrib = videoModel.attrib
        videoModelAttrib["type"] = "cirrus"
        videoModelAttrib["vram"] = "9216"
        videoModelAttrib["heads"] = "1"        
        
        return domain
    
    def getLibVirtString(self, user):
        self.authUser(user)
        return etree.tostring(self.getLibVirtXML(user), pretty_print = True)
    
    def getRamSize(self, user):
        self.authUser(user)
        ram = 0
        if self.ramSize.endswith("KB"):
            ram = int(self.ramSize.split("KB")[0])
        elif self.ramSize.endswith("MB"):
            ram = int(self.ramSize.split("MB")[0]) * 1024
        elif self.ramSize.endswith("GB"):
            ram = int(self.ramSize.split("GB")[0]) * 1024 * 1024

        if ram >= 1024:
            ram = ram - (ram % 1024)
        else:
            diff = 1024 - (ram % 1024)
            ram = ram + diff
        return str(ram)
    
    def getHdSize(self, user):
        pass       
    
    def getRemoteUtilityFolder(self, user):
        self.authUser(user)
        
        allVmsFolder = os.path.join(self.host.utilityFolder, dissomniag.config.hostConfig.vmSubdirectory)
        vmFolder = os.path.join(allVmsFolder, self.commonName)
        return vmFolder
    
    def getLocalUtilityFolder(self, user):
        self.authUser(user)
        vmFolder = os.path.join(dissomniag.config.dissomniag.vmsFolder, self.commonName)
        return vmFolder
    
    def getRemotePathToCdImage(self, user):
        self.authUser(user)
        
        folder = self.getRemoteUtilityFolder(user)
        return os.path.join(folder, self.getImageName(user))
    
    def getLocalPathToCdImage(self, user):
        self.authUser(user)
        return os.path.join(self.getLocalUtilityFolder(user), self.getImageName(user))
    
    def getImageName(self, user):
        self.authUser(user)
        return ("%s_%s.iso" % (self.commonName, self.uuid))
    
    def getPathToHdImage(self, user):
        self.authUser(user)
        
        folder = self.getUtilityFolder(user)
        imgName = "" + self.commonName + ".img"
        return os.path.join(folder, imgName)
    
    def getEmulator(self, user):
        return "/usr/bin/kvm"
    
    def authUser(self, user):
        if user.isAdmin or (self.topology != None and user in self.topology.users) or user.id == self.maintainUser.id:
            return True
        raise dissomniag.UnauthorizedFunctionCall()
    
    def getFreeVNCPortOnHost(self, user, host):
        self.authUser(user)
        selectablePort = 4004
        seen = []
        vmsOnHost = host.virtualMachines
        
        for vm in vmsOnHost:
            if vm.vncPort != None:
                seen.append(int(vm.vncPort))
        
        selected = False
        
        while not selected:
            if not selectablePort in seen:
                selected = True
                break
            else:
                selectablePort = selectablePort + 1
        
        return str(selectablePort)
    
    def addInterfaceToNet(self, user, net):
        self.authUser(user)
        if not isinstance(net, dissomniag.model.generatedNetwork):
            raise TypeError("The net object is not a generatedNetwork.")
        
        if not self.host in net.nodes:
            raise TypeError("The net object does not belong to the current host.")
        addrs = []
        addrs.append(net.getFreeAddress(user))
        
        interfaceName = Interface.getFreeName(user, self)
        
        self.addInterface(user, interfaceName, ipAddresses = addrs, net = net)
    
    def getMaintainanceInterface(self, user):
        self.authUser(user)
        
        for interface in self.interfaces:
            if interface.maintainanceInterface:
                return interface
        return None
    
    def setMaintainanceIp(self, user, ipAddr):
        self.authUser(user)
        self.modMaintainanceIP(user, ipAddr, deleteOld = True, interface = self.getMaintainanceInterface(user))
    
    def recvUpdateLiveClient(self, user, xml):
        self.authUser(user)
        
        if type(xml) == str:
            xml = ElementTree.XML(xml)
            
        maintainIpElem = xml.find("maintainIp")
        if maintainIpElem == None:
            return False
        self.setMaintainanceIp(user, str(maintainIpElem.text))
        self.lastSeenClient = datetime.datetime.now()
        session = dissomniag.Session()
        dissomniag.saveCommit(session)
        return True
    
    def getRPCUri(self, user):
        self.authUser(user)
        maintainIp = str(self.getMaintainanceIP().addr)
        if maintainIp == None:
            raise dissomniag.NoMaintainanceIp()
        return ("https://%s:%s@%s:%s/RPC2" % ("maintain", str(self.uuid), str(maintainIp), str(dissomniag.config.clientConfig.rpcServerPort)))
            
    """
    def start(self, user):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(self, "vm")
        job = dissomniag.taskManager.Job(context, "Start a VM", user = user)
        job.addTask(dissomniag.tasks.createVMOnHost())
        dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
    
    def stop(self, user):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(self, "vm")
        job = dissomniag.taskManager.Job(context, "Stop a VM", user = user)
        job.addTask(dissomniag.tasks.destroyVMOnHost())
        dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
    
    def refresh(self, user):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(self, "vm")
        job = dissomniag.taskManager.Job(context, "Refresh a VM", user = user)
        job.addTask(dissomniag.tasks.statusVM())
        dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
    
    """
    #After status check. Get the vm in a consitent state.
    """
    def operate(self, user):
        if self.state == dissomniag.model.NodeState.RUNTIME_ERROR:
            context = dissomniag.taskManager.Context()
            context.add(self, "vm")
            job = dissomniag.taskManager.Job(context, "Consisteny Operation: Delete VM", user)
            job.addTask(dissomniag.tasks.destroyVMkOnHost())
            dissomniag.taskManager.Dispatcher.addJob(user, job)
            
        elif self.state == dissomniag.model.NodeState.CREATION_ERROR:
            context = dissomniag.taskManager.Context()
            context.add(self, "vm")
            job = dissomniag.taskManager.Job(context, "Consisteny Operation: Try to create vm", user)
            job.addTask(dissomniag.tasks.createVMOnHost())
            dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
    """
    
    def test(self, user, job = None):
        self.authUser(user)
        if job == None:
            self.createTestJob(user)
        else:
            if not isinstance(job, dissomniag.taskManager.Job):
                raise dissomniag.utils.MissingJobObject()
            self.selectInitialStateActor()
            self.runningState.test(job)
        
    def prepare(self, user, job):
        self.authUser(user)
        if not isinstance(job, dissomniag.taskManager.Job):
                raise dissomniag.utils.MissingJobObject()
        self.selectInitialStateActor()
        self.runningState.prepare(job)
        
    def deploy(self, user, job):
        self.authUser(user)
        if not isinstance(job, dissomniag.taskManager.Job):
                raise dissomniag.utils.MissingJobObject()
        self.selectInitialStateActor()
        self.runningState.deploy(job)
        
    def start(self, user, job):
        self.authUser(user)
        if not isinstance(job, dissomniag.taskManager.Job):
                raise dissomniag.utils.MissingJobObject()
        self.selectInitialStateActor()
        self.runningState.start(job)
        
    def stop(self, user, job):
        self.authUser(user)
        if not isinstance(job, dissomniag.taskManager.Job):
                raise dissomniag.utils.MissingJobObject()
        self.selectInitialStateActor()
        self.runningState.stop(job)
        
    def sanityCheck(self, user, job):
        self.authUser(user)
        if not isinstance(job, dissomniag.taskManager.Job):
                raise dissomniag.utils.MissingJobObject()
        self.selectInitialStateActor()
        self.runningState.sanityCheck(job)
    
    def reset(self, user, job):
        self.authUser(user)
        if not isinstance(job, dissomniag.taskManager.Job):
                raise dissomniag.utils.MissingJobObject()
        self.selectInitialStateActor()
        self.runningState.reset(job)
        
    def createLiveClientTestJob(self, user):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(self, "vm")
        job = dissomniag.taskManager.Job(context, "Update lastSeenClient", user = user)
        job.addTask(dissomniag.tasks.updateLiveClientVM())
        dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
    
    def createTestJob(self, user):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(self, "vm")
        job = dissomniag.taskManager.Job(context, "Fetch state of a VM", user = user)
        job.addTask(dissomniag.tasks.statusVM())
        if dissomniag.model.NodeState.NOT_CREATED == self.state or dissomniag.model.NodeState.PREPARE_ERROR == self.state:
            dissomniag.taskManager.Dispatcher.addJobSyncronized(user, dissomniag.model.LiveCdEnvironment(), job)
        else:
            dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
    
    def createPrepareJob(self, user):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(self, "vm")
        job = dissomniag.taskManager.Job(context, "Prepare a VM", user = user)
        job.addTask(dissomniag.tasks.prepareVM())
        if dissomniag.model.NodeState.NOT_CREATED == self.state or dissomniag.model.NodeState.PREPARE_ERROR == self.state:
            dissomniag.taskManager.Dispatcher.addJobSyncronized(user, dissomniag.model.LiveCdEnvironment(), job)
        else:
            dissomniag.taskManager.Dispatcher.addJob(user, job)
        log.info("THREAD PREPARE ID " + str(thread.get_ident()))
        return True
    
    def createDeployJob(self, user):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(self, "vm")
        job = dissomniag.taskManager.Job(context, "Deploy a VM", user = user)
        job.addTask(dissomniag.tasks.deployVM())
        if dissomniag.model.NodeState.NOT_CREATED == self.state or dissomniag.model.NodeState.PREPARE_ERROR == self.state:
            dissomniag.taskManager.Dispatcher.addJobSyncronized(user, dissomniag.model.LiveCdEnvironment(), job)
        else:
            dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
    
    def createStartJob(self, user):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(self, "vm")
        job = dissomniag.taskManager.Job(context, "Start a VM", user = user)
        job.addTask(dissomniag.tasks.startVM())
        if dissomniag.model.NodeState.NOT_CREATED == self.state or dissomniag.model.NodeState.PREPARE_ERROR == self.state:
            dissomniag.taskManager.Dispatcher.addJobSyncronized(user, dissomniag.model.LiveCdEnvironment(), job)
        else:
            dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
    
    def createStopJob(self, user):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(self, "vm")
        job = dissomniag.taskManager.Job(context, "Stop a VM", user = user)
        job.addTask(dissomniag.tasks.stopVM())
        if dissomniag.model.NodeState.NOT_CREATED == self.state or dissomniag.model.NodeState.PREPARE_ERROR == self.state:
            dissomniag.taskManager.Dispatcher.addJobSyncronized(user, dissomniag.model.LiveCdEnvironment(), job)
        else:
            dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
    
    def createResetJob(self, user):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(self, "vm")
        job = dissomniag.taskManager.Job(context, "Reset a VM", user = user)
        job.addTask(dissomniag.tasks.resetVM())
        if dissomniag.model.NodeState.NOT_CREATED == self.state or dissomniag.model.NodeState.PREPARE_ERROR == self.state:
            dissomniag.taskManager.Dispatcher.addJobSyncronized(user, dissomniag.model.LiveCdEnvironment(), job)
        else:
            dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
    
    def createTotalResetJob(self, user):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(self, "vm")
        job = dissomniag.taskManager.Job(context, "Totally Reset a VM", user = user)
        job.addTask(dissomniag.tasks.totalResetVM())
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user, dissomniag.model.LiveCdEnvironment(), job)
        return True
    
    def createSanityDeleteJob(self, user):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(self, "vm")
        job = dissomniag.taskManager.Job(context, "Totally Reset and delete a VM", user = user)
        job.addTask(dissomniag.tasks.totalResetVM())
        job.addTask(dissomniag.tasks.sanityDeleteVM())
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user, dissomniag.model.LiveCdEnvironment(), job)
        return True
        
        
    @staticmethod
    def deleteVm(user, node):
        if node == None or not isinstance(node, VM):
            return False
        node.authUser(user)
        
        #1. Delete LiveCD
        if node.liveCd != None and type(node.liveCd) == dissomniag.model.LiveCd:
            dissomniag.model.LiveCd.deleteLiveCd(user, node.liveCd)
        
        #2. Delete maintainance User
        if node.maintainUser != None and type(node.maintainUser) == dissomniag.auth.User and node.maintainUser.isMaintain:
            session = dissomniag.Session()
            session.delete(node.maintainUser)
            dissomniag.saveCommit(session)

        #2. Delete Interfaces
        for interface in node.interfaces:
            dissomniag.model.Interface.deleteInterface(user, interface)
        
        
        context = dissomniag.taskManager.Context()
        context.add(node, "vm")
        context.add(node, "node")
        job = dissomniag.taskManager.Job(context, description = "Delete a VM", user = user)
        #3. Delete IPAddresses
        job.addTask(dissomniag.tasks.DeleteIpAddressesOnNode())
        
        #4. Delete VM
        job.addTask(dissomniag.tasks.DeleteVM())
        
        #5. Delete all Topology Connection for this VM
        session = dissomniag.Session()
        
        try:
            connections = session.query(dissomniag.model.TopologyConnection).filter(sa.or_(dissomniag.model.TopologyConnection.fromVM == node, dissomniag.model.TopologyConnection.toVM == node)).all()
        except NoResultFound:
            pass
        else:
            for connection in connections:
                session.delete(connection)
            dissomniag.saveCommit(session)
        
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user = user, syncObj = dissomniag.GitEnvironment(), job = job)
        return True
        
    
    @staticmethod
    def deleteNode(user, node):
        return VM.deleteVM(user, node)
    
    
class VMIdentity(VM, dissomniag.Identity):
    isStarted = False
    """
    classdocs
    """
    
    def __new__(cls, *args, **kwargs):
        # Store instance on cls._instance_dict with cls hash
        key = str(hash(cls))
        if not hasattr(cls, '_instance_dict'):
            cls._instance_dict = {}
        if key not in cls._instance_dict:
            cls._instance_dict[key] = \
                super(VMIdentity, cls).__new__(cls, *args, **kwargs)
        return cls._instance_dict[key]


    def start(self):
        if not self.isStarted:
            self.isStarted = True
        else:
            raise dissomniag.Identity.IdentityRestartNotAllowed()
    
    def _tearDown(self):
        pass


