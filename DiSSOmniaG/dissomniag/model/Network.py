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
    

            


        
