# -*- coding: utf-8 -*-
"""
Created on 08.08.2011

@author: Sebastian Wallat
"""
import os, subprocess, shlex, logging
from abc import abstractmethod
from twisted.conch.ssh import keys
import dissomniag

log = logging.getLogger("Identity")

class IdentityRestartNotAllowed(Exception):
    pass

class SSHKeyGenError(Exception):
    pass

class SSHKeyAddError(Exception):
    pass

class Identity():
    isStarted = False
    
    """
    classdocs
    """
    
    @abstractmethod
    def start(self):
        if not self.isStarted:
            self.isStarted = True
        else:
            raise IdentityRestartNotAllowed()
    
    @abstractmethod
    def _tearDown(self):
        raise NotImplementedError()
    
    
    def getRsaKeys(self, all = None):
        sshPrivateKey = os.path.join(dissomniag.config.dissomniag.configDir, dissomniag.config.dissomniag.rsaKeyPrivate)
        sshPrivateKey = os.path.abspath(sshPrivateKey)
        sshPublicKey = os.path.join(dissomniag.config.dissomniag.configDir, dissomniag.config.dissomniag.rsaKeyPublic)
        sshPublicKey = os.path.abspath(sshPublicKey)
        if not (os.path.exists(sshPrivateKey) and os.path.exists(sshPublicKey)):
            ret = subprocess.call(shlex.split("ssh-keygen -t rsa -q -f %s -P ''" % sshPrivateKey),
                            stdout = open('/dev/null', 'w'),
                            stderr = subprocess.STDOUT)
            if ret != 0:
                raise SSHKeyGenError()
            else:
                log.debug("New SSH Keys created")
            
                
        
        privateKeyString = file(sshPrivateKey, 'r').read()
        rsaKey = keys.Key.fromString(privateKeyString)
        publicKeyString = file(sshPublicKey, 'r').read()
        
        self._checkRsaKeyAdded(sshPrivateKey, publicKeyString)
        if all:
            return sshPrivateKey, privateKeyString, sshPublicKey, publicKeyString
        else:
            return publicKeyString, rsaKey
    
    def _checkRsaKeyAdded(self, privateKeyFd, publicKeyString):
        proc = subprocess.Popen(shlex.split("ssh-add -L"),
                               stdin = subprocess.PIPE,
                               stdout = subprocess.PIPE)
        result = proc.communicate()[0]
        result = result.split("\n")
        
        splitStrings = [publicKeyString.split(" ")[0], publicKeyString.split(" ")[1]]
        
        myPublicKey = " ".join(splitStrings)
        for line in result:
            if line.startswith(myPublicKey):
                return
            
        #Key not found
        ret = subprocess.call(shlex.split("ssh-add %s" % privateKeyFd),
                            stdout = open('/dev/null', 'w'),
                            stderr = subprocess.STDOUT)
            
        if ret != 0:
            raise SSHKeyAddError()
        else:
            log.debug("SSH Key added to environment")
        
            

identity = None

def _getVMIdentity():
    pass

def _getControlIdentity():
    return dissomniag.model.ControlSystem()

def getIdentity():
    global identity
    if identity == None:
        if dissomniag.config.dissomniag.isCentral:
            identity = _getControlIdentity()
        else:
            identity = _getVMIdentity()
    
    return identity

def start():
    dissomniag.init()
    getIdentity().start()


        




