# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag
import Networks
import Host
import Topology

class Network(dissomniag.Base):
    __tablename__ = "networks"
    id = sa.Column(sa.Integer, primary_key = True)
    netAddress = sa.Column(sa.String(39), nullable = False, unique = True)
    netMask = sa.Column(sa.String(39), nullable = False)
    discriminator = sa.Column('type', sa.String(50))
    __mapper_args__ = {'polymorphic_on': discriminator}
    """
    classdocs
    """


class generatedNetwork(Network):
    __mapper_args__ = {'polymorphic_identity': 'generatedNetwork'}
    host_id = sa.Column(sa.Integer, sa.ForeignKey('hosts.id'))
    topology_id = sa.Column(sa.Integer, sa.ForeignKey('topologies.id'))
    """
    classdocs
    """


        
