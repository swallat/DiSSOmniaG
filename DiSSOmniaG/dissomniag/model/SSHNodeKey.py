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
        
