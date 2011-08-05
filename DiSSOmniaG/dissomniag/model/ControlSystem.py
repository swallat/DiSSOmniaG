# -*- coding: utf-8 -*-
"""
Created on 05.08.2011

@author: Sebastian Wallat
"""
import sqlalchemy as sa
import sqlalchemy.orm as orm

import dissomniag
import AbstractNode

class ControlSystem(AbstractNode.AbstractNode, dissomniag.utils.SingletonMixin.Singleton):
    __mapper_args__ = {'polymorphic_identity': 'ControlSystem'}
    
    """
    classdocs
    """
    
    


        
