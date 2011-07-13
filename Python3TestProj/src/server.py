# -*- coding: utf-8 -*-
"""
Created on 12.07.2011

@author: Sebastian Wallat
"""
import socket
import socketserver
import ssl
import pickle
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCDispatcher, SimpleXMLRPCRequestHandler
try:
    import fcntl
except ImportError:
    fcntl = None

#    Easiest way to create the key file pair was to use OpenSSL -- http://openssl.org/ Windows binaries are available
#    You can create a self-signed certificate easily "openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout privatekey.pem"
#    for more information --  http://docs.python.org/library/ssl.html#ssl-certificates
#KEYFILE='/etc/ssl/private/ssl-cert-snakeoil.key'    # Replace with your PEM formatted key file
#CERTFILE='/etc/ssl/certs/ssl-cert-snakeoil.pem'  # Replace with your PEM formatted certificate file
KEYFILE='privatekey.pem'
CERTFILE='cert.pem'

userPassDict = {"mraposa":"test123",
                "jsmith":"hellow"}


class VerifyingRequestHandler(SimpleXMLRPCRequestHandler):
    '''
    Request Handler that verifies username and password passed to
    XML RPC server in HTTP URL sent by client.
    '''
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
        #    Check that username and password match internal global dictionary
        if username in userPassDict:
            if userPassDict[username] == password:
                return True
        return False
 
class SimpleXMLRPCServerTLS(socketserver.ThreadingMixIn, SimpleXMLRPCServer):
    
    def __init__(self, addr, requestHandler=VerifyingRequestHandler,
                 logRequests=True, allow_none=False, encoding=None, bind_and_activate=True):
        """Overriding __init__ method of the SimpleXMLRPCServer

        The method is an exact copy, except the TCPServer __init__
        call, which is rewritten using TLS
        """
        self.logRequests = logRequests

        SimpleXMLRPCDispatcher.__init__(self, allow_none, encoding)

        """This is the modified part. Original code was:

            socketserver.TCPServer.__init__(self, addr, requestHandler, bind_and_activate)

        which executed:

            def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
                BaseServer.__init__(self, server_address, RequestHandlerClass)
                self.socket = socket.socket(self.address_family,
                                            self.socket_type)
                if bind_and_activate:
                    self.server_bind()
                    self.server_activate()

        """
        
        #    Override the normal socket methods with an SSL socket
        socketserver.BaseServer.__init__(self, addr, VerifyingRequestHandler)
        self.socket = ssl.wrap_socket(
            socket.socket(self.address_family, self.socket_type),
            server_side=True,
            keyfile=KEYFILE,
            certfile=CERTFILE,
            cert_reqs=ssl.CERT_NONE,
            ssl_version=ssl.PROTOCOL_TLSv1,
            )
        if bind_and_activate:
            self.server_bind()
            self.server_activate()

        """End of modified part"""

        # [Bug #1222790] If possible, set close-on-exec flag; if a
        # method spawns a subprocess, the subprocess shouldn't have
        # the listening socket open.
        if fcntl is not None and hasattr(fcntl, 'FD_CLOEXEC'):
            flags = fcntl.fcntl(self.fileno(), fcntl.F_GETFD)
            flags |= fcntl.FD_CLOEXEC
            fcntl.fcntl(self.fileno(), fcntl.F_SETFD, flags)


       
        

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

def executeRpcServer():
    # Create server
    server = SimpleXMLRPCServerTLS(("10.11.0.5", 8082), requestHandler=RequestHandler)
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
    executeRpcServer()