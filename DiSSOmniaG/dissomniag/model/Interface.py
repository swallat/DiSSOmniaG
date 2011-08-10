# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import ipaddr, random

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
    
    def __init__(self, user, node, name, mac):
        session = dissomniag.Session()
        self.node = node
        self.macAddress = mac
        self.name = name
        session.add(self)
        session.commit()
            
    def addIp(self, user, ipAddrOrNet):
        
        self.authUser(user)
        
        session = dissomniag.Session()
        if type(ipAddrOrNet) == str:
            ipAddrOrNet = ipaddr.IPNetwork(ipAddrOrNet)
        ip = None
        found = False
        try:
            ip = session.query(dissomniag.model.IpAddress).filter(dissomniag.model.IpAddress.addr == str(ipAddrOrNet.ip)).filter(dissomniag.model.IpAddress.node == self.node).one()
            if ip.interface != self:
                ip.interface = self
            found = True
        except NoResultFound:
            found = False
        except MultipleResultsFound:
            try:
                one = False
                ips = session.query(dissomniag.model.IpAddress).filter(dissomniag.model.IpAddress.addr == str(ipAddrOrNet.ip)).filter(dissomniag.model.IpAddress.node == self.node).all()
                for myIp in ips:
                    if not one:
                        if ip.interface != self:
                            ip.interface = self
                        ip = myIp
                        one = True
                    else:
                        IpAddress.deleteIpAddress(user, myIp) #Delete Invalid Interfaces
                found = False
            except NoResultFound:
                found = False
        finally:
            if found == False and ip == None:
                ip = dissomniag.model.IpAddress(user, ipAddrOrNet, self.node)
                self.ipAddresses.append(ip)
                session.commit()
                return ip
            elif found == True and ip != None:
                session.commit()
                return ip
            else:
                session.commit()
                return None
            
    def getLibVirtXML(self, user):
        pass
    
    def authUser(self, user):
        return self.node.authUser(user)
    
    @staticmethod
    def checkValidMac(mac):
        splited = mac.split(":")
        if len(splited) != 6:
            raise dissomniag.NoValidMac()
        for block in splited:
            blockLength = 0
            for value in block:
                blockLength += 1
                if blockLength > 2:
                    raise dissomniag.NoValidMac()
                if value not in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "A", "b", "B", "c", "C", "d", "D", "e", "E", "f", "F"]:
                    raise dissomniag.NoValidMac()
        return True
    
    @staticmethod
    def getRandomMac():
        found = False
        session = dissomniag.Session()
        mac = None
        while not found:
            mac = [ 0x00, 0x16, 0x3e,
            random.randint(0x00, 0x7f),
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff) ]
            
            mac = ':'.join(map(lambda x: "%02x" % x, mac))
            try:
                session.query(Interface).filter(Interface.macAddress == mac).one()
            except (NoResultFound, MultipleResultsFound):
                found = True
                break
        return mac
    
    @staticmethod
    def moveIpAddressesOfInterface(user, interfaceFrom, interfaceTo):
        pass
    
    @staticmethod
    def deleteInterface(user, interface, isAdministrative = False):
        """
        TODO: Implement with generateDeleteInterfaceJob
        
        Now operation only on DB
        """
        interface.authUser(user)
        
        if isAdministrative:
            if interface.node.reDefineMaintainanceIPOnInterfaceDelete(user, interface):
                session = dissomniag.Session()
                for ipaddr in interface.ipAddresses:
                    IpAddress.deleteIpAddress(ipaddr)
                session.delete(interface)
                return True
            return False
        
    
    @staticmethod
    def generateDeleteInterfaceJob(user, interface):
        pass
        
        
            

        
