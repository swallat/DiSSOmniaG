# -*- coding: utf-8 -*-
"""
Created on 12.07.2011

@author: Sebastian Wallat
"""

import inspect

class APIIntrospect(object):
    """
    classdocs
    """


    def __init__(self, moduleName):
        """
        Constructor
        """
        self.moduleName = moduleName
    
    def getMethodList(self):
        """
        Method Description
        """
        return [method for method in dir(self.moduleName) if (callable(getattr(self.moduleName, method)) and method.startswith("_"))]
    
    def getMethodDescription(self, method):
        """
        ToDo
        """
        
    
    
        