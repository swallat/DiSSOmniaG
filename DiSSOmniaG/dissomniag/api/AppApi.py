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
log = logging.getLogger("api.AppApi.py")

def startApp(user, appName, vmName = None):
    root = etree.Element("result")
    errorMsg = etree.SubElement(root, "error")
    success = etree.SubElement(root, "success")
    success.text = "false"
    
    appName = str(appName)
    if vmName != None:
        vmName = str(vmName)
    
    session = dissomniag.Session()
    app = None
    try:
        app = session.query(dissomniag.model.App).filter(dissomniag.model.App.name == appName).one()
    except NoResultFound as e:
        errorMsg.text = ("There is no app with name %s." %appName)
        log.info(etree.tostring(root, pretty_print=True))
        return etree.tostring(root, pretty_print=True)
    except MultipleResultsFound as e:
        app = app[0]

    
    relObj = None
    
    if vmName != None:
        vm = None
        try:
            vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).one()
        except NoResultFound as e:
            errorMsg.text = ("There is no VM with name %s." % vmName)
            log.info(etree.tostring(root, pretty_print=True))
            return etree.tostring(root, pretty_print=True)
        except MultipleResultsFound as e:
            errorMsg.text = ("There are multiple VM's with name %s. DB ERROR." % vmName)
            log.info(etree.tostring(root, pretty_print=True))
            return etree.tostring(root, pretty_print=True)
        
        if not hasattr(vm, "liveCd"):
            errorMsg.text = ("VM has no liveCd!")
            log.info(etree.tostring(root, pretty_print=True))
            return etree.tostring(root, pretty_print=True)
        liveCd = vm.liveCd
        
        try:
            relObj = session.query(dissomniag.model.AppLiveCdRelation).filter(dissomniag.model.AppLiveCdRelation.app == app).filter(dissomniag.model.AppLiveCdRelation.liveCd == liveCd).one()
        except NoResultFound as e:
            errorMsg.text = ("There is no Relation between app %s and vm %s." % (appName, vmName))
            log.info(etree.tostring(root, pretty_print=True))
            return etree.tostring(root, pretty_print=True)
        except MultipleResultsFound as e:
            errorMsg.text = ("There are multiple relations between add %s and vm %s." % (appName, vmName))
            log.info(etree.tostring(root, pretty_print=True))
            return etree.tostring(root, pretty_print=True)
        
    try:
        #print("self.action() = %s" % dissomniag.model.AppActions.getName(self.action()))
        ret = app.operate(user, dissomniag.model.AppActions.START, relObj)
    except Exception as e:
        import traceback
        traceback.print_exc()
        errorMsg.text = ("General Exception %s." % str(e))
        log.info(etree.tostring(root, pretty_print=True))
        return etree.tostring(root, pretty_print=True)
    else:
        success.text = "true"
        log.info(etree.tostring(root, pretty_print=True))
        return etree.tostring(root, pretty_print=True)
    
    

def stopApp(user, appName, vmName = None):
    root = etree.Element("result")
    errorMsg = etree.SubElement(root, "error")
    success = etree.SubElement(root, "success")
    success.text = "false"
    
    appName = str(appName)
    if vmName != None:
        vmName = str(vmName)
    
    session = dissomniag.Session()
    app = None
    try:
        app = session.query(dissomniag.model.App).filter(dissomniag.model.App.name == appName).one()
    except NoResultFound as e:
        errorMsg.text = ("There is no app with name %s." %appName)
        log.info(etree.tostring(root, pretty_print=True))
        return etree.tostring(root, pretty_print=True)
    except MultipleResultsFound as e:
        app = app[0]

    
    relObj = None
    
    if vmName != None:
        vm = None
        try:
            vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).one()
        except NoResultFound as e:
            errorMsg.text = ("There is no VM with name %s." % vmName)
            log.info(etree.tostring(root, pretty_print=True))
            return etree.tostring(root, pretty_print=True)
        except MultipleResultsFound as e:
            errorMsg.text = ("There are multiple VM's with name %s. DB ERROR." % vmName)
            log.info(etree.tostring(root, pretty_print=True))
            return etree.tostring(root, pretty_print=True)
        
        if not hasattr(vm, "liveCd"):
            errorMsg.text = ("VM has no liveCd!")
            log.info(etree.tostring(root, pretty_print=True))
            return etree.tostring(root, pretty_print=True)
        liveCd = vm.liveCd
        
        try:
            relObj = session.query(dissomniag.model.AppLiveCdRelation).filter(dissomniag.model.AppLiveCdRelation.app == app).filter(dissomniag.model.AppLiveCdRelation.liveCd == liveCd).one()
        except NoResultFound as e:
            errorMsg.text = ("There is no Relation between app %s and vm %s." % (appName, vmName))
            log.info(etree.tostring(root, pretty_print=True))
            return etree.tostring(root, pretty_print=True)
        except MultipleResultsFound as e:
            errorMsg.text = ("There are multiple relations between add %s and vm %s." % (appName, vmName))
            log.info(etree.tostring(root, pretty_print=True))
            return etree.tostring(root, pretty_print=True)
        
    try:
        #print("self.action() = %s" % dissomniag.model.AppActions.getName(self.action()))
        ret = app.operate(user, dissomniag.model.AppActions.STOP, relObj)
    except Exception as e:
        import traceback
        traceback.print_exc()
        errorMsg.text = ("General Exception %s." % str(e))
        log.info(etree.tostring(root, pretty_print=True))
        return etree.tostring(root, pretty_print=True)
    else:
        success.text = "true"
        log.info(etree.tostring(root, pretty_print=True))
        return etree.tostring(root, pretty_print=True)

def refreshApp(user, appName, vmName = None):
    root = etree.Element("result")
    errorMsg = etree.SubElement(root, "error")
    success = etree.SubElement(root, "success")
    success.text = "false"
    
    appName = str(appName)
    if vmName != None:
        vmName = str(vmName)
    
    session = dissomniag.Session()
    app = None
    try:
        app = session.query(dissomniag.model.App).filter(dissomniag.model.App.name == appName).one()
    except NoResultFound as e:
        errorMsg.text = ("There is no app with name %s." %appName)
        log.info(etree.tostring(root, pretty_print=True))
        return etree.tostring(root, pretty_print=True)
    except MultipleResultsFound as e:
        app = app[0]

    
    relObj = None
    
    if vmName != None:
        vm = None
        try:
            vm = session.query(dissomniag.model.VM).filter(dissomniag.model.VM.commonName == vmName).one()
        except NoResultFound as e:
            errorMsg.text = ("There is no VM with name %s." % vmName)
            log.info(etree.tostring(root, pretty_print=True))
            return etree.tostring(root, pretty_print=True)
        except MultipleResultsFound as e:
            errorMsg.text = ("There are multiple VM's with name %s. DB ERROR." % vmName)
            log.info(etree.tostring(root, pretty_print=True))
            return etree.tostring(root, pretty_print=True)
        
        if not hasattr(vm, "liveCd"):
            errorMsg.text = ("VM has no liveCd!")
            log.info(etree.tostring(root, pretty_print=True))
            return etree.tostring(root, pretty_print=True)
        liveCd = vm.liveCd
        
        try:
            relObj = session.query(dissomniag.model.AppLiveCdRelation).filter(dissomniag.model.AppLiveCdRelation.app == app).filter(dissomniag.model.AppLiveCdRelation.liveCd == liveCd).one()
        except NoResultFound as e:
            errorMsg.text = ("There is no Relation between app %s and vm %s." % (appName, vmName))
            log.info(etree.tostring(root, pretty_print=True))
            return etree.tostring(root, pretty_print=True)
        except MultipleResultsFound as e:
            errorMsg.text = ("There are multiple relations between add %s and vm %s." % (appName, vmName))
            log.info(etree.tostring(root, pretty_print=True))
            return etree.tostring(root, pretty_print=True)
        
    try:
        #print("self.action() = %s" % dissomniag.model.AppActions.getName(self.action()))
        ret = app.operate(user, dissomniag.model.AppActions.REFRESH_GIT, relObj)
    except Exception as e:
        import traceback
        traceback.print_exc()
        errorMsg.text = ("General Exception %s." % str(e))
        log.info(etree.tostring(root, pretty_print=True))
        return etree.tostring(root, pretty_print=True)
    else:
        success.text = "true"
        log.info(etree.tostring(root, pretty_print=True))
        return etree.tostring(root, pretty_print=True)