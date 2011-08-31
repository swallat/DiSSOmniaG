# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
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
        session.commit()
        
