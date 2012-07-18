'''
Created on 12.07.2012

@author: Sebastian Wallat
'''
import datetime
import dissomniag.auth.User
import logging
log = logging.getLogger("api.CheckConnection.py")

def testConnection(user):
    return "Hello " + user.username + " " + datetime.datetime.now().__str__()

def isAdminUser(user):
    return user.isAdmin
    