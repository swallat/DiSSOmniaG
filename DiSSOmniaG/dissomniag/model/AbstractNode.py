# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import abc
import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag
from dissomniag.model import *

class NodeState:
    UP = 0
    DOWN = 1
    NOT_CREATED = 2
    ERROR = 3
    
    @staticmethod
    def getStateName(state):
        if state == NodeState.UP:
            return "UP"
        elif state == NodeState.DOWN:
            return "DOWN"
        elif state == NodeState.NOT_CREATED:
            return "NOT CREATED"
        elif state == NodeState.ERROR:
            return "ERROR"
        else:
            return None

class AbstractNode(dissomniag.Base):
    __tablename__ = "nodes" 
    id = sa.Column(sa.Integer, primary_key = True)
    commonName = sa.Column(sa.String(40), nullable = False, unique = True)
    sshKey_id = sa.Column(sa.Integer, sa.ForeignKey('sshNodeKeys.id')) #One to One
    sshKey = orm.relationship("SSHNodeKey", backref = orm.backref("node", uselist = False))
    administrativeUserName = sa.Column(sa.String(), default = "root", nullable = False)
    utilityFolder = sa.Column(sa.String(200), nullable = True)
    state = sa.Column(sa.Integer, sa.CheckConstraint("0 <= state < 4", name = "nodeState"), nullable = False)
    interfaces = orm.relationship('Interface', backref = "node") #One to Many style
    
    networks = orm.relationship('Network', secondary = node_network, backref = 'nodes')
    
    discriminator = sa.Column('type', sa.String(50), nullable = False)
    __mapper_args__ = {'polymorphic_on': discriminator}
    """
    classdocs
    """
    
    


        
