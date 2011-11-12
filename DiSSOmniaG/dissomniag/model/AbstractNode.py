# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import abc
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import logging
import netifaces
import uuid

import dissomniag
from dissomniag.model import *

log = logging.getLogger("model.AbstractNode")

class NodeState:
    UP = 0
    DOWN = 1
    NOT_CREATED = 2
    PREPARED = 3
    PREPARE_ERROR = 4
    DEPLOYED = 5
    DEPLOY_ERROR = 6
    CREATED = 7
    RUNTIME_ERROR = 8 
    CONNECTION_ERROR = 9
    CREATION_ERROR = 10 # Deprecated
    
    
    @staticmethod
    def getStateName(state):
        if state == NodeState.UP:
            return "UP"
        elif state == NodeState.DOWN:
            return "DOWN"
        elif state == NodeState.NOT_CREATED:
            return "NOT CREATED"
        elif state == NodeState.PREPARED:
            return "PREPARED"
        elif state == NodeState.PREPARE_ERROR:
            return "PREPARE_ERROR"
        elif state == NodeState.DEPLOYED:
            return "DEPLOYED"
        elif state == NodeState.DEPLOY_ERROR:
            return "DEPLOY_ERROR"
        elif state == NodeState.CREATED:
            return "CREATED"
        elif state == NodeState.CREATION_ERROR:
            return "CREATION_ERROR"
        elif state == NodeState.RUNTIME_ERROR:
            return "RUNTIME_ERROR"
        elif state == NodeState.CONNECTION_ERROR:
            return "CONNECTION_ERROR"
        else:
            return None
    
    @staticmethod
    def checkIn(state):
        if 0 <= state < 11:
            return True
        else:
            return False

class AbstractNode(dissomniag.Base):
    __tablename__ = "nodes" 
    id = sa.Column(sa.Integer, primary_key = True)
    uuid = sa.Column(sa.String(36), nullable = False, unique = True)
    commonName = sa.Column(sa.String(40), nullable = False, unique = True)
    sshKey_id = sa.Column(sa.Integer, sa.ForeignKey('sshNodeKeys.id')) #One to One
    sshKey = orm.relationship("SSHNodeKey", backref = orm.backref("node", uselist = False))
    administrativeUserName = sa.Column(sa.String(), default = "root", nullable = False)
    utilityFolder = sa.Column(sa.String(200), nullable = True)
    state = sa.Column(sa.Integer, sa.CheckConstraint("0 <= state < 11", name = "nodeState"), nullable = False)
    interfaces = orm.relationship('Interface', backref = "node") #One to Many style
    
    networks = orm.relationship('Network', secondary = node_network, backref = 'nodes')
    
    discriminator = sa.Column('type', sa.String(50), nullable = False)
    __mapper_args__ = {'polymorphic_on': discriminator}
    """
    classdocs
    """
    
    def __init__(self, user, commonName, setMyUuid = None, maintainanceIP = None,
                 sshKey = None, administrativeUserName = None,
                 utilityFolder = None, state = None,
                 parseLocalInterfaces = False):
        session = dissomniag.Session()
        self.commonName = commonName
        if setMyUuid == None:
            self.uuid = str(uuid.uuid4())
        else:
            self.uuid = uuid
            
        if state != None and NodeState.checkIn(state):
            self.state = state
        else:
            self.state = NodeState.NOT_CREATED
            
        session.add(self)
        dissomniag.saveCommit(session)
        
        if maintainanceIP != None:
            self.addIp(user, maintainanceIP, isMaintainanceIP = True)
        
        if sshKey != None and isinstance(sshKey, SSHNodeKey):
            self.sshKey = sshKey
        
        if administrativeUserName != None:
            self.administrativeUserName = administrativeUserName
            
        if utilityFolder != None:
            self.utilityFolder = utilityFolder
        
        if parseLocalInterfaces:
            self.parseLocalInterfaces(user)
        
        if maintainanceIP == None and len(self.ipAddresses) > 0:
            self.maintainanceIP = self.ipAddresses[0]
        
            
    def addIp(self, user, ipAddrOrNet, isMaintainanceIP = False, interface = None, net = None):
        """
        Add a Ip to a Node
        By setting an Interface, you specify the interface to which the Ip should belong.
        If the interface doesn't belong to the current Node, it is ignored.
        If there are other equal IP's which belong to the current node, they are going to be deleted.
        By setting isMaintainanceIP = True, you specify the new maintainanceIP of the current node.
        
        :caution:
            The old maintainanceIP is not deleted! You must do it yourself.
        """
        
        self.authUser(user)
        
        session = dissomniag.Session()
        if type(ipAddrOrNet) == str:
            ipAddrOrNet = ipaddr.IPNetwork(ipAddrOrNet)
        ip = None
        found = False
        if interface != None and interface not in self.interfaces:
            # If the interface does not belong to the current node
            # ignore the interface specification
            interface = None
        try:
            # Find ip for all interfaces
            ip = session.query(dissomniag.model.IpAddress).filter(dissomniag.model.IpAddress.addr == str(ipAddrOrNet.ip)).filter(dissomniag.model.IpAddress.node == self).one()
            found = True
        except NoResultFound:
            found = False
        except MultipleResultsFound:
            try:
                one = False
                ips = session.query(dissomniag.model.IpAddress).filter(dissomniag.model.IpAddress.addr == str(ipAddrOrNet.ip)).filter(dissomniag.model.IpAddress.node == self).all()
                for myIp in ips:
                    #Not the correct interface
                    if interface != None and isinstance(interface, Interface) and myIp.interface != interface:
                        IpAddress.deleteIpAddress(user, myIp, isAdministrative = True) #Delete Invalid Interfaces
                        continue
                    if not one:
                        ip = myIp
                        one = True
                    else:
                        IpAddress.deleteIpAddress(user, myIp, isAdministrative = True) #Delete Invalid Interfaces
                found = False
            except NoResultFound:
                found = False
        finally:
            if found == False and ip == None:
                if interface != None and interface in self.interfaces:
                    ip = interface.addIp(user, ipAddrOrNet, net = net)
                else:
                    ip = dissomniag.model.IpAddress(user, ipAddrOrNet, self, net = net)
                    self.ipAddresses.append(ip)
                if isMaintainanceIP:
                    oldMaintainance = self.getMaintainanceIP()
                    if oldMaintainance != None:
                        oldMaintainance.isMaintainance = False
                    ip.isMaintainance = True
                dissomniag.saveCommit(session)
                return ip
            elif found == True and ip != None:
                if isMaintainanceIP:
                    oldMaintainance = self.getMaintainanceIP()
                    if oldMaintainance != None:
                        oldMaintainance.isMaintainance = False
                    ip.isMaintainance = True
                dissomniag.saveCommit(session)
                return ip
            else:
                dissomniag.saveCommit(session)
                return None
    
    def parseLocalInterfaces(self, user):
        
        self.authUser(user)
        
        excludedInterfaces = ['lo', 'lo0']
        excludedIps = ['fe80:', '172.0.0.1']
        interfaceCodes = {"mac" : 17, 'ipv4': 2 , 'ipv6' : 10}
        session = dissomniag.Session()
        interfaces = netifaces.interfaces()
        
        savedInterfaces = []
        
        for interface in interfaces:
            if interface in excludedInterfaces:
                continue
            myInt = None
            
            addresses = netifaces.ifaddresses(interface)
            for key in addresses:
                if key == interfaceCodes['mac'] and myInt == None:
                    for address in addresses[key]:
                        try:
                            myInt = session.query(Interface).filter(Interface.macAddress == address['addr']).one()
                            continue # Check if IP have changed
                        except NoResultFound:
                            myInt = Interface(user, self, interface, address['addr'])
                elif (key == interfaceCodes['ipv4'] or key == interfaceCodes['ipv6']) and myInt != None:
                    
                    for address in addresses[key]:
                        found = False
                        for exclude in excludedIps:
                            if address['addr'].startswith(exclude):
                                found = True
                                break
                        if found:
                            continue
                        if key == interfaceCodes['ipv4']:
                            ipFullString = ("%s/%s" % (address['addr'], address['netmask']))
                        else:
                            try:
                                ipv6Netmask = dissomniag.model.IpAddress.parseIpv6Netmask(address['netmask'])
                            except dissomniag.model.NoIpv6Mask:
                                continue
                            else:
                                ipFullString = ("%s/%s" % (address['addr'], ipv6Netmask))
                        
                        
                        myInt.addIp(user, ipFullString)
                    
                else:
                    print("parseLocalInterfaces tried to add a seond mac to a interface or tried to add a ip to a non existing interface")
            if myInt != None:
                self.interfaces.append(myInt)
                savedInterfaces.append(myInt)
        # Delete unused Interfaces
        for interface in self.interfaces:
            if not (interface in savedInterfaces):
                Interface.deleteInterface(user, interface, isAdministrative = True)
        if self.getMaintainanceIP() == None:
            self.ipAddresses[0].isMaintainance = True
    
    def addInterface(self, user, name, mac = None, ipAddresses = [], net = None):
        """
        This method adds an interface to the current node with the name = "name".
        If no Mac Address is provided, a new one is generated.
        By adding a list of IPAddresses it is possible to assign IpAddresses to an interface.
        
        If the provided Mac Adresss is not valid this method raises an NoMacError(),
        which can be found in dissomniag.utils.Exceptions()
        """
        self.authUser(user)
        
        session = dissomniag.Session()
        interface = None
        if type(name) != str:
            raise dissomniag.NotStringError()
        if mac == None:
            mac = Interface.getRandomMac()
        # Raises NoValidMac on Mac Failure
        Interface.checkValidMac(mac)
        
        try:
            interface = session.query(Interface).filter(Interface.macAddress == mac).filter(Interface.node == self).one()
        except NoResultFound:
            interface = None
        except MultipleResultsFound:
            interfaces = session.query(Interface).filter(Interface.macAddress == mac).filter(Interface.node == self).all()
            one = False
            name = False
            for inter in interfaces:
                if not one:
                    interface = inter
                    if interface.name == name:
                        name = True
                    one = True
                elif one and not name:
                    if inter.name == name:
                        Interface.deleteInterface(user, inter, isAdministrative = True)
                        interface = inter
                        name = True
                elif one and name:
                    Interface.deleteInterface(user, inter, isAdministrative = True)             
        finally:
            if interface == None:
                interface = Interface(user, self, name, mac)
                self.interfaces.append(interface)
                
            for ipAddr in ipAddresses:
                interface.addIp(user, ipAddr, net = net)     
            try:
                equalNamedInterfaces = session.query(Interface).filter(Interface.name == name).filter(Interface.node == self).all()
                for namedInterface in equalNamedInterfaces:
                    if namedInterface.macAddress != mac:
                        #Delete all Equally named Interfaces
                        Interface.deleteInterface(user, namedInterface, isAdministrative = True)
            except NoResultFound:
                pass
            
            dissomniag.saveCommit(session)
            return interface           
    
    def modUtilityFolder(self, user, folder):
        self.authUser(user)
        self.utilityFolder = folder
    
    def modSSHNodeKey(self, user, privateKeyFile = None, publicKeyFile = None, privateKey = None, publicKey = None):
        self.authUser(user)
        if privateKeyFile != None:
            self.sshKey.privateKeyFile = privateKeyFile
            
        if publicKeyFile != None:
            self.sshKey.publicKeyFile = publicKeyFile
        
        if privateKey != None:
            self.sshKey.privateKey = privateKey
        
        if publicKey != None:
            self.sshKey.publicKey = publicKey
    
    def modMaintainanceIP(self, user, newIp, deleteOld = False, interface = None):
        self.authUser(user)
        if deleteOld and self.getMaintainanceIP() != None:
            IpAddress.deleteIpAddress(user, self.getMaintainanceIP(), isAdministrative = True)
            
        return self.addIp(user, newIp, isMaintainanceIP = True, interface = interface)
    
    def modAdministrativeUserName(self, user, username):
        self.authUser(user)
        self.administrativeUserName = username
    
    def reDefineMaintainanceIPOnInterfaceDelete(self, user, interface):
        self.authUser(user)
        if hasattr(self, "maintainanceIP") and self.maintainanceIP != None and self.maintainanceIP.interface == interface:
            for myInter in self.interfaces:
                if myInter == interface:
                    continue
                elif not myInter.ipAddresses:
                    continue
                else:
                    if myInter.ipAddresses:
                        myInter.ipAddresses[0].isMaintainance = True
                        return True
            return False
        else:
            return True
        
    def authUser(self, user):
        raise NotImplementedError()
    
    def changeState(self, user, state):
        self.authUser(user)
        
        session = dissomniag.Session()
        if not NodeState.checkIn(state):
            return False
        else:
            self.state = state
        dissomniag.saveCommit(session)
    
    def getMaintainanceIP(self):
        for ip in self.ipAddresses:
            if ip.isMaintainance:
                return ip
        return None
    
    @staticmethod
    def deleteNode(user, node):
        raise NotImplementedError()
    
    @staticmethod
    def getNodeState(user, nodeId = None, nodeUUID = None, nodeName = None):
        if nodeId == None and nodeUUID == None and nodeName == None:
            raise dissomniag.LogicalError()
        session = dissomniag.Session()
        node = None
        try:
            if nodeId != None:
                node = session.query(AbstractNode).filter(AbstractNode.id == nodeId).one()
            elif nodeUUID != None and node == None:
                node = session.query(AbstractNode).filter(AbstractNode.uuid == nodeUUID).one()
            elif nodeName != None and node == None:
                node = session.query(AbstractNode).filter(AbstractNode.name == nodeName).one()
        except (NoResultFound, MultipleResultsFound):
            raise dissomniag.LogicalError()
        node.authUser(user)
        return node.state                  
    
    


        
