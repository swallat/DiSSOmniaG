from User import *
import dissomniag.dbAccess as dbAccess

from dissomniag.dbAccess import Session

class LOGIN_SIGN(object):
    VALID_USER = 0
    NO_SUCH_USER = 1
    SECRET_UNVALID = 2
    UNVALID_ACCESS_METHOD = 3

#===============================================================================
# users = []
# 
# def login(username, password):
#    for user in users:
#        if user.username == username and user.password == password:
#            return user
#    return None  
# 
# def getUserAndKeys(username):
#    session = Session()
#    try:
#        user = session.query(User).filter(User.username == username).one()
#        return user, user.getKeys()
#    except (NoResultFound, MultipleResultsFound):
#        return None, None
# 
# def getUser(username):
#    session = Session()
#    try:
#        return session.query(User).filter(User.username == username).one()
#    except (NoResultFound, MultipleResultsFound):
#        return None
#        
# 
# def getUserObjects():
#    return users
# 
# def addUser(user):
#    users.append(user)
#===============================================================================
    

def loginRPC(username, passwd = None):
    if not passwd:
        return LOGIN_SIGN.SECRET_UNVALID, None
    
    session = Session()
    try:
        user = session.query(User).filter(User.username == username).one()
    except (NoResultFound, MultipleResultsFound):
        return LOGIN_SIGN.NO_SUCH_USER, None
    if not user.loginRPC:
        return LOGIN_SIGN.UNVALID_ACCESS_METHOD, None
    return _loginViaPasswd(user, passwd)
        
    
        
def loginSSH(username, passwd = None, key = None):
    if not passwd and not key:
        return LOGIN_SIGN.SECRET_UNVALID, None
    session = Session()
    try:
        user = session.query(User).filter(User.username == username).one()
    except (NoResultFound, MultipleResultsFound):
        return LOGIN_SIGN.NO_SUCH_USER, None
    if not user.loginSSH:
        return LOGIN_SIGN.UNVALID_ACCESS_METHOD, None
    """If Public Key was provided"""
    if not passwd:
        return _loginViaPubKey(user, key)
    else:
        return _loginViaPasswd(user, passwd)
            
def loginManhole(username, passwd = None, key = None):
    print("In LoginManhole")
    if not passwd and not key:
        return LOGIN_SIGN.SECRET_UNVALID, None
    session = Session()
    try:
        user = session.query(User).filter(User.username == username).one()
    except (NoResultFound, MultipleResultsFound):
        return LOGIN_SIGN.NO_SUCH_USER, None
    """Check that only admins have access to the Manhole backend"""
    if not user.isAdmin and not user.loginManhole:
        return LOGIN_SIGN.UNVALID_ACCESS_METHOD, None
    """If Public Key was provided"""
    if not passwd:
        return _loginViaPubKey(user, key)
    else:
        return _loginViaPasswd(user, passwd)
    
def _loginViaPubKey(user, key):
    for userKey in user.publicKeys:
        if keys.Key.fromString(userKey.publicKey).blob() == key:
            return LOGIN_SIGN.VALID_USER, user
    return LOGIN_SIGN.SECRET_UNVALID, None
    

def _loginViaPasswd(user, passwd):
    if user.checkPassword(passwd):
        return LOGIN_SIGN.VALID_USER, user
    else:
        return LOGIN_SIGN.SECRET_UNVALID, None
