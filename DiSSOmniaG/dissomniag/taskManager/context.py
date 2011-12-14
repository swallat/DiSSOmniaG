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
import logging
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import dissomniag

log = logging.getLogger("taskManagaer.context")

class Context(object):
    """
    classdocs
    """
    
    def parse(self, user):
        self.user = user
        session = dissomniag.Session()
        allObjects = dir(self)
        for obj in allObjects:
            if obj.startswith("_"):
                continue
            attribute = getattr(self, obj)
            if not type(attribute) == dict:
                continue
            if "class" not in attribute or "id" not in attribute:
                continue
            found = False
            try:
                newObj = session.query(attribute['class']).filter(attribute['class'].id == attribute['id']).one()
                found = True
            except NoResultFound:
                found = False
            except MultipleResultsFound:
                allObj = session.query(attribute['class']).filter(attribute['class'].id == attribute['id']).all()
                newObj = allObj[0]
                found = True
            
            if found == True:
                setattr(self, obj, newObj)
            
    def add(self, obj, name = None):
        cls = obj.__class__
        if not hasattr(obj, "id"):
            raise AttributeError("The Object has no Attribute named ID.")
        
        id = obj.id
        dict = {"class": cls, "id": id}
        if name == None:
            name = obj.__class__.__name__
        
        try:
            getattr(self, name)
        except AttributeError:
            pass
        else:
            raise AttributeError("The object with the Name %s already exists in this context." % name)
        setattr(self, name, dict)
    
    def addWhileRunning(self, obj, name = None):
        
        if name == None:
            setattr(self, obj.__class__.__name__, obj)
        else:
            setattr(self, name, obj)
        
            
            
        
