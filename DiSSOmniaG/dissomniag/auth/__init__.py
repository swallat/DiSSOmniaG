from User import *
import dissomniag.dbAccess as dbAccess

from dissomniag.dbAccess import Session

class LOGIN_SIGN(object):
    VALID_USER = 0
    NO_SUCH_USER = 1
    SECRET_UNVALID = 2
    UNVALID_ACCESS_METHOD = 3

def parseHtpasswdFile():
    #===========================================================================
    # From Tomato:
    #===========================================================================
    lines = [l.rstrip().split(':', 1) for l in file(dissomniag.config.HTPASSWD_FILE).readlines()]
    session = Session()
    for line in lines:
        username = line[0]
        hashedPassword = line[1]
        try:
            dbUser = session.query(User).filter(User.username == username).one()
            
            if username == dissomniag.config.HTPASSWD_ADMIN_USER:
                if dbUser.passwd != hashedPassword:
                    dbUser.updateHtpasswdPassword(hashedPassword)
                    session.flush()
                
            if dbUser.isHtpasswd and dbUser.passwd != hashedPassword:
                dbUser.updateHtpasswdPassword(hashedPassword)
                
        except NoResultFound:
            if username == dissomniag.config.HTPASSWD_ADMIN_USER:
                newUser = User(username, password = hashedPassword, publicKey = None,
                               isAdmin = True, loginRPC = True, loginSSH = True,
                               loginManhole = True, isHtpasswd = True)
            else: 
                newUser = User(username, password = hashedPassword, publicKey = None,
                               isAdmin = False, loginRPC = True, loginSSH = True,
                               loginManhole = False, isHtpasswd = True)
            session.add(newUser)
            session.flush()

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
    if not passwd and not key:
        print("Both not")
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
    if user.checkPassword(passwd) == True:
        return LOGIN_SIGN.VALID_USER, user
    else:
        return LOGIN_SIGN.SECRET_UNVALID, None
