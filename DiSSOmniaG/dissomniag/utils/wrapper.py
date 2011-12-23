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
import sys, logging
from dissomniag.dbAccess import Session
import dissomniag

log = logging.getLogger("utils.wrapper")


"""
Rewrite
Synchronization decorator
  This decorator can be used to synchronize method calls. Synchronization is relative to 
  some kind of lock. Before each function call the acquire method of the lock is called,
  and after the function call the release method is called regardless of exceptions.

Example:
  @synchronized(threading.Lock())
  def critical():
    ...critical_block...
"""
def synchronized(conditionOrLock):
    def wrap(fn):
        def call(*args, **kwargs):
            with conditionOrLock:
                return fn(*args, **kwargs)
        #call.__name__ = fn.__name__
        #call.__doc__ = fn.__doc__
        #call.__dict__.update(fn.__dict__)
        return call
    return wrap