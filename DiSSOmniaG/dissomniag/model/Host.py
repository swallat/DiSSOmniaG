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

class Host(AbstractNode):
    __tablename__ = 'hosts'
    __mapper_args__ = {'polymorphic_identity': 'host'}
    
    host_id = sa.Column('id', sa.Integer, sa.ForeignKey('nodes.id'), primary_key = True)
    qemuConnector = sa.Column(sa.String(100))
    
    
    """
    classdocs
    """
    
    def __init__(self, commonName, maintainanceIp, administrativeUserName = None):
        pass
    
    
    def addSelfGeneratedNetwork(self, name, ipNetwork):
        pass
        
