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
import sqlalchemy as sa
import sqlalchemy.orm as orm
import dissomniag
from dissomniag.dbAccess import Base
from dissomniag.model import *

class GeneralNetwork(dissomniag.Base):
    __tablename__ = "generalNetworks"
    id = sa.Column('id', sa.Integer, primary_key = True)
    name = sa.Column(sa.String, nullable = False)
    topology_id = sa.Column(sa.Integer, sa.ForeignKey('topologies.id'))
    topology = orm.relationship("Topology", backref = "generalNetworks")
    xValue = sa.Column(sa.Integer, nullable = False, default = 0)
    yValue = sa.Column(sa.Integer, nullable = False, default = 0)
    zValue = sa.Column(sa.Integer, nullable = False, default = 0)


    def __init__(self):
        '''
        Constructor
        '''
        pass
        