# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import ipaddr

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
    
    def __init__(self, node, name, mac):
        session = dissomniag.Session()
        self.node = node
        self.macAddress = mac
        self.name = name
        session.add(self)
        session.commit()
        
    def addIp(self, ipAddrOrNet):
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
                        session.delete(myIp) #Delete Invalid Interfaces
                found = False
            except NoResultFound:
                found = False
        finally:
            if found == False and ip == None:
                ip = dissomniag.model.IpAddress(ipAddrOrNet, self.node)
                self.ipAddresses.append(ip)
                session.commit()
                return ip
            else:
                session.commit()
                return None


        
