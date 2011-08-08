# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm
import logging
import subprocess, os, netifaces
from twisted.internet import reactor

import dissomniag
from dissomniag.model import *

log = logging.getLogger("model.ControlSystem")

class ControlSystem(AbstractNode):
    __mapper_args__ = {'polymorphic_identity': 'ControlSystem'}
    isStarted = False
    
    """
    classdocs
    """
    
    def __new__(cls, *args, **kwargs):
        # Store instance on cls._instance_dict with cls hash
        key = str(hash(cls))
        if not hasattr(cls, '_instance_dict'):
            cls._instance_dict = {}
        if key not in cls._instance_dict:
            cls._instance_dict[key] = \
                super(ControlSystem, cls).__new__(cls, *args, **kwargs)
        return cls._instance_dict[key]
    
    def __init__(self):
        session = dissomniag.Session()
        self.commonName = "Main"
        
        try:
            myDbObj = session.query(ControlSystem).one()
        except NoResultFound:
            myDbObj = None
        
        if dissomniag.config.dissomniag.isCentral:
            self.state = dissomniag.model.NodeState.UP
            self.utilityFolder = os.path.abspath(dissomniag.config.dissomniag.configDir)
        else:
            
            assert dissomniag.config.dissomniag.centralIp != None
            
            if self.checkCentralSystemRunning(dissomniag.config.dissomnig.centralIP):
                self.state = dissomniag.model.NodeState.UP
            else:
                self.state = dissomniag.model.NodeState.DOWN
            
        if myDbObj == None:
                session.add(self)
                session.commit()
        if dissomniag.config.dissomniag.isCentral:
            self.parseLocalInterfaces()
            
    def checkCentralSystemRunning(self, ip):
        ret = subprocess.call("ping -c 1 %s" % ip,
                              shell = True,
                              stdout = ('/dev/null', 'w'),
                              stderr = subprocess.STDOUT)
        if (ret == 0):
            return True
        else:
            return False    
    
    def start(self):
        if not self.isStarted:
            self.isStarted = True
        else:
            raise dissomniag.Identity.IdentityRestartNotAllowed()
        """
        starts The server
        """
        
        log.info("Starting Dispatcher")
        dissomniag.taskManager.Dispatcher.startDispatcher()
        dissomniag.auth.User.addUser(username = "admin", password = "b00tloader", publicKey = "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAf0N76ZZlEhL6I3+7bMx2Tje+nuAoJ4ylefaiAvl0w5mnYNIfqw7VUlN4TMjBsBReb8b1mefY5XKBEc2FXKSlCBirQeTap9dfYCMN6fJfQfw2IQFUaiXqUJHyvAqGTTtI5bq8d8QA1Kpuc+VJgGdIQXl5wcn4J+z7zB9BfaCrDsZVDTxbObNqCg8M9mc9mNgcoqHam/F6BuU5EDj1tOqXlWPFr2PgAgvvUAjMwvIbKMZU9IaMdG3hzKdoeYjSlQGhxIXH7Qxmv1MWj/O934eSfRTkYp+HEwmeg4IM/kize6IAfnVh6L4KBq1HKXn8SindeY36SZdSP8cl2H6rnA7w2XfC0ercbi2YjUm5iGAPrODbdd5p1LkTTpBt2dpuM23aBZmaQRcreq420ugipXYAL/THSAQ8mcWPbCoLPj+SDY8+GQLys7Wjzj5N1AlBElY9snbFiDefTsWBHarZEkVvOf3j23UN2pHKUIYteKZTuv0/R1mA2zmQr1Btd/nzUqFZqgLjCXkUZk9iG18wlrPSjkFUQOblGP4dn0kGjj3RZdz8ELr4sCiRiqmfe3RNSnFhqQLYZ+I3EObOKLIcAe2LLILYwln1gQHV2K35O0WpBB9XjPXyl65SWIlKqIUOIRmBRemRoA4M3UCKt1I8FN8HIDgxqlw/LzSIL2SsjkOyw== sw@sw-laptop", isAdmin = True, loginManhole = True, loginSSH = True, loginRPC = True, isHtpasswd = False)
        #print("Parse Htpasswd File at: %s" % dissomniag.config.htpasswd.htpasswd_file)
        log.info("Parse Htpasswd File at: %s" % dissomniag.config.htpasswd.htpasswd_file)
        dissomniag.auth.parseHtpasswdFile()
        #print("Starting XML-RPC Server at Port: %s" % dissomniag.config.server.rpcPort)
        log.info("Starting XML-RPC Server at Port: %s" % dissomniag.config.server.rpcPort)
        dissomniag.server.startRPCServer()
        #print("Starting SSH Server at Port: %s" % dissomniag.config.server.sshPort)
        log.info("Starting SSH Server at Port: %s" % dissomniag.config.server.sshPort)
        dissomniag.server.startSSHServer()
        #print("Starting Manhole Server at Port: %s" % dissomniag.config.server.manholePort)
        log.info("Starting Manhole Server at Port: %s" % dissomniag.config.server.manholePort)
        dissomniag.server.startManholeServer()
        reactor.run()
        self._tearDown()
        
    
    def _tearDown(self):
        #print("Closing Dispatcher")
        log.info("Closing Dispatcher")
        dissomniag.taskManager.Dispatcher.cleanUpDispatcher()
        dissomniag.utils.Logging.doLogEnd()
    
    


        
