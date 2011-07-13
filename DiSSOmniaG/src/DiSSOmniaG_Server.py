#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on 12.07.2011

@author: Sebastian Wallat
"""
import xmlrpclib, traceback
from twisted.web import xmlrpc, server, http
from twisted.internet import defer, reactor, ssl

class Example(xmlrpc.XMLRPC):
    """An example object to be published."""

    def xmlrpc_echo(self, x):
        """
        Return all passed args.
        """
        return x

    def xmlrpc_add(self, a, b):
        """
        Return sum of arguments.
        """
        return a + b

    def xmlrpc_fault(self):
        """
        Raise a Fault indicating that the procedure should not be used.
        """
        raise xmlrpc.Fault(123, "The fault procedure is faulty.")


def runserver():
    r = Example()
    sslContext = ssl.DefaultOpenSSLContextFactory("/etc/ssl/private/ssl-cert-snakeoil.key", "/etc/ssl/certs/ssl-cert-snakeoil.pem") 
    reactor.listenSSL(7080, server.Site(r) , contextFactory = sslContext)
    #reactor.listenTCP(7080, server.Site(r))
    reactor.run() 
    
if __name__ == "__main__":
    runserver()
