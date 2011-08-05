# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag

class Interface(dissomniag.Base):
    __tablename__ = 'interfaces'
    id = sa.Column(sa.Integer, primary_key = True)
    macAddress = sa.Column(sa.String(17), nullable = False, unique = True)
    name = sa.Column(sa.String(20), nullable = False)
    ipAddresses = orm.relationship('ipAddresses', backref = "interface") # One to many style
    node_id = sa.Column(sa.Integer, sa.ForeignKey('nodes.id')) #One to many style
    
    
    """
    classdocs
    """


        
