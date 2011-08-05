# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag
import AbstractNode
import Network

class Host(AbstractNode.AbstractNode):
    __tablename__ = 'hosts'
    __mapper_args__ = {'polymorphic_identity': 'host'}
    
    host_id = sa.Column('id', sa.Integer, sa.ForeignKey('nodes.id'), primary_key = True)
    qemuConnector = sa.Column(sa.String(100))
    virtualMachines = orm.relationship("VM", backref = "host")
    generatedNetworks = orm.relationship('generatedNetwork', backref = "host")
    
    """
    classdocs
    """


        
