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
# Imports for XML RPC Server
import xmlrpclib, traceback, sys, sched, time, logging
from twisted.web import xmlrpc, server, http
from twisted.internet import defer, reactor, ssl

# Imports for SSH Server
from twisted.cred import portal, checkers, credentials
from twisted.conch import error, avatar, recvline, interfaces as conchinterfaces
from twisted.conch.ssh import factory, userauth, connection, keys, session, common
from twisted.conch.insults import insults
from twisted.application import service, internet
from twisted.python import failure
from zope.interface import implements
import os

# Imports for Manhole Server
from twisted.conch import manhole, manhole_ssh

import dissomniag
from twisted.conch.checkers import SSHPublicKeyDatabase

import dissomniag.auth
from dissomniag.auth import LOGIN_SIGN
from dissomniag import initMigrate

log = logging.getLogger("server")
#===============================================================================
# The Following Twisted XML-RPC Code was extracted in main Parts 
# from the Glab ToMaTo Project.
#===============================================================================


class Introspection():
    def __init__(self, papi):
        self.api = papi

    def listMethods(self, user = None):
        return [m for m in dir(self.api) if (callable(getattr(self.api, m)) 
                                             and not m.startswith("_"))]
    
    # ToDO Reimplememtz
    def methodSignature(self, method, user = None):
        func = getattr(self.api, method)
        if not func:
            return "Unknown method: %s" % method
        import inspect
        argspec = inspect.getargspec(func)
        argstr = inspect.formatargspec(argspec.args[:-1], defaults = argspec.defaults[:-1])
        return method + argstr

    def methodHelp(self, method, user = None):
        func = getattr(self.api, method)
        if not func:
            return "Unknown method: %s" % method
        doc = func.__doc__
        if not doc:
            return "No documentation for: %s" % method
        return doc
        
class APIServer(xmlrpc.XMLRPC):
    #def __init__(self, papi):
    def __init__(self, papi):
        self.api = papi
        self.introspection = Introspection(self.api)
        xmlrpc.XMLRPC.__init__(self, allowNone = True)
        #self.logger = tomato.lib.log.Logger(tomato.config.LOG_DIR + "/api.log")

    #def log(self, function, args, user):
    #    if len(str(args)) < 50:
    #        self.logger.log("%s%s" % (function.__name__, args), user = user.name)
    #    else:
    #        self.logger.log(function.__name__, bigmessage = str(args) + 
    #                        "\n", user = user.name)

    def execute(self, function, args, user):
        try:
            #self.log(function, args, user)
            return function(user, *args)
            #return function(*(args))
        except xmlrpc.Fault, exc:
            #fault.log(exc)
            raise exc
        except Exception, exc:
            #fault.log(exc)
            #self.logger.log("Exception: %s" % exc, user = user.name)
            #raise fault.wrap(exc)
            raise exc

    def render(self, request):
        username = request.getUser()
        passwd = request.getPassword()
        sign, user = dissomniag.auth.User.loginRPCMethod(username, passwd) 
        if sign != LOGIN_SIGN.VALID_USER:
            request.setResponseCode(http.UNAUTHORIZED)
            if username == '' and passwd == '':
                return 'Authorization required!'
            else:
                return 'Authorization Failed!'
        request.content.seek(0, 0)
        args, functionPath = xmlrpclib.loads(request.content.read())
        function = None
        if hasattr(self.api, functionPath):
            function = getattr(self.api, functionPath)
        if functionPath.startswith("_"):
            functionPath = functionPath[1:]
        if hasattr(self.introspection, functionPath):
            function = getattr(self.introspection, functionPath)
        if function:
            request.setHeader("content-type", "text/xml")
            defer.maybeDeferred(self.execute, function, args, user).addErrback(self._ebRender).addCallback(self._cbRender, request)
            return server.NOT_DONE_YET
        
#===============================================================================
# End of Extraction
#===============================================================================

#===============================================================================
# SSH Server
#===============================================================================

class CliIntrospection(Introspection):
    
    def __init__(self, api, terminal):
        Introspection.__init__(self, api)
    
    def listMethods(self, terminal, user = None, *args):
        terminal.write(str(Introspection.listMethods(self, user = user)))
        terminal.nextLine()
        
    def methodHelp(self, terminal, user, methodName, method, *args):
        terminal.write(str(Introspection.methodHelp(self, str(method), user = user)))
        terminal.nextLine()
    
    def methodSignature(self, terminal, user, methodName, method, *args):
        terminal.write(str(Introspection.methodSignature(self, str(method), user = user)))
        terminal.nextLine()
    

class SSHDiSSOmniaGProtocol(recvline.HistoricRecvLine):
    def __init__(self, avatar, api):
        self.avatar = avatar
        self.user = avatar.user
        self.api = api
    
    def connectionMade(self):
        recvline.HistoricRecvLine.connectionMade(self)
        self.introspection = CliIntrospection(self.api, self.terminal)
        self.terminal.write("Welcome to the DiSSOmniaG SSH server.")
        self.terminal.nextLine()
        self.showPrompt()

    def showPrompt(self):
        self.terminal.write("$ ")

    def getCommandFunc(self, cmd):
        functionPath = cmd
        function = None
        if hasattr(self.api, functionPath):
            function = getattr(self.api, functionPath)
        if functionPath.startswith("_"):
            functionPath = functionPath[1:]
        if hasattr(self.introspection, functionPath):
            function = getattr(self.introspection, functionPath)
        if not function:
            function = getattr(self, 'do_' + cmd, None)
        if function:
            return function

    def lineReceived(self, line):
        line = line.strip()
        quitting = False
        if line:
            cmdAndArgs = line.split()
            cmd = cmdAndArgs[0]
            args = cmdAndArgs[1:]
            func = self.getCommandFunc(cmd)
            if func:
                try:
                    quitting = func(self.terminal, self.user, func.__name__, *args)
                except Exception, e:
                    self.terminal.write("Error: %s" % e)
                    self.terminal.nextLine()
            else:
                self.terminal.write("No such command.")
                self.terminal.nextLine()
        if not quitting: self.showPrompt()

    def do_help(self, terminal, user, name, cmd = ''):
        "Get help on a command. Usage: help command"
        if cmd:
            func = self.getCommandFunc(cmd)
            if func:
                self.terminal.write("Help for %s:" % cmd)
                self.terminal.write(func.__doc__)
                self.terminal.nextLine()
                return
        
        publicMethods = filter(
            lambda funcname: funcname.startswith('do_'), dir(self))
        commands = [cmd.replace('do_', '', 1) for cmd in publicMethods]
        self.terminal.write("Commands: " + " ".join(commands))
        self.terminal.nextLine()

    def do_echo(self, terminal, user, *args):
        "Echo a string. Usage: echo my line of text"
        self.terminal.write(" ".join(args))
        self.terminal.nextLine()

    def do_quit(self, terminal, user, *args):
        "Ends your session. Usage: quit"
        self.terminal.write("Bye")
        self.terminal.nextLine()
        self.terminal.loseConnection()

    def do_clear(self, terminal, user, *args):
        "Clears the screen. Usage: clear"
        self.terminal.reset()

    def connectionLost(self, reason):
        pass  
    
class SSHDiSSOmniaGPublicKeyDatabase(SSHPublicKeyDatabase):
    
    def _cbRequestAvatarId(self, validKey, credentials):
        returnMe = SSHPublicKeyDatabase._cbRequestAvatarId(self, validKey[0], credentials)
        if returnMe == validKey[1].username:
            return validKey[1]
        else:
            return returnMe
            
    def checkKey(self, credentials):
        validFlag, user = dissomniag.auth.User.loginSSHMethod(username = credentials.username, key = credentials.blob)
        if validFlag == LOGIN_SIGN.VALID_USER:
            return [True, user]
        elif validFlag == LOGIN_SIGN.NO_SUCH_USER:
            raise failure.Failure(error.ConchError("No such user"))
        elif validFlag == LOGIN_SIGN.UNVALID_ACCESS_METHOD:
            raise failure.Failure(error.ConchError("I don't recognize that key"))
        elif validFlag == LOGIN_SIGN.SECRET_UNVALID:
            raise failure.Failure(error.ConchError("I don't recognize that key"))
        else:
            raise failure.Failure(error.ConchError("Unspecified failure"))
        
class ManholeDiSSOmniaGPublicKeyDatabase(SSHPublicKeyDatabase):
    def _cbRequestAvatarId(self, validKey, credentials):
        returnMe = SSHPublicKeyDatabase._cbRequestAvatarId(self, validKey[0], credentials)
        if returnMe == validKey[1].username:
            return validKey[1]
        else:
            return returnMe
            
    def checkKey(self, credentials):
        validFlag, user = dissomniag.auth.User.loginManholeMethod(username = credentials.username, key = credentials.blob)
        if validFlag == LOGIN_SIGN.VALID_USER:
            return [True, user]
        elif validFlag == LOGIN_SIGN.NO_SUCH_USER:
            raise failure.Failure(error.ConchError("No such user"))
        elif validFlag == LOGIN_SIGN.UNVALID_ACCESS_METHOD:
            raise failure.Failure(error.ConchError("I don't recognize that key"))
        elif validFlag == LOGIN_SIGN.SECRET_UNVALID:
            raise failure.Failure(error.ConchError("I don't recognize that key"))
        else:
            raise failure.Failure(error.ConchError("Unspecified failure"))
                                                
class SSHDiSSOmniaGUserAuthDatabase:
    credentialInterfaces = credentials.IUsernamePassword,
    implements(checkers.ICredentialsChecker)
    
    def requestAvatarId(self, credentials):
        validFlag, user = dissomniag.auth.User.loginSSHMethod(username = credentials.username, passwd = credentials.password)
        if validFlag == LOGIN_SIGN.VALID_USER:
            return defer.succeed(user)
        else:
            return defer.fail(error.UnauthorizedLogin("unable to verify password"))
        
class ManholeDiSSOmniaGUserAuthDatabase:
    credentialInterfaces = credentials.IUsernamePassword,
    implements(checkers.ICredentialsChecker)
    
    def requestAvatarId(self, credentials):
        validFlag, user = dissomniag.auth.User.loginManholeMethod(username = credentials.username, passwd = credentials.password)
        if validFlag == LOGIN_SIGN.VALID_USER:
            return defer.succeed(user)
        else:
            return defer.fail(error.UnauthorizedLogin("unable to verify password"))
    
class SSHDiSSOmniaGAvatar(avatar.ConchUser):
    implements(conchinterfaces.ISession)
    
    def __init__(self, user, api):
        avatar.ConchUser.__init__(self)
        self.user = user
        self.api = api
        self.channelLookup.update({'session':session.SSHSession})

    def openShell(self, protocol):
        self.serverProtocol = insults.ServerProtocol(SSHDiSSOmniaGProtocol, self, self.api)
        self.serverProtocol.makeConnection(protocol)
        protocol.makeConnection(session.wrapProtocol(self.serverProtocol))

    def getPty(self, terminal, windowSize, attrs):
        return None

    def execCommand(self, protocol, cmd):
        self.protocol = protocol
        self.openShell(protocol)
        self.serverProtocol.write(cmd)
        #raise NotImplementedError
        
    def closed(self):
        pass

class SSHDiSSOmniaGRealm:
    implements(portal.IRealm)
    
    def __init__(self, api):
        self.api = api
        
    def requestAvatar(self, avatarId, mind, *interfaces):
        if conchinterfaces.IConchUser in interfaces:
            return interfaces[0], SSHDiSSOmniaGAvatar(avatarId, self.api), lambda: None
        else:
            raise Exception, "No supported interfaces found."

class DiSSOmniaGSSHFactory(factory.SSHFactory):
    pass

#===============================================================================
# End SSH Server
#===============================================================================

#===============================================================================
# Manhole Server
#===============================================================================

def getManholeFactory(namespace):
    realm = manhole_ssh.TerminalRealm()
    def getManhole(_): return manhole.ColoredManhole(namespace)
    realm.chainedProtocolFactory.protocolFactory = getManhole
    p = portal.Portal(realm)
    p.registerChecker(ManholeDiSSOmniaGPublicKeyDatabase())
    p.registerChecker(ManholeDiSSOmniaGUserAuthDatabase())
    f = manhole_ssh.ConchFactory(p)
    return f

#===============================================================================
# End Manhole Server
#===============================================================================

#    Easiest way to create the key file pair was to use OpenSSL -- http://openssl.org/ Windows binaries are available
#    You can create a self-signed certificate easily "openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout privatekey.pem"
#    for more information --  http://docs.python.org/library/ssl.html#ssl-certificates
#KEYFILE='/etc/ssl/private/ssl-cert-snakeoil.key'    # Replace with your PEM formatted key file
#CERTFILE='/etc/ssl/certs/ssl-cert-snakeoil.pem'  # Replace with your PEM formatted certificate file
        
def startRPCServer():
    api_server = APIServer(dissomniag.api)
    if dissomniag.config.ssl.SSL:
        sslContext = ssl.DefaultOpenSSLContextFactory(dissomniag.config.ssl.privateKey, dissomniag.config.ssl.caKey)
        reactor.listenSSL(dissomniag.config.server.rpcPort, server.Site(api_server), contextFactory = sslContext) 
    else:
        reactor.listenTCP(dissomniag.config.server.rpcPort, server.Site(api_server))

def startSSHServer():
    Portal = portal.Portal(SSHDiSSOmniaGRealm(dissomniag.cliApi))
    
    Portal.registerChecker(SSHDiSSOmniaGPublicKeyDatabase())
    Portal.registerChecker(SSHDiSSOmniaGUserAuthDatabase())
    
    publicKeyString, rsaKey = dissomniag.getIdentity().getRsaKeys()
    DiSSOmniaGSSHFactory.portal = Portal
    DiSSOmniaGSSHFactory.publicKeys = {'ssh-rsa': publicKeyString}
    DiSSOmniaGSSHFactory.privateKeys = {'ssh-rsa': rsaKey}
    reactor.listenTCP(dissomniag.config.server.sshPort, DiSSOmniaGSSHFactory())

def startManholeServer():
    reactor.listenTCP(dissomniag.config.server.manholePort, getManholeFactory(globals()))
