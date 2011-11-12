# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
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
    discriminator = sa.Column('type', sa.String(50), nullable = False)
    __mapper_args__ = {'polymorphic_on': discriminator, 'polymorphic_identity': 'network'}
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
        
        if node != None:
            self.addNode(user, node)
        dissomniag.saveCommit(session)
            
    
    def authUser(self, user):
        if isinstance(user, dissomniag.auth.User) and user.isAdmin:
            return True
        raise dissomniag.UnauthorizedFunctionCall()
    
    def __repr__(self):
        return "%s/%s" % (self.netAddress, self.netMask)
    
    """
    Is also overwritten in generatedNetwork
    """
    def addNode(self, user, node):
        self.authUser(user)
        self.nodes.append(node)
            
    
    @staticmethod
    def deleteNetwork(user, network):
        if network == None or not isinstance(network, Network):
            return False
        network.authUser(user)
        
        context = dissomniag.taskManager.Context()
        context.add(network, "net")
        job = dissomniag.taskManager.Job(context, description = "Delete a Network", user = user)
        #1. Delete all associated IP Addresses that are not connected to an Interface
        job.addTask(dissomniag.tasks.DeleteIpAddressesOnNetwork())
    
        #2. Delete Network
        job.addTask(dissomniag.tasks.DeleteNetwork())
        
        dissomniag.taskManager.Dispatcher.addJob(user, job)
        return True
    

            


        
