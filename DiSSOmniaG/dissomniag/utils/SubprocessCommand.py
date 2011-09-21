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

class StandardCmd(object):
    
    def __init__(self, cmd, log):
        
        if type(cmd) == 'list':
            self.cmd = cmd
        else:
            self.cmd = shlex.split(cmd)
        
        self.log = log
        self.output = []
        self.runned = False
        
    def multiLog(self, msg):
        msg = msg.strip()
        self.log.info(msg)
        self.output.append(msg)
        
    def run(self):
        if self.runned:
            raise RuntimeError('A Standard CMD can only be called once.')
        
        self.runned = True
        
        self.multiLog("Running %s" % " ".join(self.cmd))
        
        self.proc = subprocess.Popen(self.cmd, stdin = subprocess.PIPE,
                                               stdout = subprocess.PIPE,
                                               stderr = subprocess.STDOUT)#
        self._readOutput(self.proc)
        com = self.proc.communicate()[0]
        if com != []:
            self.multiLog(com)
        return self.proc.returncode, self.output
    
    def _readOutput(self, proc):
        while True:
            line = proc.stdout.readline()
            if not line:
                return
            self.multiLog(line)
        
        

class InteractiveCommand(object):
    
    ending = '; echo "###:"$?":###"\n'
    
    def __init__(self, cmdToInteract, log):
        
        self.cmdToInteract = str(cmdToInteract)
        self.log = log
        self.proc = subprocess.Popen(self.get(), stdin = subprocess.PIPE,
                                                 stdout = subprocess.PIPE,
                                                 stderr = subprocess.STDOUT)
    
    def __repr__(self, *args, **kwargs):
        return " ".join(self.get())
    
    def get(self):
        return shlex.split(self.cmdToInteract)

    def callCmd(self, cmd, doYes = False):
        cmd = cmd + self.ending
        self.proc.stdin.write(cmd)
        returnCode = 1
        output = []
        while True:
            line = self.proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            
            if line.startswith('###') and (line.endswith('###\n') or line.endswith('###')):
                splitter = line.split(":")
                returnCode = splitter[1]
                self.log.info(line)
                output.append(line)
                return int(returnCode), output
            elif 'Yes, do as I say!' in line:
                if doYes:
                    output.append("Writing Yes, do as I say!")
                    self.log.info("Writing Yes, do as I say!")
                    self.proc.stdin.write('Yes, do as I say!\n')
                else:
                    output.append("Writing No")
                    self.log.info("Writing No")
                    self.proc.stdin.write('No\n')
            
            output.append(line)
            self.log.info(line)
        
        return -1, output # Failure. No ending Line!!
        
        
    
    def close(self):
        self.proc.stdin.write("quit\n")
        self.proc.terminate()
        return self.proc.returncode
        
        
    
    
        
