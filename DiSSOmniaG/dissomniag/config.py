# -*- coding: utf-8 -*-
# DiSSOmniaG (Distributed Simulation Service wit OMNeT++ and Git)
# Copyright (C) 2011, 2012 Sebastian Wallat, University Duisburg-Essen
# 
# Based on an idea of:
# Sebastian Wallat <sebastian.wallat@uni-due.de, University Duisburg-Essen
# Hakim Adhari <hakim.adhari@iem.uni-due.de>, University Duisburg-Essen
# Martin Becke <martin.becke@iem.uni-due.de>, University Duisburg-Essen
#
# DiSSOmniaG is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DiSSOmniaG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DiSSOmniaG. If not, see <http://www.gnu.org/licenses/>
from abc import ABCMeta, abstractmethod
import pwd, grp, os
import ConfigParser

config = ConfigParser.SafeConfigParser()
config.read(["/etc/dissomniag/dissomniag.conf","dissomniag.conf"])


    
class ParseSection(object):
    __metaclass__ = ABCMeta
    
    def __init__(self, config, sectionName):
        self.config = config
        self.sectionName = sectionName
    
    @abstractmethod
    def parse(self):
        pass
    
    def bool(self, string):
        if string in ["False", "false", "f", "F", "0"]:
            return False
        else:
            return True
    
    def parseOption(self, section, option, defaultValue):
        """
        Doc
        """ 
        if self.config.has_option(section, option):
            return self.config.get(section, option)
        else:
            return defaultValue
        
class dissomniag(ParseSection):
    
    def parse(self):
        self.isCentral = self.bool(self.parseOption(self.sectionName, "isCentral", "True"))
        self.centralIp = self.parseOption(self.sectionName, "CentralSystemIP", "None")
        self.configDir = self.parseOption(self.sectionName, "configDir", "/etc/dissomniag/")
        self.execDir = self.parseOption(self.sectionName, "execDir", "/usr/share/dissomniag/")
        self.rsaKeyPrivate = self.parseOption(self.sectionName, "rsaKey", "ssh_key")
        self.rsaKeyPublic = self.parseOption(self.sectionName, "rsaKeyPub", "ssh_key.pub")
        self.utilityFolder = self.parseOption(self.sectionName, "utilityFolder", "/var/lib/dissomniag/")
        self.serverFolder = os.path.join(self.utilityFolder, "server/")
        self.vmsFolder = os.path.join(self.serverFolder, "vms/")
        self.liveCdPatternDirectory = self.parseOption(self.sectionName, "liveCdPatternDirectory", "pattern")
        self.patternLockFile = self.parseOption(self.sectionName, "patternLockFile", "pattern")
        self.user = self.parseOption(self.sectionName, "user", "root")
        self.group = self.parseOption(self.sectionName, "group", "root")
        self.userId = pwd.getpwnam(self.user).pw_uid
        self.groupId = grp.getgrnam(self.group).gr_gid
        self.staticFolder = os.path.join(self.execDir, "static/")
        self.staticLiveFolder = os.path.join(self.staticFolder, "live/")
        self.pidFile = "/var/run/dissomniag.pid"
        self.maintainanceInterface = self.parseOption(self.sectionName, "maintainanceInterface", "None")
        return self
    
dissomniag = dissomniag(config, "dissomniag").parse()

class server(ParseSection):
    
    def parse(self):
        self.rpcPort = int(self.parseOption(self.sectionName, "rpcServerPort", "8008"))
        self.sshPort = int(self.parseOption(self.sectionName, "sshServerPort", "8009"))
        self.useManhole = self.bool(self.parseOption(self.sectionName, "useManhole", "False"))
        self.manholePort = int(self.parseOption(self.sectionName, "manholeServerPort", "8010"))
        
        return self
    
server = server(config, "server").parse()


class ssl(ParseSection):
    def parse(self):
        if not self.config.has_section(self.sectionName):
            self.SSL = False
        else:
            self.SSL = True
        self.privateKey = self.parseOption(self.sectionName, "privateKeyFile", "privatekey.pem")
        self.caKey = self.parseOption(self.sectionName, "caKeyFile", "cert.pem")
        return self
    
ssl = ssl(config, "SSL").parse()

class db(ParseSection):
    
    def parse(self):
        self.maintainance = self.bool(self.parseOption(self.sectionName, "Maintainance", "False"))
        self.db_file = self.parseOption(self.sectionName, "db_file", os.path.join(dissomniag.execDir, "dissomniag.db"))
        self.db_string = str("%s:///%s" % ("sqlite", self.db_file))
        self.migrate_repository = os.path.join(dissomniag.execDir, "dissomniag/migrations/")
        return self
    
db = db(config, "DB").parse()

class htpasswd(ParseSection):
    
    def parse(self):
        self.htpasswd_file = self.parseOption(self.sectionName, "htpasswd_file", "htpasswd")
        self.adminUser = self.parseOption(self.sectionName, "adminUser", "admin")
        return self

htpasswd = htpasswd(config, "htpasswd").parse()

class log(ParseSection):
    
    def parse(self):
        self.logDir = self.parseOption(self.sectionName, "logDir", os.path.join(os.getcwd(), "log/"))
        self.debugFilename = self.parseOption(self.sectionName, "debugFilename", "dissomniag_DEBUG.log")
        self.warningFilename = self.parseOption(self.sectionName, "warningFilename", "dissomniag_WARNING.log")
        self.toStdOut = self.bool(self.parseOption(self.sectionName, "toStdOut", "True"))
        return self
        
log = log(config, "log").parse()

class dispatcher(ParseSection):
    
    def parse(self):
        self.revertBeforeCancel = self.bool(self.parseOption(self.sectionName, "reverBeforeCancel", "True"))
        return self
    
dispatcher = dispatcher(config, "dispatcher").parse()

class hostConfig(ParseSection):
    
    def parse(self):
        self.hostFolder = self.parseOption(self.sectionName, "hostFolder", "/var/lib/dissomniag/host/")
        self.vmSubdirectory = self.parseOption(self.sectionName, "vmSubDirectory", "vms/")
        return self
    
hostConfig = hostConfig(config, "hostConfig").parse()

class clientConfig(ParseSection):
    
    def parse(self):
        self.rpcServerPort = int(self.parseOption(self.sectionName, "rpcServerPort", "8008"))
        return self

clientConfig = clientConfig(config, "clientConfig").parse()

class gitConfig(ParseSection):
    
    def parse(self):
        self.pathToGitRepositories = self.parseOption(self.sectionName, "gitRepoFolder", "/srv/gitosis/repositories/")
        self.pathToLocalUtilFolder = self.parseOption(self.sectionName, "gitUtilFolder", os.path.join(dissomniag.utilityFolder, "gitosis"))
        self.pathToSkeleton = self.parseOption(self.sectionName, "gitSkeletonFolder", os.path.join(dissomniag.utilityFolder, "git-skeleton"))
        self.pathToStaticSkeleton = os.path.join(dissomniag.staticFolder, "git-skeleton")
        self.pathToKeyFolder = os.path.join(self.pathToLocalUtilFolder, "keydir")
        self.pathToConfigFile = os.path.join(self.pathToLocalUtilFolder, "gitosis.conf")
        self.gitUser = self.parseOption(self.sectionName, "gitUser", "gitosis")
        self.gitGroup = self.parseOption(self.sectionName, "gitGroup", "gitosis")
        self.gitosisHost = self.parseOption(self.sectionName, "gitosisHost", "localhost")
        self.scriptSyncFolder = self.parseOption(self.sectionName, "gitRepoFolder", "/srv/gitosis/sync/")
        return self
    
git = gitConfig(config, "gitConfig").parse()
