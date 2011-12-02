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
    #buildDir = sa.Column(sa.String, nullable = False)
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
    
    def __init__(self, vm):
        #self.user = vm.user
        self.plainPassword = "b00tloader"
    
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
        commonName = etree.SubElement(liveInfo, "commonName")
        commonName.text = str(self.vm.commonName)
        password = etree.SubElement(liveInfo, "password")
        password.text = str(self.plainPassword)
        uuid = etree.SubElement(liveInfo, "uuid")
        uuid.text = str(self.vm.uuid)
        serverIp = etree.SubElement(liveInfo, "serverIp")
        ident = dissomniag.getIdentity()
        serverIp.text = str(ident.getMaintainanceIP().addr)
        for interface in self.vm.interfaces:
            inter = etree.SubElement(liveInfo, "interface")
            name = etree.SubElement(inter, "name")
            name.text = str(interface.name)
            mac = etree.SubElement(inter, "mac")
            mac.text = str(interface.macAddress)
        
        vmSSHKeys = etree.SubElement(liveInfo, "vmSSHKeys")
        publicKey = etree.SubElement(vmSSHKeys, "publicKey")
        publicKey.text = str(self.vm.sshKey.publicKey)
        privateKey = etree.SubElement(vmSSHKeys, "privateKey")
        privateKey.text = str(self.vm.sshKey.privateKey)
        
        if dissomniag.getIdentity().getAdministrativeUser().publicKeys[0] != None:
            adminKey = etree.SubElement(liveInfo, "sshKey")
            adminKey.text = str(dissomniag.getIdentity().getAdministrativeUser().publicKeys[0].publicKey)
        session = dissomniag.Session()
        try:
            users = session.query(dissomniag.auth.User).filter(dissomniag.auth.User.isAdmin == True).all()
        except NoResultFound:
            pass
        else:
            for user in users:
                for key in user.getKeys():
                    userKey = etree.SubElement(liveInfo, "sshKey")
                    userKey.text = str(key) 
            
        ###
        # Add other user keys by topology
        ###
        
        return etree.tostring(liveInfo, pretty_print=True)
            
    def hashConfig(self, user, xml=None):
        self.authUser(user)
        myHash = hashlib.sha256()
        if xml == None:
            myHash.update(self.getInfoXML(user))
        else:
            myHash.update(xml)
        self.versioningHash = myHash.hexdigest()
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
                with open(os.path.join(self.vm.getLocalUtilityFolder(user), "configHash"), 'r') as f:
                    myHash = f.readline()
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
        
    def _getServerProxy(self, user):
        self.authUser(user)
        return xmlrpclib.ServerProxy(self.vm.getRPCUri(user))
    
    def addAllCurrentAppsOnRemote(self, user):
        self.authUser(user)
        
        tree = etree.Element("AppAdd")
        #Wenn keine relationen vorhanden sind überspringen.
        if self.AppLiveCdRelations == []:
            return True
        
        for rel in self.AppLiveCdRelations:
            tree.append_child(rel._getAppAddInfo(user))
        
        xmlString = self._getXmlString(tree)
        
        proxy = self._getServerProxy(user)
        
        return proxy.addApps(xmlString)
    
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
        
        # Delete App LiveCd Relations
        one = False
        for rel in livecd.AppLiveCdRelations:
            if not one:
                one = True
            dissomniag.model.AppLiveCdRelation.deleteRelation(user, rel, triggerPush = False)
        
        # Add Job for file system sanity
        context = dissomniag.taskManager.Context()
        context.add(livecd, "liveCd")
        job = dissomniag.taskManager.Job(context, "Delete a LiveCd", user)
        if one:
            job.addTask(dissomniag.tasks.GitPushAdminRepo())
        job.addTask(dissomniag.tasks.LiveCDTasks.deleteLiveCd())
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user, livecd, job)
        

