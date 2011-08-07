# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag
from dissomniag.model import *

class Interface(dissomniag.Base):
    __tablename__ = 'interfaces'
    id = sa.Column(sa.Integer, primary_key = True)
    node_id = sa.Column(sa.Integer, sa.ForeignKey('nodes.id'), nullable = False) #One to many style
    name = sa.Column(sa.String(20), nullable = False)
    macAddress = sa.Column(sa.String(17), nullable = False, unique = True)
    
    __table_args_ = (sa.UniqueConstraint('node_id', 'name'))
    
    
    
    """
    classdocs
    """


        
