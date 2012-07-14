'''
Created on 14.07.2012

@author: Sebastian Wallat
'''
from lxml import etree
import datetime
import dissomniag.auth.User
import dissomniag.model.Host
import dissomniag.config
import os
import logging
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
log = logging.getLogger("api.Hosts.py")

def getHostList(user):
    root = etree.Element("hosts")
    dissomniagPublicSshKey = etree.SubElement(root, "public-ssh-key")
    
    
    text = ""
    with open(os.path.abspath(dissomniag.config.dissomniag.rsaKeyPublic), "r") as f:
        text = f.read();
    
    dissomniagPublicSshKey.text = text
    hostList = etree.SubElement(root, "host-list")
    
    session = dissomniag.Session()
    
    try:
        hosts = session.query(dissomniag.model.Host).all()
    except NoResultFound:
        return etree.tostring(root, pretty_print = True)
    else:
        for host in hosts:
            hostList.append(host.getUserXml())
            
        return etree.tostring(root, pretty_print = True)