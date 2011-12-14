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
    
    host_id = sa.Column(sa.Integer, sa.ForeignKey('hosts.id'))
    host = orm.relationship("Host", backref = "topologies") # Many to one style
    virtualMachines = orm.relationship("VM", backref = "topology")
    
    users = orm.relationship('User', secondary = user_topology, backref = 'topologies')
    
    connections = orm.relationship("TopologyConnection", backref = "topology")
    
    def authUser(self, user):
        if user in self.users or user.isAdmin:
            return True
        raise dissomniag.UnauthorizedFunctionCall()
    
    """
    classdocs
    """
    
    @staticmethod
    def deleteTopology(user, topo):
        if topo == None or type(topo) != Topology:
            return False
        topo.authUser(user)
        
        #1. Delete VM's
        for vm in topo.virtualMachines:
            dissomniag.model.VM.deleteVM(user, vm)
            
        #2. Delete Networks's
        for net in topo.generatedNetworks:
            dissomniag.model.generatedNetwork.deleteNetwork(user, net)
        
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


        
class TopologyConnection(dissomniag.Base):
    __tablename__ = 'topologyConnections'
    id = sa.Column(sa.Integer, primary_key = True)
    fromVM_id = sa.Column(sa.Integer, sa.ForeignKey('vms.id'), nullable = False)
    fromVM = orm.relationship("VM", primaryjoin = "TopologyConnection.fromVM_id == VM.vm_id")
    viaGenNetwork_id = sa.Column(sa.Integer, sa.ForeignKey('networks.id'), nullable = False)
    viaGenNetwork = orm.relationship("generatedNetwork", backref = "connections")
    toVM_id = sa.Column(sa.Integer, sa.ForeignKey('vms.id'), nullable = False)
    toVM = orm.relationship("VM", primaryjoin = "TopologyConnection.toVM_id == VM.vm_id")
    topology_id = sa.Column(sa.Integer, sa.ForeignKey('topologies.id'))
    """
    classdocs
    """
    
    @staticmethod
    def deleteConnection(user, connection):
        if connection == None or type(connection) != TopologyConnection:
            return False
        connection.topology.authUser(user)
        try:
            TopologyConnection.deleteConnectionUnsafe(user, connection)
        except Exception:
            return False
        return True
    
    """
    May raise SqlAlchemy Exception
    """
    @staticmethod
    def deleteConnectionUnsafe(user, connection):
        if connection == None or type(connection) != TopologyConnection:
            return False
        connection.topology.authUser(user)
        
        session = dissomniag.Session()
        session.delete(connection)
        dissomniag.saveCommit(session)
        
