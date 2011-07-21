

class User(object):
    """
    classdocs
    """


    def __init__(self, username, password, publicKey = None):
        """
        Constructor
        """
        self.username = username
        self.password = password
        self.publicKeys = []
        self.addKey(publicKey)
        
    def addKey(self, publicKey):
        self.publicKeys.append(publicKey)
        
    def getKeys(self):
        return self.publicKeys

users = []

def login(username, password):
    for user in users:
        if user.username == username and user.password == password:
            return user
    return None  

def getUser(username):
    for user in users:
        if user.username == username:
            return user
    return None

def getUserObjects():
    return users

def addUser(user):
    users.append(user)
