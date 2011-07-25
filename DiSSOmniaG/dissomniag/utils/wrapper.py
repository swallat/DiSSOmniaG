# -*- coding: utf-8 -*-
"""
Created on 25.07.2011

@author: Sebastian Wallat
"""



import sys
from dissomniag.dbAccess import Session


def wrap_db(func):
    def callFunc(*args, **kwargs):
        session = Session()
        f = func(*args, **kwargs)
        session.commit()
        Session.remove()
        return f
    return callFunc
