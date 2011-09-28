# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""

import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag
from dissomniag.model import *
from dissomniag.auth import User

class LiveCdEnvironment(dissomniag.utils.Singleton):
    
    usable = False
    errorInfo = []
    prepared = False
    
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
    staticAptList = sa.Column(sa.String)
    pxeInternalPath = sa.Column(sa.String)
    pxeExternalPath = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id')) # Many to one style
    user = orm.relationship('User', backref = 'liveCd')
    
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
    
    @staticmethod
    def deleteLiveCd(user, livecd):
        if livecd == None or not isinstance(livecd, LiveCd):
            return False
        livecd.authUser(user)
        
        # Add Job for file system sanity
        
        session = dissomniag.Session()
        
        try:
            session.delete(livecd)
        except Exception:
            failed = True
        else:
            session.commit()
            failed = False
        return not failed

