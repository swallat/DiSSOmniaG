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

import dissomniag
from dissomniag.model import *

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
    topology_id = sa.Column(sa.Integer, sa.ForeignKey('topologies.id'))
    host_id = sa.Column(sa.Integer, sa.ForeignKey('hosts.id'))
    host = orm.relationship("Host", primaryjoin = "VM.host_id == Host.host_id", backref = "virtualMachines")
    liveCd_id = sa.Column(sa.Integer, sa.ForeignKey('livecds.id'))
    #liveCd = orm.relationship("LiveCd", backref = orm.backref('livecds', uselist = False))
    liveCd = orm.relationship("LiveCd", backref = "vm")
    
    """
    classdocs
    """
    
    def __init__(self, user, commonName, host):
        
        if host != None and isinstance(host, dissomniag.model.Host):
            self.host = host
        
        super(VM, self).__init__(user, commonName, state = dissomniag.model.NodeState.NOT_CREATED)
        self.vncPort = self.getFreeVNCPortOnHost(user, host)
        
        interface = self.addInterface(user, "maintain")
        interface.maintainanceInterface = True
        
        session = dissomniag.Session()    
        session.commit()
    
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
        cdromSourceAttrib["file"] = str(self.getPathToCdImage(user))
        
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
            
            interfSource = etree.SubElement(interf, "source")
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
        vncAttrib["keymap"] = "de"
        
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
    
    def getUtilityFolder(self, user):
        self.authUser(user)
        
        allVmsFolder = os.path.join(self.host.utilityFolder, dissomniag.config.hostConfig.vmSubdirectory)
        vmFolder = os.path.join(allVmsFolder, self.commonName)
        return vmFolder
    
    def getPathToCdImage(self, user):
        self.authUser(user)
        
        folder = self.getUtilityFolder(user)
        ###
        # ToDo: Edit Name to LiveCd Image Name
        ###
        return os.path.join(folder, "LiveCd.iso")
    
    def getPathToHdImage(self, user):
        self.authUser(user)
        
        folder = self.getUtilityFolder(user)
        imgName = "" + self.commonName + ".img"
        return os.path.join(folder, imgName)
    
    def getEmulator(self, user):
        return "/usr/bin/kvm"
    
    def authUser(self, user):
        if user.isAdmin or (self.topology != None and user in self.topology.users):
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
    After status check. Get the vm in a consitent state.
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
        
        
        
    @staticmethod
    def deleteVm(user, node):
        if node == None or not isinstance(node, VM):
            return False
        node.authUser(user)
        
        #1. Delete LiveCD
        if node.liveCd != None and type(node.liveCd) == dissomniag.model.LiveCd:
            dissomniag.model.LiveCd.deleteLiveCd(node.liveCd)

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
            session.commit()
        
        dissomniag.taskManager.Dispatcher.addJob(user = user, job = job)
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


