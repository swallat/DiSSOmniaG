# -*- coding: utf-8 -*-
"""
Created on 14.07.2011

@author: Sebastian Wallat
"""
import socket
import socketserver
import ssl
import pickle
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCDispatcher, \
                            SimpleXMLRPCRequestHandler
try:
    import fcntl
except ImportError:
    fcntl = None

import dissomniag

#===============================================================================
# The Following Part handeling the XML RPC Authentication,
# and the Basic HTTP Information Extraction is in main Parts extracted from
# http://blogs.blumetech.com/blumetechs-tech-blog/2011/06
#                        /python-xmlrpc-server-with-ssl-and-authentication.html
# Thanks to Michael Raposa <michael@blumetech.com>
#===============================================================================
class VerifyingRequestHandler(SimpleXMLRPCRequestHandler):
    """
    Request Handler that verifies username and password passed to
    XML RPC server in HTTP URL sent by client.
    """
    # this is the method we must override
    def parse_request(self):
        # first, call the original implementation which returns
        # True if all OK so far
        if SimpleXMLRPCRequestHandler.parse_request(self):
            # next we authenticate
            if self.authenticate(self.headers):
                return True
            else:
                # if authentication fails, tell the client
                self.send_error(401, 'Authentication failed')
        return False
   
    def authenticate(self, headers):
        from base64 import b64decode
        #    Confirm that Authorization header is set to Basic
        (basic, _, encoded) = headers.get('Authorization').partition(' ')
        assert basic == 'Basic', 'Only basic authentication supported'
       
        #    Encoded portion of the header is a string
        #    Need to convert to bytestring
        encodedByteString = encoded.encode()
        #    Decode Base64 byte String to a decoded Byte String
        decodedBytes = b64decode(encodedByteString)
        #    Convert from byte string to a regular String
        decodedString = decodedBytes.decode()
        #    Get the username and password from the string
        (username, _, password) = decodedString.partition(':')
        
        #    The Authentication Part:
        if username in config.userPassDict:
            if config.userPassDict[username] == password:
                return True
        return False
 
class SimpleXMLRPCServerTLS(socketserver.ThreadingMixIn, SimpleXMLRPCServer):
    
    def __init__(self, addr, requestHandler=VerifyingRequestHandler,
                 logRequests=True, allow_none=False, encoding=None,\
                    bind_and_activate=True):
        """
        Overriding __init__ method of the SimpleXMLRPCServer

        The method is an exact copy, except the TCPServer __init__
        call, which is rewritten using TLS
        """
        self.logRequests = logRequests

        SimpleXMLRPCDispatcher.__init__(self, allow_none, encoding)
        
        #    Override the normal socket methods with an SSL socket
        socketserver.BaseServer.__init__(self, addr, VerifyingRequestHandler)
        self.socket = ssl.wrap_socket(
            socket.socket(self.address_family, self.socket_type),
            server_side=True,
            keyfile=config.KEYFILE, # User Server Key File
            certfile=config.CERTFILE, # User Server Cert File
            cert_reqs=ssl.CERT_NONE,
            ssl_version=ssl.PROTOCOL_SSLv23,
            )
        if bind_and_activate:
            self.server_bind()
            self.server_activate()

        # [Bug #1222790] If possible, set close-on-exec flag; if a
        # method spawns a subprocess, the subprocess shouldn't have
        # the listening socket open.
        if fcntl is not None and hasattr(fcntl, 'FD_CLOEXEC'):
            flags = fcntl.fcntl(self.fileno(), fcntl.F_GETFD)
            flags |= fcntl.FD_CLOEXEC
            fcntl.fcntl(self.fileno(), fcntl.F_SETFD, flags)

#===============================================================================
# End of Cited part <michael@blumetech.com>
#===============================================================================

def runRPCServer():
    # Create server
    server = SimpleXMLRPCServerTLS(("localhost", 8082), 
                                   requestHandler=SimpleXMLRPCRequestHandler)
    server.register_introspection_functions()

    # Register pow() function; this will use the value of
    # pow.__name__ as the name, which is just 'pow'.
    server.register_function(pow)

    # Register a function under a different name
    def adder_function(x,y):
        print(x+y)
        return x + y
    server.register_function(adder_function, 'add')

    # Register an instance; all the methods of the instance are
    # published as XML-RPC methods (in this case, just 'div').
    class MyFuncs:
        def div(self, x, y):
            return x // y
       
        def enterUID(self, uid):
            print (uid)
            return "Got uid " + uid
        def echo(self, data):
            print(data)
            return data
       
        #    For this test pickle function I am assuming the pickled object is just a list
        def uploadPickle(self, pickleStringBinary):
            #    Get the binary data from the pickled string
            pickleData = pickleStringBinary.data
            #    Unpickle the data into an object
            pickObject = pickle.loads(pickleData)
            #    Print the object to test
            print (pickObject[-1])
            #    Modify the object to test
            pickObject.append("Server got pickled object")
            #    Pickle the object. Protocol=2 is required to support Python v2 clients
            newPickleString = pickle.dumps(pickObject, protocol=2)
            #    Label the string binary and send it back to the XML client
            return xmlrpc.client.Binary(newPickleString)

    server.register_instance(MyFuncs())

    # Run the server's main loop
    print("Starting XML RPC Server")
    server.serve_forever()



if __name__ == '__main__':
    runRPCServer()
