# -*- coding: utf-8 -*-
"""
Created on 26.07.2011

@author: Sebastian Wallat
"""
import logging

log = logging.getLogger("utils.Exceptions")

class BadKeyError(Exception):
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)
    
class NotStringError(Exception):
    pass

class NoValidMac(Exception):
    pass

class LogicalError(Exception):
    pass

class UnauthorizedFunctionCall(Exception):
    pass

class MissingJobObject(Exception):
    pass

class NoMaintainanceIp(Exception):
    pass
