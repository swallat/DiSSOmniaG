# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag
from dissomniag.model import *

class ControlSystem(AbstractNode):
    __mapper_args__ = {'polymorphic_identity': 'ControlSystem'}
    
    """
    classdocs
    """
    
    


        
