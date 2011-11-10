'''
Created on 27.10.2011

@author: Sebastian Wallat
'''
import os
import shlex
import subprocess
import logging

import dissomniag

log = logging.getLogger("utils.RsyncCommand")

class RsyncCommand(object):
    '''
    classdocs
    '''

    RsyncCommand = 'rsync -a -z '
    
    
    def __init__(self, src, dst, hostOrIp, username = "root", keyfile = os.path.abspath(dissomniag.config.dissomniag.rsaKeyPrivate)):
        """
        Constructor
        """
        
        self.src = str(src)
        self.dst = str(dst)
        self.hostOrIp = str(hostOrIp)
        self.username = str(username)
        self.keyfile = str(keyfile)
        
    def __repr__(self, *args, **kwargs):
        return " ".join(self.get())
        
    def get(self):
        sshKeyPart = '-e "ssh -i %s"' % self.keyfile
        returnMe = self.RsyncCommand + sshKeyPart + ' ' + self.src + ' ' + ('%s@%s:%s' % (self.username, self.hostOrIp, self.dst)) 
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
        