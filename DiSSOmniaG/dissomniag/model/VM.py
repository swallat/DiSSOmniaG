# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag
from dissomniag.model import *

class VM(AbstractNode):
    __tablename__ = 'vms'
    __mapper_args__ = {'polymorphic_identity': 'vm'}
    vm_id = sa.Column('id', sa.Integer, sa.ForeignKey('nodes.id'), primary_key = True)
    ramSize = sa.Column(sa.String, default = "1024MB", nullable = False)
    hdSize = sa.Column(sa.String, default = "5GB")
    useHD = sa.Column(sa.Boolean, default = False, nullable = False)
    enableVNC = sa.Column(sa.Boolean, default = False, nullable = False)
    vncAddress = sa.Column(sa.String)
    vncPassword = sa.Column(sa.String(40))
    dynamicAptList = sa.Column(sa.String)
    topology_id = sa.Column(sa.Integer, sa.ForeignKey('topologies.id'))
    host_id = sa.Column(sa.Integer, sa.ForeignKey('hosts.id'))
    host = orm.relationship("Host", primaryjoin = "VM.host_id == Host.host_id", backref = "virtualMachines")
    liveCd_id = sa.Column(sa.Integer, sa.ForeignKey('livecds.id'))
    liveCd = orm.relationship("LiveCd", backref = orm.backref('livecds', uselist = False))
    
    """
    classdocs
    """
    
    def getLibVirtXML(self, user):
        pass
    
    def authUser(self, user):
        if user in self.topology.users or user.isAdmin:
            return True
        raise dissomniag.UnauthorizedFunctionCall()
    
    @staticmethod
    def deleteNode(node):
        pass
    
    @staticmethod
    def generateDeleteNodeJob(node):
        pass
    
    
class VMIdentity(VM, dissomniag.Identity):
    isStarted = False
    """
    classdocs
    """
    
    def __new__(cls, *args, **kwargs):
        # Store instance on cls._instance_dict with cls hash
        key = str(hash(cls))
        if not hasattr(cls, '_instance_dict'):
            cls._instance_dict = {}
        if key not in cls._instance_dict:
            cls._instance_dict[key] = \
                super(VMIdentity, cls).__new__(cls, *args, **kwargs)
        return cls._instance_dict[key]


    def start(self):
        if not self.isStarted:
            self.isStarted = True
        else:
            raise dissomniag.Identity.IdentityRestartNotAllowed()
    
    def _tearDown(self):
        pass


