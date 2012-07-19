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
from dissomniag.model import *


user_topology = sa.Table('user_topology', dissomniag.Base.metadata,
           sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
           sa.Column('topology_id', sa.Integer, sa.ForeignKey('topologies.id')),
)

class Topology(dissomniag.Base):
    __tablename__ = 'topologies'
    id = sa.Column(sa.Integer, primary_key = True)
    name = sa.Column(sa.String, nullable = False)
    #virtualMachines = orm.relationship("VM", backref = "topology")
    #generatedNetworks = orm.relationship("GeneratedNetwork", backref = "topology")
    users = orm.relationship('User', secondary = user_topology, backref = 'topologies')
    
    def authUser(self, user):
        if user in self.users or user.isAdmin:
            return True
        raise dissomniag.UnauthorizedFunctionCall()
    
    """
    classdocs
    """
    
    def getShortXml(self, user):
        root = etree.Element("topology")
        name = etree.SubElement(root, "name")
        name.text = str(self.name)
        userList = etree.SubElement(root, "user-list")
        for user in self.users:
            userName = etree.SubElement(userList, "user-name")
            userName.text = str(user.username)
        return root
    
    def getFullXml(self, user):
        root = self.getShortXml(user)
        
        for vm in self.vms:
            root.append(vm.getGuiXml(user))
            
        for genNet in self.generatedNetworks:
            root.append(genNet.getGuiXml(user))
        
        for generalNet in self.generalNetworks:
            root.append(generalNet.getGuiXml(user))
            
        return root
    
    
    @staticmethod
    def deleteTopology(user, topo):
        if topo == None or type(topo) != Topology:
            return False
        topo.authUser(user)
        
        #1. Delete VM's
        for vm in topo.vms:
            dissomniag.model.VM.deleteVM(user, vm)
            
        #2. Delete Networks's
        for net in topo.generatedNetworks:
            dissomniag.model.generatedNetwork.deleteNetwork(user, net)
            
        session = dissomniag.Session()
        #3. Delete General Network's
        for net in topo.generalNetworks:
            session.delete(net)

        dissomniag.saveCommit(session)
        
        context = dissomniag.taskManager.Context()
        context.add(topo, "topology") 
        
        job = dissomniag.taskManager.Job(context = context, description = "Delete Topology", user = user)
        #3. Delete Connections
        job.addTask(dissomniag.tasks.DeleteTopologyConnections())
        job.addTask(dissomniag.tasks.DeleteExistingVMsOnHost())
        job.addTask(dissomniag.tasks.DeleteExistingNetsOnHost())
        
        #4. Delete Topology
        job.addTask(dissomniag.tasks.DeleteTopology())
        
        dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
        
