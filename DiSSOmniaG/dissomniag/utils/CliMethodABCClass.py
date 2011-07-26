# -*- coding: utf-8 -*-
"""
Created on 25.07.2011

@author: Sebastian Wallat
"""
from abc import ABCMeta, abstractmethod
import sys
import colorama
from colorama import Fore, Style, Back

class CliMethodABCClass(object):
    __metaclass__ = ABCMeta
    """
    classdocs
    """
    @abstractmethod
    def implementation(self, *args):
        pass
    
    def call(self, terminal, user, *args):
        self.terminal = terminal
        self.user = user
        self.initiate(self.terminal)
        try:
            self.implementation(*args)
        except SystemExit:
            pass
        finally:
            self.finish()
        
    def initiate(self, terminal):
        self.oldStdout = sys.stdout
        sys.stdout = terminal
        self.oldErrout = sys.stderr
        sys.stderr = terminal
        colorama.init(autoreset = True)
    
    def finish(self):
        colorama.deinit()
        sys.stdout = self.oldStdout
        sys.stderr = self.oldErrout
        
    def colorString(self, text, color = None, background = None, style = None):
        color = (color if color != None else "")
        background = (background if background != None else "")
        style = (style if style != None else "")
        return color + background + style + text + Fore.RESET + Style.RESET_ALL + Back.RESET
    
    def printError(self, text):
        print(self.colorString(str(text), color = Fore.RED, style = Style.BRIGHT))
    
    def printSuccess(self, text):
        print(self.colorString(str(text), color = Fore.GREEN, style = Style.BRIGHT))
        
    def printInfo(self, text):
        print(self.colorString(str(text), color = Fore.YELLOW, style = Style.BRIGHT))
