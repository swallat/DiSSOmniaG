# -*- coding: utf-8 -*-
"""
Created on 31.08.2011

@author: Sebastian Wallat
"""
import os
import dissomniag

class LiveCdEnvironmentChecks(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        infoObj = dissomniag.model.LiveCd.LiveCdEnvironment()
        
        #1. Check if Folder is writable
        
    
    def revert(self):
        pass

