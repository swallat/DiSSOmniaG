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
        """
        starts The server
        """
        if not self.isStarted:
            self.isStarted = True
        else:
            raise dissomniag.Identity.IdentityRestartNotAllowed()
        
        self.user = self.getAdministrativeUser()
        log.info("Starting Dispatcher")
        dissomniag.taskManager.Dispatcher.startDispatcher()
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
                dissomniag.taskManager.Dispatcher.addJob(self.user, job)
        
        # Check existing VM's
        
        try:
            vms = session.query(dissomniag.model.VM).all()
        except NoResultFound:
            pass
        else:
            for vm in vms:
                if (vm.host != None):
                    context = dissomniag.taskManager.Context()
                    context.add(vm, "vm")
                    job = dissomniag.taskManager.Job(context, "Sanity check VM on startup", user = self.user)
                    job.addTask(dissomniag.tasks.statusVM())
                    dissomniag.taskManager.Dispatcher.addJobSyncronized(self.user, vm.host, job)
                    
        self.createSampleTopology()
        
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
        if dissomniag.config.server.useManhole:
            log.info("Starting Manhole Server at Port: %s" % dissomniag.config.server.manholePort)
            dissomniag.server.startManholeServer()
        reactor.run()
        self._tearDown()
        
    def createSampleTopology(self):
        session = dissomniag.Session()
        try:
            topos = session.query(dissomniag.model.Topology).all()
        except NoResultFound:
            pass
        else:
            for topo in topos:
                if topo.name == "SampleTopology":
                    return
                
        #No sample Topo exists
        adminUser = session.query(dissomniag.auth.User).all()[1]
        ident = dissomniag.getIdentity() 
        ip = str(ident.getMaintainanceIP().addr)
        host = dissomniag.model.Host(adminUser, "localhost", "132.252.151.218", "br0", administrativeUserName = "dissomniag-host-user")
        session.add(host)
        dissomniag.saveCommit(session)
        host.checkFull(adminUser)
        topo = dissomniag.model.Topology()
        topo.name = "SampleTopology" 
        session.add(topo)
        dissomniag.saveCommit(session)
        net1 = dissomniag.model.generatedNetwork(adminUser, "10.100.1.0/24", host, topo, "Connection1") 
        net1.xValue = str(83)
        net1.yValue = str(57)
        net1.zValue = str(0)
        session.add(net1)
        dissomniag.saveCommit(session)
        net2 = dissomniag.model.generatedNetwork(adminUser, "10.100.2.0/24", host, topo, "Connection2") 
        net2.xValue = str(285) 
        net2.yValue = str(58) 
        net2.zValue = str(0) 
        session.add(net1)
        dissomniag.saveCommit(session)
        
        vm1 = dissomniag.model.VM(adminUser, "Source", host)
        vm1.xValue = str(17) 
        vm1.yValue = str(9) 
        vm1.zValue = str(0)
        session.add(vm1) 
        dissomniag.saveCommit(session) 
        
        vm2 = dissomniag.model.VM(adminUser, "SimulatedNetwork", host)
        vm2.xValue = str(169) 
        vm2.yValue = str(10) 
        vm2.zValue = str(0.1)
        
        session.add(vm2) 
        dissomniag.saveCommit(session) 
        
        vm3 = dissomniag.model.VM(adminUser, "Sink", host) 
        vm3.xValue = str(406) 
        vm3.yValue = str(16) 
        vm3.zValue = str(0) 
        session.add(vm3) 
        dissomniag.saveCommit(session) 
        
        topo.vms.append(vm1) 
        topo.vms.append(vm2) 
        topo.vms.append(vm3) 
        
        dissomniag.saveCommit(session)
        
        vm1.addInterfaceToNet(adminUser, net1) 
        vm2.addInterfaceToNet(adminUser, net1) 
        vm2.addInterfaceToNet(adminUser, net2) 
        vm3.addInterfaceToNet(adminUser, net2) 
        
        dissomniag.saveCommit(session)
    
    def _tearDown(self):
        #print("Closing Dispatcher")
        log.info("Closing Dispatcher")
        dissomniag.taskManager.Dispatcher.cleanUpDispatcher()
        dissomniag.utils.Logging.doLogEnd()
    
    


        
