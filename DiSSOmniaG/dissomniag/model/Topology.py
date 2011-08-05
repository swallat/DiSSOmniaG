# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag
import VM
import dissomniag.auth.User
import Network
import Interface

user_topology = sa.Table('user_topology', dissomniag.Base.metadata,
           sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
           sa.Column('topology_id', sa.Integer, sa.ForeignKey('topologies.id')),
)

class Topology(dissomniag.Base):
    __tablename__ = 'topologies'
    id = sa.Column(sa.Integer, primary_key = True)
    name = sa.Column(sa.String, nullable = False)
    users = orm.relationship('User', secondary = user_topology, backref = 'topologies')
    virtualMachines = orm.relationship("VM", backref = "topology")
    createdNetworks = orm.relationship("generatedNetwork", backref = "topology")
    connections = orm.relationship("TopologyConnection", backref = "topology")
    
    """
    classdocs
    """


        
class TopologyConnection(dissomniag.Base):
    __tablename__ = 'topologyConnections'
    id = sa.Column(sa.Integer, primary_key = True)
    fromVM_id = sa.Column(sa.Integer, sa.ForeignKey('vms.id'), nullable = False)
    fromVM = orm.relationship("VM", backref = "connections")
    viaGenNetwork_id = sa.Column(sa.Integer, sa.ForeignKey('generatedNetwork.id'), nullable = False)
    viaGenNetwork = orm.relationship("generatedNetwork", backref = "connections")
    toVM_id = sa.Column(sa.Integer, sa.ForeignKey('vms.id'), nullable = False)
    toVM = orm.relationship("VM", backref = "connections")
    topology_id = sa.Column(sa.Integer, sa.ForeignKey('topologies.id'))
    
    """
    classdocs
    """

        
