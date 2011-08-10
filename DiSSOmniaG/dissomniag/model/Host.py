# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag
from dissomniag.dbAccess import Base
from dissomniag.model import *

class Host(AbstractNode):
    __tablename__ = 'hosts'
    __mapper_args__ = {'polymorphic_identity': 'host'}
    
    host_id = sa.Column('id', sa.Integer, sa.ForeignKey('nodes.id'), primary_key = True)
    qemuConnector = sa.Column(sa.String(100))
    
    
    """
    classdocs
    """
    def __init__(self, user, commonName, maintainanceIP,
                 sshKey = None, administrativeUserName = None):
        if administrativeUserName != None:
            self.administrativeUserName = administrativeUserName
            
        self.qemuConnector = "qemu+ssh://%s@%s/system?no_tty=1" % (self.administrativeUserName, maintainanceIP)
        
        super(Host, self).__init__(user = user, commonName = commonName,
                                   maintainanceIP = maintainanceIP, ssKey = sshKey,
                                   administrativeUserName = administrativeUserName)
        
        
    
    
    def addSelfGeneratedNetwork(self, user, name, ipNetwork):
        pass
    
    def authUser(self, user):
        if user.isAdmin:
            return True
        raise dissomniag.UnauthorizedFunctionCall()
    
    def checkConnectivity(self, user):
        pass
    
    @staticmethod
    def deleteNode(node):
        pass
    
    @staticmethod
    def generateDeleteNodeJob(node):
        pass
