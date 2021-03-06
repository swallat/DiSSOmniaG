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
import unittest
import dissomniag

dissomniag.initMigrate.init()
dissomniag.taskManager.Dispatcher.startDispatcher()


class Test(unittest.TestCase):


    def setUp(self):
        self.session = dissomniag.Session()
        self.user = dissomniag.getIdentity().getAdministrativeUser()
        self.host = self.session.query(dissomniag.model.Host).one()


    def tearDown(self):
        pass


    def testInsertNew(self):
        self.numNets = len(self.session.query(dissomniag.model.Network).all())
        netString = dissomniag.model.generatedNetwork.getFreeNetString(self.user, self.host)
        net = dissomniag.model.generatedNetwork(self.user, netString, host = self.host)
        self.newNumNets = len(self.session.query(dissomniag.model.Network).all())
        assert (self.numNets + 1) == self.newNumNets
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testInsertNew']
    unittest.main()
