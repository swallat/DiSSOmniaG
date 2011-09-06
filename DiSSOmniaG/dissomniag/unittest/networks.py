# -*- coding: utf-8 -*-
"""
Created on 06.09.2011

@author: Sebastian Wallat
"""
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
