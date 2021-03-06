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
import dissomniag
from dissomniag.model.VMStates import *

import logging

log = logging.getLogger("model.VMStates.Prepare_Error_VM")

class Prepare_Error_VM(AbstractVMState):
    '''
    classdocs
    '''
    def test(self, job):
        return self.sanityCheck(job)
    
    def prepare(self, job):
        return self.sanityCheck(job)
    
    def deploy(self, job):
        self.vm.changeState(dissomniag.model.NodeState.NOT_CREAED)
        return self.vm.runningState.deploy(job)
    
    def start(self, job):
        self.vm.changeState(dissomniag.model.NodeState.NOT_CREAED)
        return self.vm.runningState.start(job)
    
    def stop(self, job):
        return True
    
    def sanityCheck(self, job):
        self.vm.changeState(dissomniag.model.NodeState.NOT_CREATED)
        return self.vm.runningState.prepare(job)
    
    def reset(self, job):
        self.vm.changeState(dissomniag.model.NodeState.PREPARED)
        return self.vm.runningState.reset(job)
        