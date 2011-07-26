# -*- coding: utf-8 -*-
"""
Created on 19.07.2011

@author: Sebastian Wallat
"""
import logging

log = logging.getLogger("config")

rpcServerPort = 8008
sshServerPort = 8009
manholeServerPort = 8010


#    Easiest way to create the key file pair was to use OpenSSL -- http://openssl.org/ Windows binaries are available
#    You can create a self-signed certificate easily "openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout privatekey.pem"
#    for more information --  http://docs.python.org/library/ssl.html#ssl-certificates
#SSL_PrivKey='/etc/ssl/private/ssl-cert-snakeoil.key'    # Replace with your PEM formatted key file
#SSL_CaKey='/etc/ssl/certs/ssl-cert-snakeoil.pem'  # Replace with your PEM formatted certificate file
SSL = True
SSL_PrivKey = "privatekey.pem"
SSL_CaKey = "cert.pem"

MAINTANANCE = False
DB_FILE = "dissomniag.db"
DB_STRING = "%s:///%s" % ("sqlite", DB_FILE)
MIGRATE_REPOSITORY = "dissomniag/migrations"

HTPASSWD_FILE = "htpasswd"
HTPASSWD_ADMIN_USER = "admin"

LOG_DIR = "log/"
LOG_DEBUG_FILENAME = "dissomniag_DEBUG.log"
LOG_WARNING_FILENAME = "dissomniag_WARNING.log"

