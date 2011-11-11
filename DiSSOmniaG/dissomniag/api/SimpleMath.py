# -*- coding: utf-8 -*-
"""
Created on 19.07.2011

@author: Sebastian Wallat
"""
    
def add(user, a, b):
    return str(MathClasses.AddClass(a, b).getValue()) + str(user)

def sub(user, a, b):
    return str(MathClasses.SubClass(a, b).getValue()) + str(user)

def mult(user, a, b):
    return str(MathClasses.MultClass(a, b).getValue())+ str(user)

def div(user, a, b):
    return str(MathClasses.DivClass(a, b).getValue()) + str(user)

import dissomniag.MathClasses as MathClasses
