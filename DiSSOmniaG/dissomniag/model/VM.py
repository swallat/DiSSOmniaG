# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag
import AbstractNode
import Topology
import Host

class VM(AbstractNode.AbstractNode):
    __tablename__ = 'vms'
    __mapper_args__ = {'polymorphic_identity': 'vm'}
    vm_id = sa.Column('id', sa.Integer, sa.ForeignKey('nodes.id'), primary_key = True)
    ramSize = sa.Column(sa.String, default = "1024MB", nullable = False)
    hdSize = sa.Column(sa.String, default = "5GB")
    useHD = sa.Column(sa.Boolean, default = False, nullable = False)
    enableVNC = sa.Column(sa.Boolean, default = False, nullable = False)
    vncAddress = sa.Column(sa.String)
    vncPassword = sa.Column(sa.String(40))
    dynamicAptList = sa.Column(sa.String)
    topology_id = sa.Column(sa.Integer, sa.ForeignKey('topologies.id'))
    host_id = sa.Column(sa.Integer, sa.ForeignKey('hosts.id'))
    liveCd_id = sa.Column(sa.Integer, sa.ForeignKey('livecds.id'))
    liveCd = orm.relationship("LiveCd", backref = orm.backref('livecds', uselist = False))
    
    """
    classdocs
    """


