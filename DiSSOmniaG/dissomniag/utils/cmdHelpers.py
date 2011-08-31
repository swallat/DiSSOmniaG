# -*- coding: utf-8 -*-
"""
Created on 31.08.2011

@author: Sebastian Wallat
"""

def getDpkgCheckInstalledString(packet):
    return ("dpkg-query -W -f='${Status} ${Version}\n' %s" % packet)