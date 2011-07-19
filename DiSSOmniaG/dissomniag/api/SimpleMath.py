# -*- coding: utf-8 -*-
"""
Created on 19.07.2011

@author: Sebastian Wallat
"""

from dissomniag.MathClasses import AddClass, SubClass, MultClass, DivClass
    
def add(a, b):
    return AddClass(a, b).getValue()

def sub(a, b):
    return SubClass(a, b).getValue()

def mult(a, b):
    return MultClass(a, b).getValue()

def div(a, b):
    return DivClass(a, b).getValue()
