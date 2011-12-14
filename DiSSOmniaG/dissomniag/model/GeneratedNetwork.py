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
import sqlalchemy as sa
import sqlalchemy.orm as orm
import ipaddr
import lxml
from lxml import etree
import uuid
import re

import dissomniag
from dissomniag.dbAccess import Base
from dissomniag.model import *

class MultipleHostException(Exception):
    pass

class GenNetworkState:
    INACTIVE = 0
    CREATED = 1
    RUNTIME_ERROR = 2
    GENERAL_ERROR = 3
    
    @staticmethod
    def getStateName(state):
        if state == GenNetworkState.INACTIVE:
            return "INACTIVE"
        elif state == GenNetworkState.CREATED:
            return "CREATED"
        elif state == GenNetworkState.RUNTIME_ERROR:
            return "RUNTIME_ERROR"
        elif state == GenNetworkState.GENERAL_ERROR:
            return "GENERAL_ERROR"
        else:
            return None
    
    @staticmethod
    def checkIn(state):
        if 0 <= state < 4:
            return True
        else:
            return False

class generatedNetwork(Network):
    __tablename__ = 'genNetworks'
    __mapper_args__ = {'polymorphic_identity': 'generatedNetwork'}
    id = sa.Column('id', sa.Integer, sa.ForeignKey('networks.id'), primary_key = True)
    topology_id = sa.Column(sa.Integer, sa.ForeignKey('topologies.id'))
    topology = orm.relationship("Topology", backref = "generatedNetworks")
    state = sa.Column(sa.Integer, sa.CheckConstraint("0 <= state < 4", name = "genNetState"), nullable = True)
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
    
    def __init__(self, user, network, host, topology = None):
        assert isinstance(host, dissomniag.model.Host)
        name = self.findEmptyName(host)
        if topology:
            self.topology = topology
        assert isinstance(host, dissomniag.model.Host)
        super(generatedNetwork, self).__init__(user = user, network = network, node = host, name = name)
        self.setDhcpServerAddress(user)
        self.state = GenNetworkState.INACTIVE
        session = dissomniag.Session()
        dissomniag.saveCommit(session)
        
    def findEmptyName(self, host):
        name = None
        existingNames = []
        numberPattern = "([1-9]?[0-9]*)$"
        for net in host.networks:
            if not isinstance(net, generatedNetwork):
                continue
            existingNames.append(str(net.name))
            
        
        if not existingNames:
            name = ("%s%d" % (self.namePrefix, 0))
        else:
            seen = []
            for names in existingNames:
                seen.append(int(re.search(numberPattern, names).groups()[0]))
            seen = sorted(seen)
            found = False
            last = None
            for value in seen:
                if last == None: 
                    last = value
                    if value == 1:
                        last = 0
                        found = True
                        break
                    continue
                elif last == (value - 1): 
                    last = value
                    continue 
                else:
                    found = True
                    last = (value - 1) 
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
        dhcpAddress = self.getDhcpServerAddress(user)
        if ip in net:
            ipString = "%s/%s" % (str(ip), str(self.netMask))
            if dhcpAddress != None:
                dhcpAddress.isDhcpAddress = False
            dhcpAddress = dissomniag.model.IpAddress(user, ipString, isDhcpAddress = True, net = self)
            dhcpAddress.isDhcpAddress = True
        return dhcpAddress
    
    def getDhcpServerAddress(self, user):
        self.authUser(user)
        for ip in self.ipAddresses:
            if ip.isDhcpAddress:
                return ip
        return None
         
    def getFreeAddress(self, user):
        self.authUser(user)
        netString = ("%s/%s" % (self.netAddress, self.netMask))
        net = ipaddr.IPNetwork(netString)
        found = False
        foundIp = None
        for ip in net.iterhosts():
            #print ip
            if self.checkFreeAddress(user, ip):
                found = True
                foundIp = str(ip)
                #print "FoundIp: %s" % foundIp
                break
            
        if found:
            return ("%s/%s" % (str(foundIp), str(self.netMask)))
        else:
            return None
              
    def checkFreeAddress(self, user, address):
        self.authUser(user)
        netString = ("%s/%s" % (self.netAddress, self.netMask))
        self.net = ipaddr.IPNetwork(netString)
        if not isinstance(address, ipaddr.IPv4Address):
            address = ipaddr.IPAddress(address)
        
        if not address in self.net:
            return False
        
        for addr in self.ipAddresses:
            if str(addr.addr) == str(address):
                return False
            
        dhcpNet = self.getDhcpSubnet(user)
        if dhcpNet != None and address in dhcpNet:
            return False
        
        return True
    
    def getDhcpSubnet(self, user):
        self.authUser(user)
        fullNetString = ("%s/%s" % (self.netAddress, self.netMask))
        netParts = self.netAddress.split(".")
        netParts[3] = "128"
        dhcpNetAddress = ".".join(netParts)
        dhcpNetString = ("%s/%s" % (dhcpNetAddress, "27"))
        fullNet = ipaddr.IPNetwork(fullNetString)
        dhcpNet = ipaddr.IPNetwork(dhcpNetString)
        if dhcpNet in fullNet:
            return dhcpNet
        else:
            return None
    
    def getDhcpSubnetString(self, user):
        self.authUser(user)
        return str(self.getDhcpSubnet(user))
    
    def getLibVirtXML(self, user):
        self.authUser(user)
        root = etree.Element("network")
        name = etree.SubElement(root, "name")
        name.text = self.name
        uuid = etree.SubElement(root, "uuid")
        uuid.text = self.uuid
        forward = etree.SubElement(root, "forward")
        if self.withQos and self.getHost(user).libvirtVersion >= "0.9.4":
            bandwith = etree.SubElement(root, 'bandwith')
            inbound = etree.SubElement(bandwith, 'inbound')
            inboundAttrib = inbound.attrib
            inboundAttrib['average'] = str(self.inboundAverage)
            inboundAttrib['peak'] = str(self.inboundPeak)
            inboundAttrib['burst'] = str(self.inboundBurst)
            outbound = etree.SubElement(bandwith, 'outbound')
            outboundAttrib = outbound.attrib
            outboundAttrib['average'] = str(self.outboundAverage)
            outboundAttrib['peak'] = str(self.outboundPeak)
            outboundAttrib['burst'] = str(self.outboundBurst)
        ip = etree.SubElement(root, "ip")
        ipAttrib = ip.attrib
        ipAttrib['address'] = self.getDhcpServerAddress(user).addr
        ipAttrib['netmask'] = self.netMask
        
        dhcp = etree.SubElement(ip, 'dhcp')
        
        first = None
        last = None
        dhcpNet = self.getDhcpSubnet(user)
        for i in dhcpNet.iterhosts():
            if first == None:
                first = str(i)
            last = str(i)
        
        range = etree.SubElement(dhcp, 'range')
        rangeAttrib = range.attrib
        rangeAttrib['start'] = first
        rangeAttrib['end'] = last
        for ip in self.ipAddresses:
            #Do not add Addresses with no Interface
            if ip.interface == None or ip.node == None or ip.isV6:
                continue
            host = etree.SubElement(dhcp, 'host')
            hostAttrib = host.attrib
            hostAttrib['mac'] = ip.interface.macAddress
            hostAttrib['name'] = ip.node.commonName
            hostAttrib['ip'] = ip.addr
            
        return root
            
    def getLibVirtString(self, user):
        self.authUser(user)
        return etree.tostring(self.getLibVirtXML(user), pretty_print = True)
                
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
        
    def addNode(self, user, node):
        self.authUser(user)
        
        if isinstance(node, dissomniag.model.Host):
            if self.getHost(user) != None:
                raise MultipleHostException()
        
        self.nodes.append(node)
        
    def getHost(self, user):
        self.authUser(user)
        for node in self.nodes:
            if isinstance(node, dissomniag.model.Host):
                return node
            
        return None
    
    def authUser(self, user):
        if self.topology != None:
            if user in self.topology.users:
                return True
        return super(generatedNetwork, self).authUser(user)
    
    def start(self, user):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(self, "net")
        job = dissomniag.taskManager.Job(context, "Start a network", user = user)
        job.addTask(dissomniag.tasks.createNetworkOnHost())
        dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
    
    def stop(self, user):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(self, "net")
        job = dissomniag.taskManager.Job(context, "Stop a network", user = user)
        job.addTask(dissomniag.tasks.destroyNetworkOnHost())
        dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
    
    def refresh(self, user):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(self, "net")
        job = dissomniag.taskManager.Job(context, "Refresh a network", user = user)
        job.addTask(dissomniag.tasks.statusNetwork())
        dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
    
    """
    After status check. Get the network in a consitent state.
    """
    def operate(self, user):
        if self.state == GenNetworkState.GENERAL_ERROR:
            context = dissomniag.taskManager.Context()
            context.add(self, "net")
            job = dissomniag.taskManager.Job(context, "Consisteny Operation: Delete Net", user)
            job.addTask(dissomniag.tasks.destroyNetworkOnHost())
            dissomniag.taskManager.Dispatcher.addJob(user, job)
            
        elif self.state == GenNetworkState.RUNTIME_ERROR:
            context = dissomniag.taskManager.Context()
            context.add(self, "net")
            job = dissomniag.taskManager.Job(context, "Consisteny Operation: Try to create net", user)
            job.addTask(dissomniag.tasks.createNetworkOnHost())
            dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
            
    
    @staticmethod
    def deleteNetwork(user, network):
        if network == None or not isinstance(network, generatedNetwork):
            return False
        network.authUser(user)
        
        #1. Delete TopologyConnection
        session = dissomniag.Session()
        try:
            connections = session.query(dissomniag.model.TopologyConnection).filter(dissomniag.model.TopologyConnection.viaGenNetwork == network).all()
        except NoResultFound:
            pass
        else:
            for connection in connections:
                session.delete(connection)
            dissomniag.saveCommit(session)
            
        #2. Destroy Network on Host
        if network.state == GenNetworkState.CREATED:
            network.stop(user)
        #3. Call Super delete Network
        return Network.deleteNetwork(user, network)
        
    
    @staticmethod
    def cleanUpGeneratedNetworks(user, host):
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
            if not isinstance(net, dissomniag.model.generatedNetwork):
                continue
            if not net.netAddress.startswith("10.100."):
                continue
            netId = net.netAddress.split(".")
            blockedNets.append(int(netId[2]))
        foundNet = None
        for net in range(0, 255):
            if net not in blockedNets:
                foundNet = net
                break
        if foundNet != None:
            returnNet = ("10.100.%d.0/255.255.255.0" % foundNet)
            return returnNet
        else:
            return None
        
