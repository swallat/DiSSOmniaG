# -*- coding: utf-8 -*-
"""
Created on 25.07.2011

@author: Sebastian Wallat
"""

import sys, logging
from dissomniag.dbAccess import Session

log = logging.getLogger("utils.wrapper")

def wrap_db(func):
    def callFunc(*args, **kwargs):
        session = Session()
        f = func(*args, **kwargs)
        session.commit()
        Session.remove()
        return f
    return callFunc
