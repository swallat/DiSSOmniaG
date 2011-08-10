# -*- coding: utf-8 -*-
"""
Created on 27.07.2011

@author: Sebastian Wallat
"""
import logging
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import dissomniag

log = logging.getLogger("taskManagaer.context")

class Context(object):
    """
    classdocs
    """
    
    def parse(self):
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
        
            
            
        
