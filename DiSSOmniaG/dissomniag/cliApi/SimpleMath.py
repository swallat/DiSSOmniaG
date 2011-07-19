# -*- coding: utf-8 -*-
"""
Created on 19.07.2011

@author: Sebastian Wallat
"""

from dissomniag.MathClasses import AddClass, SubClass, MultClass, DivClass
    
def add(terminal, a, b):
    value = str(AddClass(int(a), int(b)).getValue())
    terminal.write(value)
    terminal.nextLine()

def sub(terminal, a, b):
    terminal.write(str(SubClass(int(a), int(b)).getValue()))
    terminal.nextLine()

def mult(terminal, a, b):
    terminal.write(str(MultClass(int(a), int(b)).getValue()))
    terminal.nextLine()
    
def div(terminal, a, b):
    terminal.write(str(DivClass(int(a), int(b)).getValue()))
    terminal.nextLine()

