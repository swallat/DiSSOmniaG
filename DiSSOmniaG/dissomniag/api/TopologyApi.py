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
log = logging.getLogger("api.TopologyApi.py")

def getTopologyList(user):
    root = etree.Element("result")
    errorMsg = etree.SubElement(root, "error")
    
    session = dissomniag.Session()
    
    topoList = etree.SubElement(root, "topology-list")
    topos = []
    
    try:
        topos = session.query(dissomniag.model.Topology).all()
    except NoResultFound:
        pass
    else:
        for topo in topos:
            topoList.append(topo.getShortXml(user))
            
    retString = etree.tostring(root, pretty_print = True)
    log.info("Send TopologyList: " + retString)
    return retString

def isTopologyNameValid(user, topoName):
    
    root = etree.Element("result")
    errorMsg = etree.SubElement(root, "error")
    
    topoName = str(topoName)
    
    session = dissomniag.Session()
    isValid = "false"
    try:
        topo = session.query(dissomniag.model.Topology).filter(dissomniag.model.Topology.name == topoName).all()
    except NoResultFound:
        isValid = "true"
    else:
        isValid = "false"
        
    valid = etree.SubElement(root, "isValid")
    valid.text = isValid
    retString = etree.tostring(root, pretty_print = True)
    log.info("Senf isTopologyNameValid: " + retString)
    return retString
        
        
def addTopology(user, topoName):
    root = etree.Element("result")
    errorMsg = etree.SubElement(root, "error")
    topoName = str(topoName)
    added = etree.SubElement(root, "added")
    session = dissomniag.Session()
    found = True
    try:
        topos = session.query(dissomniag.model.Topology).filter(dissomniag.model.Topology.name == topoName).all()
    except NoResultFound:
        found = False
    else:
        if not topos:
            found = False
        else:
            found = True
        
    
    if found:
        errorMsg.text = "Topology already Exists"
        added.text = "false"
        retString = etree.tostring(root, pretty_print = True)
        log.info("Add topology: " + retString)
        return retString
    else:
        topo = dissomniag.model.Topology()
        topo.name = topoName
        topo.users.append(user)
        session.add(topo)
        dissomniag.saveCommit(session)
        added.text = "true"
        retString = etree.tostring(root, pretty_print = True)
        log.info("Add topology: " + retString)
        return retString
    
def deleteTopology(user, topoName):
    root = etree.Element("result")
    errorMsg = etree.SubElement(root, "error")
    deleted = etree.SubElement(root, "deleted")
    topoName = str(topoName)
    session = dissomniag.Session()
    
    log.info("Topology to Delete: " + topoName)
    topos = []
    try:
        topos = session.query(dissomniag.model.Topology).filter(dissomniag.model.Topology.name == topoName).all()
    except NoResultFound:
        errorMsg.text = "There is no Topology with name " + topoName
        deleted.text = "false"
        retString = etree.tostring(root, pretty_print = True)
        log.info("Add topology: " + retString)
        return retString
    
    
    topo = topos[0]
    log.info("Topo: " + topo)
    isDeleted = dissomniag.model.Topology.deleteTopology(user,topo)
    log.finco("is Deleted:" + str(isDeleted))
    if isDeleted:
        deleted.text = "true"
    else:
        deleted.text = "false"
    deleted.text = "false"
    retString = etree.tostring(root, pretty_print = True)
    log.info("Add topology: " + retString)
    return retString
    
        
    
    
    