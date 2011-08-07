# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag
from dissomniag.dbAccess import Base
from dissomniag.model import *

node_network = sa.Table('node_network', Base.metadata,
                          sa.Column('node_id', sa.Integer, sa.ForeignKey('nodes.id')),
                          sa.Column('network_id', sa.Integer, sa.ForeignKey('networks.id')),
)

class Network(dissomniag.Base):
    __tablename__ = "networks"
    id = sa.Column(sa.Integer, primary_key = True)
    name = sa.Column(sa.String, nullable = False)
    netAddress = sa.Column(sa.String(39), nullable = False)
    netMask = sa.Column(sa.String(39), nullable = False) 
    discriminator = sa.Column('type', sa.String(50))
    __mapper_args__ = {'polymorphic_on': discriminator}
    """
    classdocs
    """


class generatedNetwork(Network):
    __mapper_args__ = {'polymorphic_identity': 'generatedNetwork'}
    topology_id = sa.Column(sa.Integer, sa.ForeignKey('topologies.id'), nullable = False)
    topology = orm.relationship("Topology", backref = "generatedNetworks")
    """
    classdocs
    """


        
