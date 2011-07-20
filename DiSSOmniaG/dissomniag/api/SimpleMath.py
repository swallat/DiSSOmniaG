# -*- coding: utf-8 -*-
"""
Created on 19.07.2011

@author: Sebastian Wallat
"""
    
def add(a, b):
    return MathClasses.AddClass(a, b).getValue()

def sub(a, b):
    return MathClasses.SubClass(a, b).getValue()

def mult(a, b):
    return MathClasses.MultClass(a, b).getValue()

def div(a, b):
    return MathClasses.DivClass(a, b).getValue()

import dissomniag.MathClasses as MathClasses
