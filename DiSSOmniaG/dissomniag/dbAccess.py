# -*- coding: utf-8 -*-
"""
Created on 23.07.2011

@author: Sebastian Wallat
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import dissomniag.config as config

log = logging.getLogger("dbAccess")

engine = create_engine(config.db.db_string, echo = (True if config.db.maintainance else False))
Session = scoped_session(sessionmaker())
Session.configure(bind = engine)

Base = declarative_base()
