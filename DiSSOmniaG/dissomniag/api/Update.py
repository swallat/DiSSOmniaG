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
            return vm.recvUpdateLiveClient(user, xml)