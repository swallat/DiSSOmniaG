# -*- coding: utf-8 -*-
"""
Created on 14.07.2011

@author: Sebastian Wallat
"""

def xmlRpcClient(pickableObject):
    '''
    Connects to RPC server for HTTPs. This is simply a demo function to showcase
    what can be done.
    @param pickleString:
    '''

    import pickle
    import xmlrpc
    from xmlrpc import client

    #    Connects to server
    #    Can only connect over HTTPS with HTTPS server
    #    Server supports passing username and password
    s = xmlrpc.client.ServerProxy('https://mraposa:test123@localhost:8082')
    #     Runs various functions on the remote server
    #print(s.pow(2,3))  # Returns 2**3 = 8
    print(s.add(2,3))  # Returns 5
    print(s.div(5,2))  # Returns 5//2 = 2
   
    #    Uploads a pickable object to XML RPC server.
    #    First pickles the object into a string -- Uses protocol=2 to enforce Python 2 vs 3 compatibility
    #    Then send the string as a binary over XMLRPC. Sending a string results in conversion errors from
    #    Python 2 to 3
    #    Server returns a binary pickled object back
    pickleString = pickle.dumps(pickableObject, protocol=2)
    newPickleStringBinary = s.uploadPickle(xmlrpc.client.Binary(pickleString))
   
    #    gets Binary data from returned results
    newPickleString = newPickleStringBinary.data
    #    Load the new pickle data into a new object
    newPickleObject = pickle.loads(newPickleString)
    print ("Client got object: " + newPickleObject[-1])

    # Print list of available methods
    print(s.system.listMethods())

if __name__ == '__main__':
    pass