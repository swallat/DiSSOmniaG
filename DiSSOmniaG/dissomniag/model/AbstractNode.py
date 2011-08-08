# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import abc
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import logging
import netifaces

import dissomniag
from dissomniag.model import *

log = logging.getLogger("model.AbstractNode")

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
    
    
    def parseLocalInterfaces(self):
        excludedInterfaces = ['lo', 'lo0']
        excludedIps = ['fe80:', '172.0.0.1']
        interfaceCodes = {"mac" : 17, 'ipv4': 2 , 'ipv6' : 10}
        session = dissomniag.Session()
        interfaces = netifaces.interfaces()
        
        savedInterfaces = []
        
        for interface in interfaces:
            if interface in excludedInterfaces:
                continue
            myInt = None
            
            addresses = netifaces.ifaddresses(interface)
            for key in addresses:
                if key == interfaceCodes['mac'] and myInt == None:
                    for address in addresses[key]:
                        try:
                            myInt = session.query(Interface).filter(Interface.macAddress == address['addr']).one()
                            continue # Checl if IP have changed
                        except NoResultFound:
                            myInt = Interface(self, interface, address['addr'])
                elif (key == interfaceCodes['ipv4'] or key == interfaceCodes['ipv6']) and myInt != None:
                    
                    for address in addresses[key]:
                        found = False
                        for exclude in excludedIps:
                            if address['addr'].startswith(exclude):
                                found = True
                                break
                        if found:
                            continue
                        if key == interfaceCodes['ipv4']:
                            ipFullString = ("%s/%s" % (address['addr'], address['netmask']))
                        else:
                            try:
                                ipv6Netmask = dissomniag.model.IpAddress.parseIpv6Netmask(address['netmask'])
                            except dissomniag.model.NoIpv6Mask:
                                continue
                            else:
                                ipFullString = ("%s/%s" % (address['addr'], ipv6Netmask))
                        
                        
                        myInt.addIp(ipFullString)
                    
                else:
                    print("parseLocalInterfaces tried to add a seond mac to a interface or tried to add a ip to a non existing interface")
            if myInt != None:
                self.interfaces.append(myInt)
                savedInterfaces.append(myInt)
            # Delete unused Interfaces
            for interface in self.interfaces:
                if not (interface in savedInterfaces):
                    session.delete(interface)
            
                    
    
    


        
