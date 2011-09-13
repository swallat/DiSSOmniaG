# -*- coding: utf-8 -*-
"""
Created on 02.09.2011

@author: Sebastian Wallat
"""
import os
import shlex
import subprocess
import logging

import dissomniag

log = logging.getLogger("utils.SSHCommand")

class SSHCommand(object):
    
    """
    classdocs
    """
    SSH_CMD = "ssh -q -oConnectTimeout=30 -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null -oPasswordAuthentication=false "

    def __init__(self, cmd, hostOrIp, username = "root", keyfile = os.path.abspath(dissomniag.config.dissomniag.rsaKeyPrivate)):
        """
        Constructor
        """
        
        self.cmd = str(cmd)
        self.hostOrIp = str(hostOrIp)
        self.username = str(username)
        self.keyfile = str(keyfile)
        
    def __repr__(self, *args, **kwargs):
        return " ".join(self.get())
         
    def get(self):
        connectionString = "-\i " + self.keyfile + " " + self.username + "@" + self.hostOrIp + " "
        returnMe = self.SSH_CMD + connectionString + self.cmd
        return shlex.split(returnMe)
        
    def call(self):
        return subprocess.call(self.get())
    
    def callAndGetOutput(self):
        cmd = self.get()
        self.proc = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        self.output = self._readOutput(self.proc)
        com = self.proc.communicate()[0]
        if com != '':
            self.output.append(com)
        self.exitCode = self.proc.returncode
        return self.exitCode, self.output
        
    def _readOutput(self, proc):
        output = []
        while True:
            next = proc.stdout.readline()
            if not next:
                break
            output.append(next.strip())
        
        return output
        
        
        
