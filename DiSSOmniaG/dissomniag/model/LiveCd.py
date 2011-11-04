# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""

import sqlalchemy as sa
import sqlalchemy.orm as orm
from lxml import etree
import hashlib
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import dissomniag
from dissomniag.model import *
from dissomniag.auth import User

class LiveCdEnvironment(dissomniag.utils.Singleton):
    
    usable = False
    errorInfo = []
    prepared = False
    lifeInfoFilename = "liveInfo.xml"
    
    def makeInitialChecks(self):
        pass
    
    def getErrorInfo(self):
        if self.usable == True:
            return None
        else:
            returnMe = ""
            if self.errorInfo == []:
                returnMe = "Not Initialized"
            else:
                for line in self.errorInfo:
                    returnMe += str(line)
            return returnMe

class LiveCd(dissomniag.Base):
    __tablename__ = 'livecds'
    id = sa.Column(sa.Integer, primary_key = True)
    buildDir = sa.Column(sa.String, nullable = False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id')) # Many to one style
    user = orm.relationship('User', backref = 'liveCd')
    plainPassword = sa.Column(sa.String)
    imageCreated = sa.Column(sa.Boolean, default = False)
    versioningHash = sa.Column(sa.String(64), nullable = True)
    onHdUpToDate = None #Only Runtime Parameter True == UptoDate, False == NotUpToDate, None== Unknown
    onRemoteUpToDate = None #Only Runtime Parameter True == UptoDate, False == NotUpToDate, None== Unknown
    
    """
    classdocs
    """
    
    def _generateRPCUser(self):
        pass
    
    def _deleteRPCUser(self):
        pass
    
    def authUser(self, user):
        if user.isAdmin:
            return True
        else:
            return self.vm.authUser(user)
    
    def getInfoXMLwithVersionongHash(self, user):
        self.authUser(user)
        xml = self.getInfoXML(user)
        return xml, self.hashConfig(user, xml)
        
        
    def getInfoXML(self, user):
        self.authUser(user)
        liveInfo = etree.Element("liveInfo")
        password = etree.SubElement(liveInfo, "password")
        password.text = str(self.plainPassword)
        uuid = etree.SubElement(liveInfo, "uuid")
        uuid.text = str(self.vm.uuid)
        serverIp = etree.SubElement(liveInfo, "serverIp")
        serverIp.text = str(dissomniag.getIdentity().getMaintainanceIP())
        for interface in self.vm.interfaces:
            inter = etree.SubElement(liveInfo, "interface")
            name = etree.SubElement(inter, "name")
            name.text = str(interface.name)
            mac = etree.SubElement(inter, "mac")
            mac.text = str(interface.macAddress)
        
        if dissomniag.getIdentity().getAdministrativeUser().publicKeys[0] != None:
            adminKey = etree.SubElement(liveInfo, "sshKey")
            adminKey.text = dissomniag.getIdentity().getAdministrativeUser().publicKey[0]
        session = dissomniag.Session()
        try:
            users = session.query(dissomniag.auth.User).filter(dissomniag.auth.User.isAdmin == True).all()
        except NoResultFound:
            pass
        else:
            for user in users:
                for key in user.getKeys():
                    userKey = etree.SubElement(liveInfo, "sshKey")
                    userKey.text = key 
            
        ###
        # Add other user keys by topology
        ###
        
        return etree.tostring(liveInfo, pretty_print=True)
            
    def hashConfig(self, user, xml=None):
        self.authUser(user)
        myHash = hashlib.sha256()
        if xml == None:
            hash.update(self.getInfoXML(user))
        else:
            hash.update(xml)
        self.versioningHash = myHash.hexdigist()
        return self.versioningHash
    
    def prepareLiveImage(self, user):
        self.authUser(user)
        
        if self.onHdUpToDate != True:
            pass
        
    def deployLiveImage(self, user):
        self.authUser(user)
        
    
    def checkOnHdUpToDate(self, user, refresh = False):
        self.authUser(user)
        
        if self.onHdUpToDate == None or refresh == True:
            try:
                with open(os.path.join(self.vm.getLocalUtilityFolder(), "configHash"), 'r') as f:
                    myHash = f.readline(self.versioningHash)
            except Exception:
                self.onHdUpToDate = False
                raise Exception("No config hash for LiveCd on HD.")
            
            if myHash == self.hashConfig(user):
                self.onHdUpToDate = True
                return True
            else:
                self.onHdUpToDate = False
                return False
        elif self.onHdUpToDate:
            return True
        else:
            return False
        
    def checkOnRemoteUpToDate(self, user, refresh = False):
        self.authUser(user)
        
        if self.onRemoteUpToDate == None or refresh == True:
            """
            Create new job
            """
            context = dissomniag.taskManager.Context()
            context.add(self.vm, "vm")
            job = dissomniag.taskManager.Job(context, "Check LiveCd up to date", user)
            job.addTask(dissomniag.tasks.VMTasks.statusVM())
            dissomniag.taskManager.Dispatcher.addJobSyncronized(user, LiveCdEnvironment(), job)
            return None
        elif self.onRemoteUpToDate:
            return True
        else:
            return False
    
    @staticmethod
    def checkUptODateOnHd(user, livecd):
        if livecd == None or not isinstance(livecd,LiveCd):
            return False
        livecd.authUser(user)
        
        try:
            with open(os.path.join(livecd.vm.getLocalUtilityFolder(), "configHash"), 'r') as f:
                myHash = f.readline(livecd.versioningHash)
        except Exception:
            livecd.onHdUpToDate = False
            raise Exception("No config hash for LiveCd on HD.")
        
        if myHash == livecd.hashConfig(user):
            livecd.onHdUpToDate = True
        else:
            livecd.onHdUpToDate = False
        
        return
       
    
    @staticmethod
    def deleteLiveCd(user, livecd):
        if livecd == None or not isinstance(livecd, LiveCd):
            return False
        livecd.authUser(user)
        
        # Add Job for file system sanity
        context = dissomniag.TaskManager.Context()
        context.add(livecd)
        job = dissomniag.taskManager.Job(context, "Delete a VM", user)
        job.addTask(dissomniag.tasks.LiveCDTasks.deleteLiveCd())
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user, livecd, job)
        
        session = dissomniag.Session()
        
        try:
            session.delete(livecd)
        except Exception:
            failed = True
        else:
            session.commit()
            failed = False
        return not failed

