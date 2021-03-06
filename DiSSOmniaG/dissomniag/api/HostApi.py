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
            
    retString = etree.tostring(root, pretty_print = True)
    log.info("Send hostList: " + retString)
    return retString

def checkHost(user, hostName):
    root = etree.Element("result")
    errorMsg = etree.SubElement(root, "error")
    
    if not user.isAdmin:
        errorMsg.text("User is no admin user")
        return etree.tostring(root, pretty_print = True)
    
    session = dissomniag.Session()
    host = None
    try:
        host = session.query(dissomniag.model.Host).filter(dissomniag.model.Host.commonName == str(hostName)).one()
    except (NoResultFound, MultipleResultsFound):
        errorMsg.text("The Host you have entered is not known or valid.")
        return etree.tostring(root, pretty_print = True)
    
    host.checkFull(user)
    return etree.tostring(root, pretty_print = True)
    