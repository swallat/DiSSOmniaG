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
    
def jobs(*args):
    import ManageJobs
    ManageJobs.CliJobs().call(*args)

def stopJob(*args):
    import ManageJobs
    ManageJobs.stopJob().call(*args)
    
def addDummyJob(*args):
    import ManageJobs
    ManageJobs.addDummyJob().call(*args)
    
def listHosts(*args):
    import ManageHosts
    ManageHosts.listHosts().call(*args)
    
def addHost(*args):
    import ManageHosts
    ManageHosts.addHost().call(*args)

def testSubprocess(terminal, user, *args):
    import sys
    sys.stdout = terminal
    sys.stderr = terminal
    import subprocess
    
    terminal.write("One line at a time:")
    terminal.nextLine()
    
    proc = subprocess.Popen("python repeater.py",
                            shell = True,
                            stdin = subprocess.PIPE,
                            stdout = subprocess.PIPE,
                            )
    for i in range(5):
        proc.stdin.write(" % d\n" % i)
        output = proc.stdout.readline()
        terminal.write(str(output.rstrip()))
        terminal.nextLine()
    remainder = proc.communicate()[0]
    terminal.write(str(remainder))
    terminal.nextLine()
