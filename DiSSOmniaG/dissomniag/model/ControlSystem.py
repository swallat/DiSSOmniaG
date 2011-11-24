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
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import uuid
import thread

import dissomniag
from dissomniag.model import *

log = logging.getLogger("model.ControlSystem")

class ControlSystem(AbstractNode, dissomniag.Identity):
    __mapper_args__ = {'polymorphic_identity': 'ControlSystem'}
    isStarted = False
    user = None
    
    """
    classdocs
    """
    
    #def __new__(cls, *args, **kwargs):
    #    # Store instance on cls._instance_dict with cls hash
    #    key = str(hash(cls)) + str(thread.get_ident())
    #    if not hasattr(cls, '_instance_dict'):
    #        cls._instance_dict = {}
    #    if key not in cls._instance_dict:
    #        cls._instance_dict[key] = \
    #            super(ControlSystem, cls).__new__(cls, *args, **kwargs)
    #    return cls._instance_dict[key]
    
    def __init__(self):
        session = dissomniag.Session()
        self.user = self.getAdministrativeUser()
        try:
            myDbObj = session.query(ControlSystem).one()
        except NoResultFound:
            myDbObj = None
        
        if myDbObj == None and dissomniag.config.dissomniag.isCentral:
            sshPrivateKey, privateKeyString, sshPublicKey, publicKeyString = self.getRsaKeys(all = True)
            sshKey = dissomniag.model.SSHNodeKey()
            sshKey.privateKey = privateKeyString
            sshKey.privateKeyFile = sshPrivateKey
            sshKey.publicKey = publicKeyString
            sshKey.publicKeyFile = sshPublicKey
            self.user.delKeys()
            self.user.addKey(sshKey.publicKey)
            super(ControlSystem, self).__init__(user = self.user, commonName = "Main",
                 sshKey = sshKey,
                 utilityFolder = os.path.abspath(dissomniag.config.dissomniag.configDir),
                 state = dissomniag.model.NodeState.UP,
                 parseLocalInterfaces = True)
            session.add(self)
            self.parseLocalInterfaces(self.user)
            
        elif myDbObj != None and dissomniag.config.dissomniag.isCentral:
            self.commonName = "Main"
            self.state = dissomniag.model.NodeState.UP
            self.utilityFolder = os.path.abspath(dissomniag.config.dissomniag.configDir)
            # Refresh Administrative User keys
            self.user.delKeys()
            self.user.addKey(myDbObj.sshKey.publicKey)
        elif not dissomniag.config.dissomniag.isCentral:
            self.commonName = "Main"
            assert dissomniag.config.dissomniag.centralIp != None
            
            if self.checkCentralSystemRunning(dissomniag.config.dissomnig.centralIP):
                self.state = dissomniag.model.NodeState.UP
            else:
                self.state = dissomniag.model.NodeState.DOWN
            
        if myDbObj == None:
            session.add(self)
        
        dissomniag.saveCommit(session)
        
    def authUser(self, user):
        if user.isAdmin:
            return True
        raise dissomniag.UnauthorizedFunctionCall()
    
    def getIdentityUser(self, user):
        self.authUser(user)
        if self.user == None:
            self.user = self.getAdministrativeUser()
        return self.user
            
    def checkCentralSystemRunning(self, ip):
        ret = subprocess.call("ping -c 1 %s" % ip,
                              shell = True,
                              stdout = open('/dev/null', 'w'),
                              stderr = subprocess.STDOUT)
        if (ret == 0):
            return True
        else:
            return False    
    
    def run(self):
        if not self.isStarted:
            self.isStarted = True
        else:
            raise dissomniag.Identity.IdentityRestartNotAllowed()
        """
        starts The server
        """
        
        #log.info("Securly rollback Session")
        #try:
        #    dissomniag.Session().rollback()
        #except Exception:
        #    pass
        self.user = self.getAdministrativeUser()
        log.info("Starting Dispatcher")
        dissomniag.taskManager.Dispatcher.startDispatcher()
        sw = dissomniag.auth.User.addUser(username = "admin", password = "b00tloader", publicKey = "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAf0N76ZZlEhL6I3+7bMx2Tje+nuAoJ4ylefaiAvl0w5mnYNIfqw7VUlN4TMjBsBReb8b1mefY5XKBEc2FXKSlCBirQeTap9dfYCMN6fJfQfw2IQFUaiXqUJHyvAqGTTtI5bq8d8QA1Kpuc+VJgGdIQXl5wcn4J+z7zB9BfaCrDsZVDTxbObNqCg8M9mc9mNgcoqHam/F6BuU5EDj1tOqXlWPFr2PgAgvvUAjMwvIbKMZU9IaMdG3hzKdoeYjSlQGhxIXH7Qxmv1MWj/O934eSfRTkYp+HEwmeg4IM/kize6IAfnVh6L4KBq1HKXn8SindeY36SZdSP8cl2H6rnA7w2XfC0ercbi2YjUm5iGAPrODbdd5p1LkTTpBt2dpuM23aBZmaQRcreq420ugipXYAL/THSAQ8mcWPbCoLPj+SDY8+GQLys7Wjzj5N1AlBElY9snbFiDefTsWBHarZEkVvOf3j23UN2pHKUIYteKZTuv0/R1mA2zmQr1Btd/nzUqFZqgLjCXkUZk9iG18wlrPSjkFUQOblGP4dn0kGjj3RZdz8ELr4sCiRiqmfe3RNSnFhqQLYZ+I3EObOKLIcAe2LLILYwln1gQHV2K35O0WpBB9XjPXyl65SWIlKqIUOIRmBRemRoA4M3UCKt1I8FN8HIDgxqlw/LzSIL2SsjkOyw== sw@sw-laptop", isAdmin = True, loginManhole = True, loginSSH = True, loginRPC = True, isHtpasswd = False)
        sw.addKey("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDL4E096miP6Zhfne5uZnwPpdzGlUp/3FqLmxOfDednHLfYfuwp7YVJeFOMvHALghf7ICcwr18hGqK0DBj7zfVSzH0nDoj461JnOPELiaoja/Vh7cvzSmrgFTr1VnDHMtQ9Jcm1daMP6WXvQ6amw3pt6CUGM3vSlZ9zdfdqPJhfuy0rJlsiyRY5y8cgDg8xOoZtYlfmQalPOcMvB+qwAKJDgnrXI/2MxVP/YLAM6SY3GY4J59SSoV4sgLSJUMtKrI2V1Vs49GXpiLeLjbShgapeKfvFujF/MeWa2H0xwGaERoChwMqO6ylh7p90lGHh+SJg3a6tAoz9GULv/iGwiZoz sw@R307")
        #Check LiveCd Environment
        context = dissomniag.taskManager.Context()
        job = dissomniag.taskManager.Job(context, "Check the LiveCD assembly environment.", user = self.user)
        job.addTask(dissomniag.tasks.LiveCdEnvironmentChecks())
        job.addTask(dissomniag.tasks.CheckLiveCdEnvironmentPrepared())
        job.addTask(dissomniag.tasks.PrepareLiveCdEnvironment())
        dissomniag.taskManager.Dispatcher.addJobSyncronized(self.user,dissomniag.model.LiveCdEnvironment(), job)
        
        #Check Git Environment
        dissomniag.GitEnvironment().createCheckJob()
        
        # Check existing Hosts
        
        session = dissomniag.Session()
        
        try:
            hosts = session.query(dissomniag.model.Host).all()
        except NoResultFound:
            pass
        else:
            for host in hosts:
                host.checkFull(self.user)
        
        # Check existing Net's
        
        try:
            nets = session.query(dissomniag.model.generatedNetwork).all()
        except NoResultFound:
            pass
        else:
            for net in nets:
                context = dissomniag.taskManager.Context()
                context.add(net, "net")
                job = dissomniag.taskManager.Job(context, "Sanity check generatedNetworks on startup", user = self.user)
                job.addTask(dissomniag.tasks.statusNetwork())
                dissomniag.taskManager.Dispatcher.addJobSyncronized(self.user, net.host, job)
        
        # Check existing VM's
        
        try:
            vms = session.query(dissomniag.model.VM).all()
        except NoResultFound:
            pass
        else:
            for vm in vms:
                context = dissomniag.taskManager.Context()
                context.add(vm, "vm")
                job = dissomniag.taskManager.Job(context, "Sanity check VM on startup", user = self.user)
                job.addTask(dissomniag.tasks.statusVM())
                dissomniag.taskManager.Dispatcher.addJobSyncronized(self.user, vm.host, job)
        
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
    
    


        
