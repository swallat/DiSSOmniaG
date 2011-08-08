# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import logging
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import ipaddr

import dissomniag
from dissomniag.model import *

log = logging.getLogger("model.IpAddress")

class NoIpv6Mask(Exception):
    pass

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
    
    def __init__(self, ipAddrOrNet, node):
        session = dissomniag.Session()
        
        if type(ipAddrOrNet) == str:
            ipAddrOrNet = ipaddr.IPNetwork(ipAddrOrNet)
        
        self.node = node
        
        self.addr = str(ipAddrOrNet.ip)
        if (ipAddrOrNet.version == 4):
            self.isV6 = False
        elif (ipAddrOrNet.version == 6):
            self.isV6 = True
        
        if (ipAddrOrNet.prefixlen < ipAddrOrNet.max_prefixlen):
            found = False
            try:
                networks = session.query(Network).filter(Network.netAddress == str(ipAddrOrNet.network)).filter(Network.netMask == str(ipAddrOrNet.netmask)).all()
                for network in networks:
                    if node in network.nodes:
                        found = True # Net is associated with actual node, there is no need to create a new Net 
            except NoResultFound:
                found = False
            finally:
                if found == False:
                    self.network = Network(ipAddrOrNet, node)
        session.add(self)
        session.commit()
        
    
    @staticmethod
    def parseIpv6Netmask(longNetmask):
        result = 0
        fBefore = True
        nm = longNetmask.split(":")
        if len(nm) < 3:
            raise NoIpv6Mask()
        
        for block in nm:
            for value in block:
                if fBefore:
                    if value == 'f':
                        result += 4
                        continue
                    elif value == 'e':
                        result += 3
                    elif value == 'c':
                        result += 2
                    elif value == '8':
                        result += 1
                    fBefore = False
                else:
                    if value != '0':
                        raise NoIpv6Mask()
        return str(result)
                        
                
        

        
        


        
