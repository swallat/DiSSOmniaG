# -*- coding: utf-8 -*-
"""
Created on 10.08.2011

@author: Sebastian Wallat
"""
import subprocess
import shlex


def isIpPingable(ip):
    ret = subprocess.call(shlex.split("ping -c 1 %s" % ip),
                            stdout = open('/dev/null', 'w'),
                            stderr = subprocess.STDOUT)
    if (ret == 0):
        return True
    else:
        return False  
