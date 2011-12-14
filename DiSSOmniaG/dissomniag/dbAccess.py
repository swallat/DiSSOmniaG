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
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import dissomniag.config as config

log = logging.getLogger("dbAccess")

engine = create_engine(config.db.db_string, echo = (True if config.db.maintainance else False))
#engine = create_engine(config.db.db_string, echo = True)
Session = scoped_session(sessionmaker())
Session.configure(bind = engine)

Base = declarative_base()
"""
The declarative Base
"""

def saveFlush(session):
    try:
        session.flush()
    except Exception as e:
        session.rollback()
        raise e
    
def saveCommit(session):
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
