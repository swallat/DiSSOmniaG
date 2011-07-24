
import dissomniag.dbAccess as dbAccess
from dissomniag.dbAccess import Session

from User import * 

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
                    session.commit()
                
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
            session.commit()
