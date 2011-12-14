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
    
    def callAndGetOutput(self, withError = True):
        cmd = self.get()
        if withError:
            self.proc = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        else:
            self.proc = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
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
        
        
        
