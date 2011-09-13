# -*- coding: utf-8 -*-
"""
Created on 13.09.2011

@author: Sebastian Wallat
"""

import os
import shlex
import subprocess
import logging

import dissomniag

log = logging.getLogger("utils.SubprocessCommand")

class InteractiveCommand(object):
    
    ending = '; echo "###:"$?":###"\n'
    
    def __init__(self, cmdToInteract, log):
        
        self.cmdToInteract = str(cmdToInteract)
        self.log = log
        self.proc = None
    
    def __repr__(self, *args, **kwargs):
        return " ".join(self.get())
    
    def get(self):
        return shlex.split(self.cmdToInteract)
    
    def init(self):
        self.proc = subprocess.Popen(self.get(), stdin = subprocess.PIPE,
                                                 stdout = subprocess.PIPE,
                                                 stderr = subprocess.STDOUT)
    def callCmd(self, cmd):
        self.proc.stdin.write(cmd)
        returnCode = 1
        while True:
            line = self.proc.stdout.readline()
            if not line:
                break
            elif line.startswith('###') and (line.endswith('###\n') or line.endswith('###')):
                splitter = line.split(":")
                returnCode = splitter[1]
            
            self.log.info(line)
        
        return int(returnCode)
    
    def close(self):
        self.proc.stdin.write("quit\n")
        self.proc.terminate()
        return self.proc.returncode
        
        
    
    
        
