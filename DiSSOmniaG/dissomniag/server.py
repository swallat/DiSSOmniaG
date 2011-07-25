# -*- coding: utf-8 -*-
"""
Created on 19.07.2011

@author: Sebastian Wallat
"""
# Imports for XML RPC Server
import xmlrpclib, traceback, sys
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
            #return function(*(args[0]), user = user, **(args[1]))
            return function(*(args))
        except xmlrpc.Fault, exc:
            #fault.log(exc)
            raise
        except Exception, exc:
            #fault.log(exc)
            #self.logger.log("Exception: %s" % exc, user = user.name)
            #raise fault.wrap(exc)
            raise

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
    
    def listMethods(self, terminal, user = None):
        terminal.write(str(Introspection.listMethods(self, user = user)))
        terminal.nextLine()
        
    def methodHelp(self, terminal, method, user = None):
        terminal.write(str(Introspection.methodHelp(self, str(method), user = user)))
        terminal.nextLine()
    
    def methodSignature(self, terminal, method, user = None):
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
                    quitting = func(self.terminal, self.user, *args)
                except Exception, e:
                    self.terminal.write("Error: %s" % e)
                    self.terminal.nextLine()
            else:
                self.terminal.write("No such command.")
                self.terminal.nextLine()
        if not quitting: self.showPrompt()

    def do_help(self, cmd = ''):
        "Get help on a command. Usage: help command"
        if cmd:
            func = self.getCommandFunc(cmd)
            if func:
                self.terminal.write(func.__doc__)
                self.terminal.nextLine()
                return
        
        publicMethods = filter(
            lambda funcname: funcname.startswith('do_'), dir(self))
        commands = [cmd.replace('do_', '', 1) for cmd in publicMethods]
        self.terminal.write("Commands: " + " ".join(commands))
        self.terminal.nextLine()

    def do_echo(self, terminal, *args):
        "Echo a string. Usage: echo my line of text"
        self.terminal.write(" ".join(args))
        self.terminal.nextLine()

    def do_whoami(self, terminal, user, *args):
        "Prints your user name. Usage: whoami"
        self.terminal.write(self.user.username)
        self.terminal.nextLine()

    def do_quit(self, terminal, *args):
        "Ends your session. Usage: quit"
        self.terminal.write("Bye")
        self.terminal.nextLine()
        self.terminal.loseConnection()

    def do_clear(self, terminal, *args):
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
        serverProtocol = insults.ServerProtocol(SSHDiSSOmniaGProtocol, self, self.api)
        serverProtocol.makeConnection(protocol)
        protocol.makeConnection(session.wrapProtocol(serverProtocol))

    def getPty(self, terminal, windowSize, attrs):
        return None

    def execCommand(self, protocol, cmd):
        raise NotImplementedError
        
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
        
def getRSAKeys():
    if not (os.path.exists('public.key') and os.path.exists('private.key')):
        #generate a RSA keypar
        print "Generating RSA keypair..."
        from Crypto.PublicKey import RSA
        KEY_LENGTH = 1024
        rsaKey = keys.Key(RSA.generate(KEY_LENGTH))
        publicKeyString = rsaKey.public().toString('OPENSSH')
        privateKeyString = rsaKey.toString('OPENSSH')
        #save keys for next time
        file('public.key', 'w+b').write(publicKeyString)
        file('private.key', 'w+b').write(privateKeyString)
        print "done."
    else:
        privateKeyString = file('private.key', 'r').read()
        rsaKey = keys.Key.fromString(privateKeyString)
        publicKeyString = file('public.key', 'r').read()
    return publicKeyString, rsaKey

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


        
def startRPCServer():
    api_server = APIServer(dissomniag.api)
    if dissomniag.config.SSL:
        sslContext = ssl.DefaultOpenSSLContextFactory(dissomniag.config.SSL_PrivKey, dissomniag.config.SSL_CaKey)
        reactor.listenSSL(dissomniag.config.rpcServerPort, server.Site(api_server), contextFactory = sslContext) 
    else:
        reactor.listenTCP(dissomniag.config.rpcSserverPort, server.Site(api_server))

def startSSHServer():
    Portal = portal.Portal(SSHDiSSOmniaGRealm(dissomniag.cliApi))
    
    Portal.registerChecker(SSHDiSSOmniaGPublicKeyDatabase())
    Portal.registerChecker(SSHDiSSOmniaGUserAuthDatabase())
    
    publicKeyString, rsaKey = getRSAKeys()
    DiSSOmniaGSSHFactory.portal = Portal
    DiSSOmniaGSSHFactory.publicKeys = {'ssh-rsa': publicKeyString}
    DiSSOmniaGSSHFactory.privateKeys = {'ssh-rsa': rsaKey}
    reactor.listenTCP(dissomniag.config.sshServerPort, DiSSOmniaGSSHFactory())

def startManholeServer():
    reactor.listenTCP(dissomniag.config.manholeServerPort, getManholeFactory(globals()))


def startServer():
    print("Parse Htpasswd File at: %s" % dissomniag.config.HTPASSWD_FILE)
    dissomniag.auth.parseHtpasswdFile()
    print("Starting XML-RPC Server at Port: %s" % dissomniag.config.rpcServerPort)
    startRPCServer()
    print("Starting SSH Server at Port: %s" % dissomniag.config.sshServerPort)
    startSSHServer()
    print("Starting Manhole Server at Port: %s" % dissomniag.config.manholeServerPort)
    startManholeServer()
    
    reactor.run()

if __name__ == '__main__':
    startServer()
