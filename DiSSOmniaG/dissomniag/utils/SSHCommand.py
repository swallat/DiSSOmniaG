# -*- coding: utf-8 -*-
"""
Created on 02.09.2011

@author: Sebastian Wallat
"""
import shlex
import subprocess
import dissomniag

class SSHCommand(object):
    
    """
    classdocs
    """
    SSH_CMD = shlex.split("ssh -q -oConnectTimeout=30 -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null -oPasswordAuthentication=false")

    def __init__(self, cmd, hostOrIp, username = "root", keyfile = dissomniag.config.dissomniag.rsaKeyPrivate):
        """
        Constructor
        """
        
        self.cmd = shlex.split(cmd)
        self.hostOrIp = hostOrIp
        self.username = username
        self.keyfile = keyfile
        
    def _getFullCmdString(self):        
        connectionString = shlex.split(self.username + "@" + self.hostOrIp)
        return self.SSH_CMD + connectionString + self.cmd
        
    def run(self, redirectStdinTo = None, redirectStdoutTo = None, redirectStderrTo = None):
        pass
    
    def close(self):
        pass
    
    def returnCode(self):
        pass
    
    def getOutput(self):
        pass
    
    def callAndClose(self):
        pass
        
    
        
        
