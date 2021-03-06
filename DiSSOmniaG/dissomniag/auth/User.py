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
import logging
import time, atexit, datetime, crypt, string, random, sys
from twisted.conch.ssh import keys
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, LargeBinary
from sqlalchemy.orm import relationship 
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import dissomniag.dbAccess
from dissomniag import Base, Session
from dissomniag.taskManager import Job

log = logging.getLogger("auth.User")

class LOGIN_SIGN(object):
    VALID_USER = 0
    NO_SUCH_USER = 1
    SECRET_UNVALID = 2
    UNVALID_ACCESS_METHOD = 3

user_publickey = Table('user_publickey', Base.metadata,
                       Column('user_id', Integer, ForeignKey('users.id')),
                       Column('key_id', Integer, ForeignKey('public_keys.id')),
)
"""
Test
"""

class User(Base):
    """
    classdocs
    """
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key = True)
    username = Column(String(40), nullable = False, unique = True)
    passwd = Column(String(40), nullable = False)
    isAdmin = Column(Boolean, default = False)
    loginRPC = Column(Boolean, default = False)
    loginSSH = Column(Boolean, default = False)
    loginManhole = Column(Boolean, default = False)
    isHtpasswd = Column(Boolean, default = False)
    isMaintain = Column(Boolean, default = False)
    
    publicKeys = relationship('PublicKey', secondary = user_publickey, backref = 'users')
    

    def __init__(self, username, password, publicKey = None, isAdmin = False, loginRPC = False, loginSSH = False, loginManhole = False, isHtpasswd = False, maintain = False):
        """
        Constructor
        """
        
        self.username = username
        if password:
            self.isHtpasswd = isHtpasswd
            if self.isHtpasswd:
                self.updateHtpasswdPassword(password)
            else:
                self._savePassword(password)
        if publicKey:
            try:
                self.addKey(publicKey)
            except dissomniag.BadKeyError:
                pass
        self.isAdmin = isAdmin
        self.loginRPC = loginRPC
        self.loginSSH = loginSSH
        self.loginManhole = loginManhole
        self.isMaintain = maintain
   
    def __repr__(self):
        return "<User: %s, isAdmin: %s, loginRPC: %s, loginSSH: %s, loginManhole: %s, isHtpasswd: %s, PublicKeys: %s>" \
                        % (self.username, self.isAdmin, self.loginRPC, self.loginSSH, self.loginManhole, self.isHtpasswd, self.publicKeys)
    
    @staticmethod
    def addUser(username, password, publicKey = None, isAdmin = None,
                        loginRPC = None, loginSSH = None,
                        loginManhole = None, isHtpasswd = None):
        session = Session()
        try:
            thisUser = session.query(User).filter(User.username == username).one()
            thisUser.saveNewPassword(password)
            if publicKey:
                thisUser.addKey(publicKey)
            if isAdmin != None:
                thisUser.isAdmin = isAdmin
            if loginRPC != None:
                thisUser.loginRPC = loginRPC
            if loginSSH != None:
                thisUser.loginSSH = loginSSH
            if loginManhole != None and thisUser.isAdmin:
                thisUser.loginManhole = loginManhole
            if isHtpasswd != None:
                thisUser.isHtpasswd = isHtpasswd
            dissomniag.saveCommit(session)
            return thisUser                 
        except (NoResultFound, MultipleResultsFound):
            if isAdmin == None:
                isAdmin = False
            if loginRPC == None:
                loginRPC = False
            if loginSSH == None:
                loginSSH = False
            if loginManhole == None:
                loginManhole = False
            if isHtpasswd == None:
                isHtpasswd = False
            return User(username, password, publicKey, isAdmin, loginRPC, loginSSH, loginManhole, isHtpasswd)
        
    def addKey(self, publicKey):
        session = dissomniag.dbAccess.Session()
        
        #Check if entered Key is a valid Key
        try:
            keys.Key.fromString(publicKey)
        except keys.BadKeyError:
            raise dissomniag.BadKeyError("Not a valid SSH Key")
            
        try:
            existingKey = session.query(PublicKey).filter(PublicKey.publicKey == publicKey).one()
            self.publicKeys.append(existingKey)
        except NoResultFound:
            newKey = PublicKey(publicKey)
            session.add(newKey)
            self.publicKeys.append(newKey)
        finally:
            dissomniag.saveCommit(session)
        
    def getKeys(self):
        return self.publicKeys
    
    def delKeys(self):
        session = dissomniag.Session()
        self.publicKeys = []
        dissomniag.saveCommit(session)
        
        
    def checkPassword(self, password):
        return self.passwd == crypt.crypt(password, self.passwd)
    
    def saveNewPassword(self, newPassword):
        self._savePassword(newPassword)
        if self.isHtpasswd:
            dissomniag.auth.refreshHtpasswdFile()           
    
    def updateHtpasswdPassword(self, newPassword):
        self.isHtpasswd = True
        self.passwd = newPassword
        
    def _savePassword(self, password):
        saltchars = string.ascii_letters + string.digits + './'
        salt = "$1$"
        salt += ''.join([ random.choice(saltchars) for x in range(8) ])
        self.passwd = crypt.crypt(password, salt)
        session = Session()
        dissomniag.saveCommit(session)
        
    @staticmethod
    def loginRPCMethod(username, passwd = None):
        if not passwd:
            return LOGIN_SIGN.SECRET_UNVALID, None
        
        session = Session()
        try:
            user = session.query(User).filter(User.username == username).one()
        except (NoResultFound, MultipleResultsFound):
            return LOGIN_SIGN.NO_SUCH_USER, None
        if not user.loginRPC:
            return LOGIN_SIGN.UNVALID_ACCESS_METHOD, None
        return User._loginViaPasswd(user, passwd)
    
    @staticmethod          
    def loginSSHMethod(username, passwd = None, key = None):
        if not passwd and not key:
            return LOGIN_SIGN.SECRET_UNVALID, None
        session = Session()
        try:
            user = session.query(User).filter(User.username == username).one()
        except (NoResultFound, MultipleResultsFound):
            return LOGIN_SIGN.NO_SUCH_USER, None
        if not user.loginSSH:
            return LOGIN_SIGN.UNVALID_ACCESS_METHOD, None
        """If Public Key was provided"""
        if not passwd:
            return User._loginViaPubKey(user, key)
        else:
            return User._loginViaPasswd(user, passwd)
    @staticmethod           
    def loginManholeMethod(username, passwd = None, key = None):
        if not passwd and not key:
            return LOGIN_SIGN.SECRET_UNVALID, None
        session = Session()
        try:
            user = session.query(User).filter(User.username == username).one()
        except (NoResultFound, MultipleResultsFound):
            return LOGIN_SIGN.NO_SUCH_USER, None
        """Check that only admins have access to the Manhole backend"""
        if not user.isAdmin and not user.loginManhole:
            return LOGIN_SIGN.UNVALID_ACCESS_METHOD, None
        """If Public Key was provided"""
        if not passwd:
            return User._loginViaPubKey(user, key)
        else:
            return User._loginViaPasswd(user, passwd)
    @staticmethod    
    def _loginViaPubKey(user, key):
        for userKey in user.publicKeys:
            if keys.Key.fromString(userKey.publicKey).blob() == key:
                return LOGIN_SIGN.VALID_USER, user
        return LOGIN_SIGN.SECRET_UNVALID, None
    @staticmethod    
    def _loginViaPasswd(user, passwd):
        
        if user.checkPassword(passwd) == True:
            return LOGIN_SIGN.VALID_USER, user
        else:
            return LOGIN_SIGN.SECRET_UNVALID, None
    
class PublicKey(Base):
    """
    Class Description
    """
    
    __tablename__ = "public_keys"
    
    id = Column(Integer, primary_key = True)
    publicKey = Column(LargeBinary(1000), nullable = False, unique = True)
    
    def __init__(self, publicKey):
        self.publicKey = publicKey
        
    def __repr__(self):
        return str(self.publicKey)
    
    def getUserHostPart(self): 
        pKey = self.publicKey.split(" ")
        i = len(pKey) - 1
        part = pKey[i]
        part = part.split("@")
        if len(part) > 1:
            user = part[0]
            host = part[1].split("\n")[0]
        else:
            user = None
            host = part[0].split("\n")[0]
        
        return user, host
    
    def getUser(self):
        return self.getUserHostPart()[0]
    
    def getHost(self):
        return self.getUserHostPart()[1]
    
    def getUserHostString(self):
        part = self.getUserHostPart()
        return "%s@%s" % (part[0], part[1])
    
    def getPublicFileString(self):
        return "%s.pub" % self.getUserHostString()
