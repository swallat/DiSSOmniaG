# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm
import ipaddr
import lxml
import uuid
import re

import dissomniag
from dissomniag.dbAccess import Base
from dissomniag.model import *


node_network = sa.Table('node_network', Base.metadata,
                          sa.Column('node_id', sa.Integer, sa.ForeignKey('nodes.id')),
                          sa.Column('network_id', sa.Integer, sa.ForeignKey('networks.id')),
)

class Network(dissomniag.Base):
    __tablename__ = "networks"
    id = sa.Column(sa.Integer, primary_key = True)
    uuid = sa.Column(sa.String(36), nullable = False, unique = True)
    name = sa.Column(sa.String, nullable = False)
    netAddress = sa.Column(sa.String(39), nullable = False)
    netMask = sa.Column(sa.String(39), nullable = False) 
    type = sa.Column('type', sa.String(50))
    __mapper_args__ = {'polymorphic_on': type}
    """
    classdocs
    """
    
    def __init__(self, user, network, node = None, name = None):
        
        session = dissomniag.Session()
        if type(network) == str:
            network = ipaddr.IPNetwork(network)
        
        if name == None:
            name = "PublicNetwork"
        self.uuid = str(uuid.uuid4())
        self.name = name
        
        
        self.netAddress = str(network.network)
        self.netMask = str(network.netmask)
        session.add(self)
        session.commit()
        if node != None:
            self.nodes.append(node)
            session.commit()
            
    @staticmethod
    def deleteNetwork(user, network):
        pass
    
    @staticmethod
    def generateDeleteNetworkJob(user, network):
        pass
    
    def authUser(self, user):
        if user.isAdmin:
            return True
        raise dissomniag.UnauthorizedFunctionCall()

class generatedNetwork(Network):
    __mapper_args__ = {'polymorphic_identity': 'generatedNetwork'}
    topology_id = sa.Column(sa.Integer, sa.ForeignKey('topologies.id'))
    topology = orm.relationship("Topology", backref = "generatedNetworks")
    dhcpAddress_id = sa.Column(sa.Integer, sa.ForeignKey('ipAddresses.id'))
    dhcpAddress = orm.relationship("IpAddress", primaryjoin = "IpAddress.id == generatedNetwork.dhcpAddress_id")
    withQos = sa.Column(sa.Boolean, nullable = False, default = False)
    inboundAverage = sa.Column(sa.Integer)
    inboundPeak = sa.Column(sa.Integer)
    inboundBurst = sa.Column(sa.Integer)
    outboundAverage = sa.Column(sa.Integer)
    outboundPeak = sa.Column(sa.Integer)
    outboundBurst = sa.Column(sa.Integer)
    
    namePrefix = "virdiss"
    ranges = {"255": range(1, 255),
                  "128": range(1, 128),
                  "64": range(1, 64),
                  "32": range(1, 32),
                  "16": range(1, 16),
                  "8": range(1, 8),
                  "4": range(1, 4),
                  "2": range(1, 2),
                  "1": range(1, 2),
                  "0": range(1, 2)}
    """
    classdocs
    """
    
    def __init__(self, user, network, topology = None, node = None):
        name = self.findEmptyName()
        if topology:
            self.topology = topology
        super(generatedNetwork, self).__init__(user, network, node = node, name = name)
        self.setDhcpServerAddress(user)
        session = dissomniag.Session()
        session.add(self)
        session.commit()
        
    def findEmptyName(self):
        session = dissomniag.Session()
        name = None
        existingNames = None
        numberPattern = "([1-9]?[0-9]*)$"
        try:
            existingNames = session.query(generatedNetwork.name).all()
        except NoResultFound:
            pass
        
        if existingNames == None:
            name = ("%s%d" % (self.namePrefix, 0))
        else:
            seen = []
            for names in existingNames:
                seen.append(int(re.search(numberPattern, str(names[0])).group[0]))
            seen = sorted(seen)
            found = False
            last = None
            for value in seen:
                if last == None:
                    last = value
                elif last == (value - 1):
                    last = value
                else:
                    found = True
                    last = value
                    break
            if not found:
                last = last + 1
            
            name = ("%s%d" % (self.namePrefix, last))
             
        return name
    
    def setDhcpServerAddress(self, user):
        self.authUser(user)
        ip = self.netAddress.split(".")
        ip[3] = str(int(ip[3]) + 1)
        networkString = "%s/%s" % (self.netAddress, self.netMask)
        net = ipaddr.IPNetwork(networkString)
        ipAddr = ".".join(ip)
        ip = ipaddr.IPAddress(ipAddr)
        if ip in net:
            ipString = "%s/%s" % (self.ip, self.netMask)
            self.dhcpAddress = IpAddress(user, ipString, isDhcpAddress = True)
        return self.dhcpAddress
         
    def getFreeAddress(self, user):
        self.authUser(user)
        net = self.netAddress.split(".")
        netString = ("%s/%s" % (self.netAddress, self.netMask))
        hm = ipaddr.IPNetwork(netString).hostmask.split(".")
        found = False
        ip = None
        for block in range(3, -1, -1):
            if int(hm[block]) == 0:
                return None
            ip = self._findFree(net, hm, block)
            if ip != None:
                found = True
                break
        if found:
            return ("%s/%s" % (".".join(ip), self.netMask))
        else:
            return None
    
    def _findFree(self, net = [], hostMask = [], block = 3):
        address = net
        continueTo = 1
        if block == 3:
            if ".".join(address) == self.netMask:
                address[3] = str(int(address[3]) + 2)
                continueTo = 3 # Go over netAddress and dhcpAddress
            for i in self.ranges[hostMask[3]]:
                if (i < continueTo):
                    continue
                if self.checkFreeAddress:
                    return address
                address[3] = str(int(net[3]) + i)
            return None
        elif block == 2:
            for i in self.ranges[hostMask[2]]:
                address[2] = str(int(net[2]) + i)
                address = self._findFree(address, hostMask, 3)
                if address != None:
                    return address
            return None
        elif block == 1:
            for i in self.ranges[hostMask[1]]:
                address[1] = str(int(net[1]) + i)
                address = self._findFree(address, hostMask, 2)
                if address != None:
                    return address
            return None
        elif block == 0:
            for i in self.ranges[hostMask[0]]:
                address[0] = str(int(net[0]) + i)
                address = self._findFree(address, hostMask, 1)
                if address != None:
                    return address
            return None
              
    def checkFreeAddress(self, user, address):
        self.authUser(user)
        netString = ("%s/%s" % (self.netAddress, self.netMask))
        self.net = ipaddr.IPNetwork(netString)
        
        if not ipaddr.IPAddress(address) in self.net:
            return False
        
        for addr in self.ipAddresses:
            if addr.addr == address:
                return False
        
        return True
    
    def getLibVirtXML(self, user):
        root = lxml.etree.Element("network")
        name = lxml.etree.SubElement(root, "name")
        name.text = self.name
        uuid = lxml.etree.SubElement(root, "uuid")
        uuid.text = self.uuid
        if self.withQos:
            bandwith = lxml.SubElement(root, 'bandwith')
            inbound = lxml.SubElement(bandwith, 'inbound')
            inboundAttrib = inbound.attrib
            inboundAttrib['average'] = str(self.inboundAverage)
            inboundAttrib['peak'] = str(self.inboundPeak)
            inboundAttrib['burst'] = str(self.inboundBurst)
            outbound = lxml.SubElement(bandwith, 'outbound')
            outboundAttrib = outbound.attrib
            outboundAttrib['average'] = str(self.outboundAverage)
            outboundAttrib['peak'] = str(self.outboundPeak)
            outboundAttrib['burst'] = str(self.outboundBurst)
        
        
                
    def setQos(self, user, inboundAvg, inboundPeak, inboundBurst, outboundAvg, outboundPeak, outboundBurst):
        self.authUser(user)
        self.inboundAverage = inboundAvg
        self.inboundPeak = inboundPeak
        self.inboundBurst = inboundBurst
        self.outboundAverage = outboundAvg
        self.outboundPeak = outboundPeak
        self.outboundBurst = outboundBurst
        self.withQos = True
        
    def modifyQos(self, user, inboundAvg = None, inboundPeak = None, inboundBurst = None, outboundAvg = None, outboundPeak = None, outboundBurst = None):
        self.authUser(user)
        if not self.withQos:
            return False
        if inboundAvg == None and inboundPeak == None and inboundBurst == None and outboundAvg == None and outboundPeak == None and outboundBurst == None:
            return False
        if inboundAvg:
            self.inboundAverage = inboundAvg
        if inboundPeak:
            self.inboundPeak = inboundPeak
        if inboundBurst:
            self.inboundBurst = inboundBurst
        if outboundAvg:
            self.outboundAverage = outboundAvg
        if outboundPeak:
            self.outboundPeak = outboundPeak
        if outboundBurst:
            self.outboundBurst = outboundBurst
        
        return True
    
    def delQos(self, user):
        self.inboundAverage = None
        self.inboundPeak = None
        self.inboundBurst = None
        self.outboundAverage = None
        self.outboundPeak = None
        self.outboundBurst = None
        self.withQos = False
        
        
    
    def authUser(self, user):
        if self.topology != None:
            if user in self.topology.users:
                return True
        return super(generatedNetwork, self).authUser(user)
    
    @staticmethod
    def cleanUpGeneratedNetworks(user):
        pass
    
    @staticmethod
    def generateJobCleanUpGeneratedNetworks(user):
        pass
    
    @staticmethod
    def getFreeNetString(user, host):
        """
        All nets are /24 Nets.
        """
        
        host.authUser(user)
        
        if type(host) != dissomniag.model.Host:
            raise dissomniag.LogicalError()
        
        blockedNets = []
        for net in host.networks:
            if type(net) != generatedNetwork:
                continue
            if not net.netMask.startswith("10.10."):
                continue
            netId = net.netMask.split()
            blockedNets.append(netId[2])
        
        foundNet = None
        for net in range(0, 255):
            if net not in blockedNets:
                foundNet = net
                break
        if foundNet != None:
            returnNet = ("10.10.%d.0/255.255.255.0" % foundNet)
            return returnNet
        else:
            return None
        
            


        
