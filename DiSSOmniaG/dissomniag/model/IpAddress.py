# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag
import Interface
import Network

class IpAddress(dissomniag.Base):
    __tablename__ = 'ipAddresses'
    id = sa.Column(sa.Integer, primary_key = True)
    addr = sa.Column(sa.String(39), nullable = False, unique = True)
    netmask = sa.Column(sa.String(39), nullable = False)
    interface_id = sa.Column(sa.Integer, sa.ForeignKey('interfaces.id')) # One to many style
    network_id = sa.Column(sa.Integer, sa.ForeignKey('networks.id')) # Many to One style
    network = orm.relationship('Network', backref = 'connectedInterfaces') # Many to One style
    """
    classdocs
    """


        
