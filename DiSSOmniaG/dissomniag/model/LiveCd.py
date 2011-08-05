# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag

class LiveCd(dissomniag.Base):
    __tablename__ = 'livecds'
    id = sa.Column(sa.Integer, primary_key = True)
    uuid = sa.Column(sa.String(36), unique = True, nullable = False)
    buildDir = sa.Column(sa.String, nullable = False)
    staticAptList = sa.Column(sa.String)
    pxeInternalPath = sa.Column(sa.String)
    pxeExternalPath = sa.Column(sa.String)
    
    
    """
    classdocs
    """


