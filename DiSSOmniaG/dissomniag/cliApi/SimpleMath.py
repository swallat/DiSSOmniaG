# -*- coding: utf-8 -*-
"""
Created on 19.07.2011

@author: Sebastian Wallat
"""


    
def add(terminal, a, b):
    value = str(MathClasses.AddClass(int(a), int(b)).getValue())
    terminal.write(value)
    terminal.nextLine()

def sub(terminal, a, b):
    terminal.write(str(MathClasses.SubClass(int(a), int(b)).getValue()))
    terminal.nextLine()

def mult(terminal, a, b):
    terminal.write(str(MathClasses.MultClass(int(a), int(b)).getValue()))
    terminal.nextLine()
    
def div(terminal, a, b):
    terminal.write(str(MathClasses.DivClass(int(a), int(b)).getValue()))
    terminal.nextLine()

import dissomniag.MathClasses as MathClasses
