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
from lxml import etree as ElementTree
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import dissomniag
import logging
log = logging.getLogger("api.Update.py")

def update(user, infoXml):
    
    xml = ElementTree.XML(infoXml)
    
    session = dissomniag.Session()
    
    uuidElem = xml.find("uuid")
    uuid = None
    if uuidElem != None:
       uuid = str(uuidElem.text)
    
    try:
        vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.uuid == uuid).one()
    except (NoResultFound, MultipleResultsFound) as e:
        log.info("No Vm with UUID %s for user %s" % (uuid, str(user)))
    else:
        try:
            vm.authUser(user)
        except dissomniag.UnauthorizedFunctionCall as e:
            log.info("Unauthorized RPC Call for UUID %s with user %s" % (uuid, str(user)))
            return False
        else:
            ret = vm.recvUpdateLiveClient(user, xml)
            """
            Push app info
            """
            try:
                vm.liveCd.createAddAllCurrentAppsOnRemoteJob(user, vm.liveCd)
            except Exception as e:
                import traceback
                traceback.print_exc()
                log.error("Cannot push App info to LiveCd! %s" % str(e))
            return ret
            
        
def updateAppInfo(user, appInfoXml):
    
    xml = ElementTree.XML(appInfoXml)
    
    uuidElem = xml.find("uuid")
    uuid = None
    
    if uuidElem != None:
        uuid = str(uuidElem.text)
       
    appNameElem = xml.find("appName")
    appName = None
    
    if appNameElem != None:
        appName = str(appNameElem.text)
        
    if uuidElem == None or appName == None:
        log.info("updateAppInfo: UUID or appName not provided!")
        
    stateElem = xml.find("state")
    state = None
    if stateElem != None:
        try:
            state = int(stateElem.text)
        except Exception as e:
            log.info("updateAppInfo: Cannot parse state.")
            return False
    else:
        log.info("updateAppInfo: No state provided.")
        return False
    
    logElem = xml.find("log")
    myLog = None
    if logElem != None:
        myLog = str(logElem.text)
    else:
        log.info("updateAppInfo: No log provided.")
        myLog = ""
    
    session = dissomniag.Session()
    
    try:
        vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.uuid == uuid).one()
    except (NoResultFound, MultipleResultsFound) as e:
        log.info("No Vm with UUID %s for user %s" % (uuid, str(user)))
        return False
    
    if not hasattr(vm, "liveCd"):
        log.info("VM has no live Cd object!.")
        return False
    
    liveCd = vm.liveCd
    
    try:
        app = session.query(dissomniag.model.App).filter(dissomniag.model.App.name == appName).one()
    except (NoResultFound, MultipleResultsFound) as e:
        log.info("No App with name %s for user %s" % (appName, str(user)))
        return False
    
    try: 
        relObj = session.query(dissomniag.model.AppLiveCdRelation).filter(dissomniag.model.AppLiveCdRelation.liveCd == liveCd).filter(dissomniag.model.AppLiveCdRelation.app == app).one()
    except (NoResultFound, MultipleResultsFound) as e:
        log.info("No App LiveCd relation found for VM %s and app %s for user %s" % (uuid, appName, str(user)))
        return False
    else:
        try:
            relObj.updateInfo(user, state, myLog)
            dissomniag.saveCommit(session)
            return True
        except Exception as e:
            return False    
    