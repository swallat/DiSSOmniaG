# -*- coding: utf-8 -*-
'''
Created on 16.11.2011

@author: Sebastian Wallat
'''
import dissomniag
import logging

log = logging.getLogger("GitEnvironment")


class GitEnvironment(dissomniag.utils.SingletonMixin):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        pass
    
    
    def prepare(self):
        pass
    
    def isUpTodate(self):
        pass
    
    def getNewConfig(self):
        pass
    
    def getConfigAndHash(self):
        pass
    
    def getUserApps(self, user):
        """
        Get all sections in config where user is used
        """
        pass
    
    def checkout(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
    
    def commit(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
    
    def addKeyToKeyDir(self, job, pubKeyString):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
    
    def updateConfig(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
    
    def pull(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject()
    
    def push(self, job):
        if not isinstance(job, dissomniag.taskManager.Job):
            raise dissomniag.utils.MissingJobObject() 