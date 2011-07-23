# -*- coding: utf-8 -*-
"""
Created on 22.07.2011

@author: Sebastian Wallat
"""
import time, atexit, datetime, crypt, string, random, sys
from twisted.conch.ssh import keys
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, Binary
from sqlalchemy.orm import relationship 

import dissomniag.dbAccess
from dissomniag.dbAccess import Base, Session
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

user_publickey = Table('user_publickey', Base.metadata,
                       Column('user_id', Integer, ForeignKey('users.id')),
                       Column('key_id', Integer, ForeignKey('public_keys.id')),
)

class User(Base):
    """
    classdocs
    """
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key = True)
    username = Column(String(40), nullable = False, unique = True)
    passwd = Column(String(40))
    isAdmin = Column(Boolean)
    loginRPC = Column(Boolean)
    loginSSH = Column(Boolean)
    loginManhole = Column(Boolean)
    isHtpasswd = Column(Boolean)
    
    publicKeys = relationship('PublicKey', secondary = user_publickey, backref = 'users')

    def __init__(self, username, password, publicKey = None, isAdmin = False, loginRPC = False, loginSSH = False, loginManhole = False, isHtpasswd = False):
        """
        Constructor
        """
        self.username = username
        if publicKey:
            self.addKey(publicKey)
        self.isAdmin = isAdmin
        self.loginRPC = loginRPC
        self.loginSSH = loginSSH
        self.loginManhole = loginManhole
        self.isHtpasswd = isHtpasswd
        if self.isHtpasswd:
            self.updateHtpasswdPassword(password)
        else:
            self._savePassword(password)
        
    def addKey(self, publicKey):
        publicKey = keys.Key.fromString(publicKey).blob()
        session = dissomniag.dbAccess.Session()
        try:
            existingKey = session.query(PublicKey).filter(PublicKey.publicKey == publicKey).one()
            self.publicKeys.append(existingKey)
        except NoResultFound:
            newKey = PublicKey(publicKey)
            session.add(newKey)
            self.publicKeys.append(newKey)
        finally:
            session.flush()
        
    def getKeys(self):
        return self.publicKeys
        
    def checkPassword(self, password):
        return self.passwd == crypt.crypt(password, self.passwd)
    
    def saveNewPassword(self, newPassword):
        if (self.username == dissomniag.config.HTPASSWD_ADMIN_USER):
            return
        else:
            self.isHtpasswd = False
            self._savePassword(newPassword)
    
    def updateHtpasswdPassword(self, newPassword):
        self.isHtpasswd = True
        self.passwd = newPassword
        
    def _savePassword(self, password):
        saltchars = string.ascii_letters + string.digits + './'
        salt = "$1$"
        salt += ''.join([ random.choice(saltchars) for x in range(8) ])
        self.passwd = crypt.crypt(password, salt)
        #self.passwd_time = datetime.datetime.now()
        #self.save()

    
class PublicKey(Base):
    """
    Class Description
    """
    
    __tablename__ = "public_keys"
    
    id = Column(Integer, primary_key = True)
    publicKey = Column(Binary(1000), nullable = False, unique = True)
    
    def __init__(self, publicKey):
        self.publicKey = publicKey
        
    def __repr__(self):
        self.publicKey
