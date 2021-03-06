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
import os, subprocess, shlex, logging
import pwd
from abc import abstractmethod
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from twisted.conch.ssh import keys
import random
import string
import threading
import dissomniag
import os

log = logging.getLogger("Identity")

class IdentityRestartNotAllowed(Exception):
    pass

class SSHKeyGenError(Exception):
    pass

class SSHKeyAddError(Exception):
    pass

class Identity:
    isStarted = False
    systemUserName = "<System>"
    sshEnvironmentPrepared = False
    
    """
    classdocs
    """
    
    @abstractmethod
    def run(self):
        if not self.isStarted:
            self.isStarted = True
        else:
            raise IdentityRestartNotAllowed()
    
    @abstractmethod
    def _tearDown(self):
        raise NotImplementedError()
    
    def getAdministrativeUser(self):
        session = dissomniag.Session()
        user = None
        try: 
            user = session.query(dissomniag.auth.User).filter(dissomniag.auth.User.username == self.systemUserName).one()
        except MultipleResultsFound:
            one = False
            users = session.query(dissomniag.auth.User).filter(dissomniag.auth.User.username == self.systemUserName).all()
            for myUser in users:
                if one == False:
                    user = myUser
                    one = True
                    continue
                else:
                    session.delete(myUser)
        except NoResultFound:
            password = self.generateRandomPassword(length = 40)
            user = dissomniag.auth.User(self.systemUserName, password = password, isAdmin = True,
                    loginRPC = False, loginSSH = False, loginManhole = False,
                    isHtpasswd = False)
            session.add(user)
            dissomniag.saveCommit(session)
        finally:
            return user
            
    def generateRandomPassword(self, length = 20, chars = string.letters + string.digits):
            return ''.join([random.choice(chars) for i in range(length)])
    
    
    def getRsaKeys(self, all = None):
        uidBefore = os.geteuid()
        os.seteuid(0)
        gidBefore = os.getgid()
        os.setegid(0)
        self._prepareSSHEnvironment()
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
        privateKey = keys.Key.fromString(privateKeyString)
        publicKeyString = file(sshPublicKey, 'r').read()
        publicKey = keys.Key.fromString(publicKeyString)
        
        self._checkRsaKeyAdded(sshPrivateKey, publicKeyString)
        os.setegid(gidBefore)
        os.seteuid(uidBefore)
        if all:
            return sshPrivateKey, privateKeyString, sshPublicKey, publicKeyString
        else:
            return publicKey, privateKey
    
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
        log.info(str(privateKeyFd))
        ret = subprocess.call(shlex.split("ssh-add %s" % str(privateKeyFd)),
                            stdout = open('/dev/null', 'w'),
                            stderr = subprocess.STDOUT)
            
        if ret != 0:
            raise SSHKeyAddError()
        else:
            log.debug("SSH Key added to environment")
        
    def _prepareSSHEnvironment(self):
        if self.sshEnvironmentPrepared:
            return
        
        proc = subprocess.Popen("ssh-agent", stdout = subprocess.PIPE,
                                            stderr = subprocess.STDOUT)
        lines = []
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            lines.append(line)
            
        for line in lines:
            commands = line.split(";")
            if len(commands) == 1 and commands[0] == '1':
                continue
            for command in commands:
                pointers = command.split("=")
                if len(pointers) != 2:
                    continue
                log.info(command)
                os.environ[pointers[0]] = pointers[1]
        self.sshEnvironmentPrepared = True
                
    def refreshSSHEnvironment(self):
        self._prepareSSHEnvironment()
        sshKey = dissomniag.getIdentity().sshKey
        return self._checkRsaKeyAdded(sshKey.privateKeyFile, sshKey.publicKey)
        
            

identity = None

def _getVMIdentity():
    pass

def _getControlIdentity():
    session = dissomniag.Session()
    try:
        central = session.query(dissomniag.model.ControlSystem).one()
    except NoResultFound:
         central = dissomniag.model.ControlSystem()
         dissomniag.saveCommit(session)
         session.expire(central)
         return central
    except MultipleResultsFound:
        session.expire(central[0])
        return central[0]
    else:
        session.expire(central)
        return central

def getIdentity():
    if dissomniag.config.dissomniag.isCentral:
        identity = _getControlIdentity()
    else:
        identity = _getVMIdentity()
    
    return identity

class rootContext():
    lock = threading.RLock()
    counter = 0
    
    def __enter__(self):
        with rootContext.lock:
            rootContext.counter += 1
            getRoot()
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        with rootContext.lock:
            rootContext.counter -= 1
            if rootContext.counter <= 0:
                rootContext.counter = 0
                resetPermissions()
            
def getRoot():
    os.seteuid(0)
    os.setegid(0)

def resetPermissions():
    os.setegid(dissomniag.config.dissomniag.groupId)
    os.seteuid(dissomniag.config.dissomniag.userId)
    
savedWorkingDir = os.getcwd()

def chDir(chDirTo):
    global savedWorkingDir
    savedWorkingDir = os.getcwd()
    try:
        os.chdir(chDirTo)
        return True
    except IOError:
        return False
    
def resetDir():
    global savedWorkingDir
    try:
        os.chdir(savedWorkingDir)
        return True
    except IOError:
        return False
    
    
def checkProgrammUserAndGroup():
    log.info("In checkProgrammUserAndGroup")
    if os.getuid() != 0:
        raise OSError("The System must be started ad root.")
    resetPermissions()
    
def run():
    
    dissomniag.checkProgrammUserAndGroup()
    os.chdir(dissomniag.config.dissomniag.execDir)
    dissomniag.init()
    dissomniag.getIdentity().run()


        




