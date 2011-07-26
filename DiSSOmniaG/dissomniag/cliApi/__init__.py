import logging

log = logging.getLogger("cliApi.__init__")

def listUser(*args):
    import ManageUsers
    ManageUsers.listUser().call(*args)

def listKeys(*args):
    import ManageUsers
    ManageUsers.listKeys().call(*args)

def addUser(*args):
    import ManageUsers
    ManageUsers.addUser().call(*args)
    
def addKey(*args):
    import ManageUsers
    ManageUsers.addKey().call(*args)

def modUser(*args):
    import ManageUsers
    ManageUsers.modUser().call(*args)

def delUser(*args):
    import ManageUsers
    ManageUsers.delUser().call(*args)
    
def delKey(*args):
    import ManageUsers
    ManageUsers.delKey().call(*args)
    
def passwd(*args):
    import ManageUsers
    ManageUsers.passwd().call(*args)

def whoami(*args):
    import ManageUsers
    ManageUsers.whoami().call(*args)    
