# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import tempfile, os
import shlex, shutil
import subprocess
import sqlalchemy as sa
import dissomniag
from dissomniag.model import *

class SSHNodeKey(dissomniag.Base):
    __tablename__ = "sshNodeKeys"
    id = sa.Column(sa.Integer, primary_key = True)
    privateKey = sa.Column(sa.LargeBinary(1000), unique = True, nullable = True)
    privateKeyFile = sa.Column(sa.String, nullable = True)
    publicKey = sa.Column(sa.LargeBinary(1000), unique = True, nullable = True)
    publicKeyFile = sa.Column(sa.String, nullable = True)
    """
    classdocs
    """
        
    def __repr__(self):
        return str(self.publicKey)
    
    def getUserHostPart(self):
        if self.publicKey == None:
            return None
        
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
    
    @staticmethod
    def generateVmKey(hostname, user = "user"):
        directory_name = tempfile.mkdtemp()
        privKey = os.path.join(directory_name, "key")
        pubKey = os.path.join(directory_name, "key.pub")
        
        ret = subprocess.call(shlex.split("ssh-keygen -t rsa -q -f %s -P ''" % privKey),
                            stdout = open('/dev/null', 'w'),
                            stderr = subprocess.STDOUT)
        if ret != 0:
            return None
        
        with open(privKey, 'r') as f:
            privateKey = f.read()
            
        with open(pubKey, 'r') as f:
            publicKey = f.read()
            
        pKey = publicKey.split(" ")
        i = len(pKey) -1
        pKey[i] = "%s@%s\n" % (user, hostname)
        
        shutil.rmtree(directory_name)
        
        returnMe = SSHNodeKey()
        returnMe.privateKey = privateKey
        returnMe.publicKey = " ".join(pKey)
        return returnMe
        
