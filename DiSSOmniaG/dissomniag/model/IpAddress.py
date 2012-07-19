# -*- coding: utf-8 -*-
# DiSSOmniaG (Distributed Simulation Service wit OMNeT++ and Git)
# Copyright (C) 2011, 2012 Sebastian Wallat, University Duisburg-Essen
# 
# Based on an idea of:
# Sebastian Wallat <sebastian.wallat@uni-due.de, University Duisburg-Essen
# Hakim Adhari <hakim.adhari@iem.uni-due.de>, University Duisburg-Essen
# Martin Becke <martin.becke@iem.uni-due.de>, University Duisburg-Essen
#
# DiSSOmniaG is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DiSSOmniaG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DiSSOmniaG. If not, see <http://www.gnu.org/licenses/>
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
    isDhcpAddress = sa.Column(sa.Boolean, nullable = False, default = False)
    isMaintainance = sa.Column(sa.Boolean, nullable = False, default = False)
    node_id = sa.Column(sa.Integer, sa.ForeignKey('nodes.id')) #One to many style, da immer gesichert sein muss, dass eine IP auf einem Host nur einmal vorkommen kann. ROUTING
    node = orm.relationship('AbstractNode', primaryjoin = "IpAddress.node_id == AbstractNode.id", backref = "ipAddresses") #One to Many style
    interface_id = sa.Column(sa.Integer, sa.ForeignKey('interfaces.id')) # One to many style
    interface = orm.relationship('Interface', backref = 'ipAddresses')
    network_id = sa.Column(sa.Integer, sa.ForeignKey('networks.id')) # Many to One style
    network = orm.relationship('Network', primaryjoin = "IpAddress.network_id == Network.id", backref = 'ipAddresses') # Many to One style
    __table_attr__ = (sa.UniqueConstraint('addr', 'node_id', name = "uniqueAddressPerNode"))
    
    """
    classdocs
    """
    
    def __init__(self, user, ipAddrOrNet, node = None, isDhcpAddress = False, net = None):
        session = dissomniag.Session()
        
        if not isinstance(ipAddrOrNet, (ipaddr.IPv4Network, ipaddr.IPv6Network)):
            ipAddrOrNet = ipaddr.IPNetwork(ipAddrOrNet)
        
        if node:
            self.node = node
        
        self.isDhcpAddress = isDhcpAddress
        
        self.addr = str(ipAddrOrNet.ip)
        if (ipAddrOrNet.version == 4):
            self.isV6 = False
        elif (ipAddrOrNet.version == 6):
            self.isV6 = True
        
        if (ipAddrOrNet.prefixlen < ipAddrOrNet.max_prefixlen) and not net:
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
                    self.network = Network(user, ipAddrOrNet, node)
        elif isinstance(net, (dissomniag.model.Network, dissomniag.model.generatedNetwork)):
            self.network = net
        session.add(self)
        dissomniag.saveCommit(session)
        
    def authUser(self, user):
        return self.node.authUser(user)
    
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

    @staticmethod
    def deleteIpAddress(user, ipAddress, isAdministrative = False):
        session = dissomniag.Session()
        session.delete(ipAddress)
        dissomniag.saveFlush(session)
    
    @staticmethod
    def checkValidIpAddress(ipAddress):
        try:
            ipaddr.IPNetwork(ipAddress)
        except ValueError:
            return False
        else:
            return True
                
        

        
        


        
