'''
Created on 14.07.2012

@author: Sebastian Wallat
'''
from lxml import etree
import dissomniag.auth.User
import dissomniag.model.Host
import dissomniag.config
import os
import logging
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
log = logging.getLogger("api.Hosts.py")

def getHostList(user):
    
    root = etree.Element("result")
    errorMsg = etree.SubElement(root, "error")
    
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
        pass
    else:
        for host in hosts:
            hostList.append(host.getUserXml())
    return etree.tostring(root, pretty_print = True)
            
    retString = etree.tostring(root, pretty_print = True)
    log.info("Send hostList: " + retString)
    return retString