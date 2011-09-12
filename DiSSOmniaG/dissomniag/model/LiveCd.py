# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag
from dissomniag.model import *

class LiveCdEnvironment(dissomniag.utils.SingletonMixin):
    
    usable = False
    errorInfo = []
    
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

class LiveCd(dissomniag.Base):
    __tablename__ = 'livecds'
    id = sa.Column(sa.Integer, primary_key = True)
    buildDir = sa.Column(sa.String, nullable = False)
    staticAptList = sa.Column(sa.String)
    pxeInternalPath = sa.Column(sa.String)
    pxeExternalPath = sa.Column(sa.String)
    
    
    """
    classdocs
    """
    
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

