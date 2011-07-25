
def listUsers(*args):
    import ManageUsers
    ManageUsers.listUsers().call(*args)

def addUser(*args):
    import ManageUsers
    ManageUsers.addUser().call(*args)
    
def addKey(*args):
    import ManageUsers
    ManageUsers.addKey().call(*args)

def delUser(*args):
    import ManageUsers
    ManageUsers.delUser().call(*args)
    
def delKey(*args):
    import ManageUsers
    ManageUsers.delKey().call(*args)
    
def passwd(*args):
    import ManageUsers
    ManageUsers.passwd().call(*args)
    
