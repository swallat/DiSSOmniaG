# -*- coding: utf-8 -*-
"""
Created on 11.11.2011

@author: Sebastian Wallat
"""
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
            #try:
            #vm.liveCd.addAllCurrentAppsOnRemote(user)
            #except Exception as e:
            #    log.error("Cannot push App info to LiveCd! %s" % str(e))
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
        appName = str(appName.text)
        
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
    log = None
    if log != None:
        log = str(logElem.text)
    else:
        log.info("updateAppInfo: No log provided.")
        return False
    
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
    
    