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
    #liveCd = orm.relationship("LiveCd", backref = orm.backref('livecds', uselist = False))
    liveCd = orm.relationship("LiveCd", backref = "vm")
    
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
    def deleteVM(user, node):
        if node == None or type(node) != VM:
            return False
        node.authUser(user)
        
        #1. Delete LiveCD
        if node.liveCD != None and type(node.liveCd) == dissomniag.model.LiveCd:
            dissomniag.model.LiveCd.deleteLiveCd(node.liveCd)

        #2. Delete Interfaces
        for interface in node.interfaces:
            dissomniag.model.Interface.deleteInterface(user, interface)
        
        
        context = dissomniag.taskManager.Context()
        context.add(node, "vm")
        context.add(node, "node")
        job = dissomniag.taskManager.Job(context, description="Delete a VM", user = user)
        #3. Delete IPAddresses
        job.addTask(dissomniag.tasks.DeleteIpAddressesOnNode())
        
        #4. Delete VM
        job.addTask(dissomniag.tasks.DeleteVM())
        
        #5. Delete all Topology Connection for this VM
        session = dissomniag.Session()
        
        try:
            connections = session.query(dissomniag.model.TopologyConnection).filter(sa.or_(dissomniag.model.TopologyConnection.fromVM == node, dissomniag.model.TopologyConnection.toVM == node)).all()
        except NoResultFound:
            pass
        else:
            for connection in connections:
                session.delete(connection)
            session.commit()
        
        dissomniag.taskManager.Dispatcher.addJob(user = user, job = job)
        return True
        
    
    @staticmethod
    def deleteNode(user, node):
        return VM.deleteVM(user, node)
    
    
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


