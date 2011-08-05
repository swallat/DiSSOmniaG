# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import dissomniag

class SSHHostKey(dissomniag.Base):
    __tablename__ = "sshHostKeys"
    id = sa.Column(sa.Integer, primary_key = True)
    privateKey = sa.Column(sa.Binary(1000), unique = True, nullable = True)
    privateKeyFile = sa.Column(sa.String, nullable = True)
    publicKey = sa.Column(sa.Binary(1000), unique = True, nullable = True)
    publicKeyFile = sa.Column(sa.String, nullable = True)
    """
    classdocs
    """


        
