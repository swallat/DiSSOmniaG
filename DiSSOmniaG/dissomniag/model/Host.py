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
import sqlalchemy as sa
import sqlalchemy.orm as orm
import lxml
from lxml import etree

import dissomniag
from dissomniag.dbAccess import Base
from dissomniag.model import *

class Host(AbstractNode):
    __tablename__ = 'hosts'
    __mapper_args__ = {'polymorphic_identity': 'host'}
    
    host_id = sa.Column('id', sa.Integer, sa.ForeignKey('nodes.id'), primary_key = True)
    qemuConnector = sa.Column(sa.String(100))
    bridgedInterfaceName = sa.Column(sa.String(10))
    lastChecked = sa.Column(sa.DateTime, nullable = True, default = None)
    configurationMissmatch = sa.Column(sa.Boolean, nullable = True, default = None)#True False None (Not checked Yet)
    libvirtVersion = sa.Column(sa.String(10), nullable = True, default = None) #None (Not installed or not checked Yet) Else Version Number
    kvmUsable = sa.Column(sa.Boolean, nullable = True, default = None) #True False None (not checked yet)
    freeDiskspace = sa.Column(sa.String(20), nullable = True, default = None) #None (not checked yet) FreeDiskSpace
    ramCapacity = sa.Column(sa.String(20), nullable = True, default = None) #None (not checked yet) ramCapacity
    libvirtCapabilities = sa.Column(sa.String, nullable = True, default = None)
    
    """
    classdocs
    """
    def __init__(self, user, commonName, maintainanceIP, bridgedInterfaceName,
                 sshKey = None, administrativeUserName = None):
        if administrativeUserName != None:
            self.administrativeUserName = administrativeUserName
            
        self.qemuConnector = "qemu+ssh://%s@%s/system?no_verify=1,no_tty=1" % (self.administrativeUserName, maintainanceIP)
        
        self.bridgedInterfaceName = bridgedInterfaceName
        
        utilityFolder = dissomniag.config.hostConfig.hostFolder
        
        super(Host, self).__init__(user = user, commonName = commonName,
                                   maintainanceIP = maintainanceIP, sshKey = sshKey,
                                   administrativeUserName = administrativeUserName,
                                   utilityFolder = utilityFolder,
                                   state = dissomniag.model.NodeState.DOWN)
        
        self.checkPingable(user)

    
    def addSelfGeneratedNetwork(self, user, name, ipNetwork = None):
        pass
    
    def authUser(self, user):
        if user.isAdmin:
            return True
        raise dissomniag.UnauthorizedFunctionCall()
    
    def getUserXml(self):
        host = etree.Element("host")
        name = etree.SubElement(host, "name")
        name.text = self.commonName
        uuid = etree.SubElement(host, "uuid");
        uuid.text = self.uuid
        userName = etree.SubElement(host, "userName")
        userName.text = self.administrativeUserName
        utilityFolder = etree.SubElement(host, "utilityFolder");
        utilityFolder.text = self.utilityFolder
        maintainanceIp = etree.SubElement(host, "maintainanceIp");
        maintainanceIp.text = self.getMaintainanceIP().addr;
        state = etree.SubElement(host, "hostState");
        state.text = dissomniag.model.NodeState.getStateName(self.state)
        lastChecked = etree.SubElement(host, "lastChecked")
        lastChecked.text = self.lastChecked;
        return host
        
    
    def checkPingable(self, user):
        
        self.authUser(user)
        
        context = dissomniag.taskManager.Context()
        context.add(self, "host")
        job = dissomniag.taskManager.Job(context, description = "Ping Host to check if it is up.", user = user)
        job.addTask(dissomniag.tasks.HostTasks.CheckHostUpTask())
        dissomniag.taskManager.Dispatcher.addJob(user, job)
        
    def checkFull(self, user):
        
        self.authUser(user)
        
        context = dissomniag.taskManager.Context()
        context.add(self, "host")
        job = dissomniag.taskManager.Job(context, description = "CheckUp all needed Parameters of a Host", user = user)
        job.addTask(dissomniag.tasks.HostTasks.CheckHostUpTask())
        job.addTask(dissomniag.tasks.HostTasks.checkLibvirtVersionOnHost())
        job.addTask(dissomniag.tasks.HostTasks.checkKvmOnHost())
        job.addTask(dissomniag.tasks.HostTasks.checkUtilityDirectory())
        job.addTask(dissomniag.tasks.HostTasks.getFreeDiskSpaceOnHost())
        job.addTask(dissomniag.tasks.HostTasks.getRamCapacityOnHost())
        job.addTask(dissomniag.tasks.HostTasks.gatherLibvirtCapabilities())
        dissomniag.taskManager.Dispatcher.addJob(user, job)        
        
    def modBridgedInterfaceName(self, user, newName):
        self.authUser(user)
        if len(newName) > 10:
            return False
        else:
            session = dissomniag.Session()
            self.bridgedInterfaceName = newName
            dissomniag.saveCommit(session)
            return True
        
    def makeFullCheck(self, user):
        self.authUser(user)
        
        context = dissomniag.taskManager.Context()
        context.add(self, "host")
        job = dissomniag.taskManager.Job(context, description = "Check Host Job", user = user)
        
        job.addTask(dissomniag.tasks.CheckHostUpTask())
        job.addTask(dissomniag.tasks.checkLibvirtVersionOnHost())
        job.addTask(dissomniag.tasks.checkKvmOnHost())
        job.addTask(dissomniag.tasks.getFreeDiskSpaceOnHost())
        job.addTask(dissomniag.tasks.getRamCapacityOnHost())
        
        dissomniag.taskManager.Dispatcher.addJob(user, job)
        
    @staticmethod
    def deleteHost(user, node):
        if not isinstance(node, Host):
            return False
        
        node.authUser(user)
        #1. Delete all Topologies on Host
        
        session = dissomniag.Session()
        try:
            topologies = session.query(dissomniag.model.Topology).filter(dissomniag.model.Topology.host == node).all()
        except NoResultFound:
            pass
        
        for topology in topologies:
            dissomniag.model.Topology.deleteTopology(topology)
        
        context = dissomniag.taskManager.Context()
        context.add(node, "host")    
        job = dissomniag.taskManager.Job(context, description = "delete Host Job", user = user)
        
        #2. Delete all VM's
        job.addTask(dissomniag.tasks.HostTasks.DeleteExistingVMsOnHost())
        
        #3. Delete all Nets
        job.addTask(dissomniag.tasks.HostTasks.DeleteExistingNetsOnHost())
        
        #4. Delete Node
        job.addTask(dissomniag.tasks.HostTasks.DeleteHost())
        
        dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
    
    @staticmethod
    def deleteNode(user, node):
        return Host.deleteHost(user, node)
