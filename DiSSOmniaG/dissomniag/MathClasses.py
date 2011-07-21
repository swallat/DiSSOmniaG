# -*- coding: utf-8 -*-
"""
Created on 19.07.2011

@author: Sebastian Wallat
"""

class AddClass(object):
    """
    classdocs
    """


    def __init__(self, a, b):
        """
        Constructor
        """
        self.a = a
        self.b = b
        self.calc()
    
    def calc(self):
        self.calc = self.a + self.b
        
    def getValue(self):
        return self.calc
    
class SubClass(object):
    
    def __init__(self, a, b):
        """
        Constructor
        """
        self.a = a
        self.b = b
        self.calc()
    
    def calc(self):
        self.calc = self.a - self.b
        
    def getValue(self):
        return self.calc

class MultClass(object):
    
    def __init__(self, a, b):
        """
        Constructor
        """
        self.a = a
        self.b = b
        self.calc()
    
    def calc(self):
        self.calc = self.a * self.b
        
    def getValue(self):
        return self.calc
    
class DivClass(object):
    
    def __init__(self, a, b):
        """
        Constructor
        """
        self.a = a
        self.b = b
        self.calc()
    
    def calc(self):
        self.calc = self.a / self.b
        
    def getValue(self):
        return self.calc      
