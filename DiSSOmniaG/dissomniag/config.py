# -*- coding: utf-8 -*-
"""
Created on 19.07.2011

@author: Sebastian Wallat
"""
from abc import ABCMeta, abstractmethod

import ConfigParser

config = ConfigParser.SafeConfigParser()
config.read(["dissomniag.conf"])


    
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

class server(ParseSection):
    
    def parse(self):
        self.rpcPort = int(self.parseOption(self.sectionName, "rpcServerPort", "8008"))
        self.sshPort = int(self.parseOption(self.sectionName, "sshServerPort", "8009"))
        self.manholePort = int(self.parseOption(self.sectionName, "manholeServerPort", "8010"))
        return self
    
server = server(config, "server").parse()


class ssl(ParseSection):
    #    Easiest way to create the key file pair was to use OpenSSL -- http://openssl.org/ Windows binaries are available
    #    You can create a self-signed certificate easily "openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout privatekey.pem"
    #    for more information --  http://docs.python.org/library/ssl.html#ssl-certificates
    #SSL_PrivKey='/etc/ssl/private/ssl-cert-snakeoil.key'    # Replace with your PEM formatted key file
    #SSL_CaKey='/etc/ssl/certs/ssl-cert-snakeoil.pem'  # Replace with your PEM formatted certificate file
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
        self.db_file = self.parseOption(self.sectionName, "db_file", "dissomniag.db")
        self.db_string = "%s:///%s" % ("sqlite", self.db_file)
        self.migrate_repository = "dissomniag/migrations"
        return self
    
db = db(config, "DB").parse()

class htpasswd(ParseSection):
    
    def parse(self):
        self.htpasswd_file = self.parseOption(self.sectionName, "htpasswd_file", "htpasswd")
        self.adminUser = self.parseOption(self.sectionName, "adminUser", "admin")
        return self

htpasswd = htpasswd(config, "HTPASSWD").parse()

class log(ParseSection):
    
    def parse(self):
        self.logDir = self.parseOption(self.sectionName, "logDir", "log/")
        self.debugFilename = self.parseOption(self.sectionName, "debugFilename", "dissomniag_DEBUG.log")
        self.warningFilename = self.parseOption(self.sectionName, "warningFilename", "dissomniag_WARNING.log")
        return self
        
log = log(config, "LOG").parse()

