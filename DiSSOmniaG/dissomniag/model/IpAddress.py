# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import logging
import sqlalchemy as sa
import sqlalchemy.orm as orm
import ipaddr

import dissomniag
from dissomniag.model import *

log = logging.getLogger("model.IpAddress")

class IpAddress(dissomniag.Base):
    __tablename__ = 'ipAddresses'
    id = sa.Column(sa.Integer, primary_key = True)
    addr = sa.Column(sa.String(39), nullable = False)
    isV6 = sa.Column(sa.Boolean, nullable = False, default = False)
    node_id = sa.Column(sa.Integer, sa.ForeignKey('nodes.id'), nullable = False) #One to many style, da immer gesichert sein muss, dass eine IP auf einem Host nur einmal vorkommen kann. ROUTING
    node = orm.relationship('AbstractNode', primaryjoin = "IpAddress.node_id == AbstractNode.id", backref = "ipAddresses") #One to Many style
    interface_id = sa.Column(sa.Integer, sa.ForeignKey('interfaces.id')) # One to many style
    interface = orm.relationship('Interface', backref = 'ipAddresses')
    network_id = sa.Column(sa.Integer, sa.ForeignKey('networks.id')) # Many to One style
    network = orm.relationship('Network', backref = 'connectedInterfaces') # Many to One style
    topology_id = sa.Column(sa.Integer, sa.ForeignKey('topologies.id')) # Many to one style
    topology = orm.relationship('Topology', backref = 'ipAddresses')
    __table_attr__ = (sa.UniqueConstraint('addr', 'node_id', name = "uniqueAddressPerNode"))
    
    """
    classdocs
    """

        
        


        
