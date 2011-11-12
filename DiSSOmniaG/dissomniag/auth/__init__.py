import logging

log = logging.getLogger("auth.__init__")

import dissomniag.dbAccess
from dissomniag.dbAccess import Session

from User import * 

def parseHtpasswdFile():
    """
    Test parseHtPasswdFile()
    """
    #===========================================================================
    # From Tomato:
    #===========================================================================
    lines = [l.rstrip().split(':', 1) for l in file(dissomniag.config.htpasswd.htpasswd_file).readlines()]
    session = Session()
    usernamesInHtpasswd = []
    for line in lines:
        username = line[0]
        usernamesInHtpasswd.append(username)
        hashedPassword = line[1]
        try:
            dbUser = session.query(User).filter(User.username == username).one()
            
            if username == dissomniag.config.htpasswd.adminUser:
                if dbUser.passwd != hashedPassword:
                    dbUser.updateHtpasswdPassword(hashedPassword)
                    dissomniag.saveCommit(session)
                
            if dbUser.isHtpasswd and dbUser.passwd != hashedPassword:
                dbUser.updateHtpasswdPassword(hashedPassword)
                
        except NoResultFound:
            if username == dissomniag.config.htpasswd.adminUser:
                newUser = User.addUser(username, password = hashedPassword, publicKey = None,
                               isAdmin = True, loginRPC = True, loginSSH = True,
                               loginManhole = True, isHtpasswd = True)
            else: 
                newUser = User.addUser(username, password = hashedPassword, publicKey = None,
                               isAdmin = False, loginRPC = True, loginSSH = True,
                               loginManhole = False, isHtpasswd = True)
            session.add(newUser)
            dissomniag.saveCommit(session)
    try:
        for user in session.query(User).filter(User.isHtpasswd == True).all():
            if user.username not in usernamesInHtpasswd:
                session.delete(user)
    except NoResultFound:
        pass
    dissomniag.saveCommit(session)
    dissomniag.saveFlush(session)

def refreshHtpasswdFile():
    #raise NotImplementedError()
    pass
