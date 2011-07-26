import logging

log = logging.getLogger("auth.__init__")

import dissomniag.dbAccess as dbAccess
from dissomniag.dbAccess import Session

from User import * 

def parseHtpasswdFile():
    #===========================================================================
    # From Tomato:
    #===========================================================================
    lines = [l.rstrip().split(':', 1) for l in file(dissomniag.config.HTPASSWD_FILE).readlines()]
    session = Session()
    usernamesInHtpasswd = []
    for line in lines:
        username = line[0]
        usernamesInHtpasswd.append(username)
        hashedPassword = line[1]
        try:
            dbUser = session.query(User).filter(User.username == username).one()
            
            if username == dissomniag.config.HTPASSWD_ADMIN_USER:
                if dbUser.passwd != hashedPassword:
                    dbUser.updateHtpasswdPassword(hashedPassword)
                    session.commit()
                
            if dbUser.isHtpasswd and dbUser.passwd != hashedPassword:
                dbUser.updateHtpasswdPassword(hashedPassword)
                
        except NoResultFound:
            if username == dissomniag.config.HTPASSWD_ADMIN_USER:
                newUser = User.addUser(username, password = hashedPassword, publicKey = None,
                               isAdmin = True, loginRPC = True, loginSSH = True,
                               loginManhole = True, isHtpasswd = True)
            else: 
                newUser = User.addUser(username, password = hashedPassword, publicKey = None,
                               isAdmin = False, loginRPC = True, loginSSH = True,
                               loginManhole = False, isHtpasswd = True)
            session.add(newUser)
            session.commit()
    try:
        for user in session.query(User).filter(User.isHtpasswd == True).all():
            if user.username not in usernamesInHtpasswd:
                session.delete(user)
    except NoResultFound:
        pass
    session.commit()
    session.flush()

def refreshHtpasswdFile():
    pass
