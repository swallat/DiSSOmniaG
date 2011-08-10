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
                                   maintainanceIP = maintainanceIP, sshKey = sshKey,
                                   administrativeUserName = administrativeUserName,
                                   state = dissomniag.model.NodeState.DOWN)
        
        self.check(user)
        self.initiateRemote(user)
        
        
    
    
    def addSelfGeneratedNetwork(self, user, name, ipNetwork = None):
        pass
    
    def authUser(self, user):
        if user.isAdmin:
            return True
        raise dissomniag.UnauthorizedFunctionCall()
    
    def check(self, user):
        self.authUser(user)
        
        context = dissomniag.taskManager.Context()
        context.add(self, "host")
        job = dissomniag.taskManager.Job(context, dexcription = "Ping Host to check if it is up.", user = user)
        job.addTask(dissomniag.tasks.HostTasks.CheckHostUpTask())
        dissomniag.taskManager.Dispatcher.addJob(user, job)
        
    def initiateRemote(self, user):
        pass
    
    @staticmethod
    def deleteNode(node):
        pass
    
    @staticmethod
    def generateDeleteNodeJob(node):
        pass
