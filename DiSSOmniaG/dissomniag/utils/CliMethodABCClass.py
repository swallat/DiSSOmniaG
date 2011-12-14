# -*- coding: utf-8 -*-
# DiSSOmniaG (Distributed Simulation Service wit OMNeT++ and Git)
# Copyright (C) 2011, 2012 Sebastian Wallat, University Duisburg-Essen
# 
# Based on an idea of:
# Sebastian Wallat <sebastian.wallat@uni-due.de, University Duisburg-Essen
# Hakim Adhari <hakim.adhari@iem.uni-due.de>, University Duisburg-Essen
# Martin Becke <martin.becke@iem.uni-due.de>, University Duisburg-Essen
#
# DiSSOmniaG is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DiSSOmniaG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DiSSOmniaG. If not, see <http://www.gnu.org/licenses/>
import logging
from abc import ABCMeta, abstractmethod
import sys
import colorama
from colorama import Fore, Style, Back

log = logging.getLogger("utils.CliMethodABCClass")

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
