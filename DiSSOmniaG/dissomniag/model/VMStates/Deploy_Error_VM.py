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

log = logging.getLogger("model.VMStates.Deploy_Error_VM")

class Deploy_Error_VM(AbstractVMState):
    '''
    classdocs
    '''
    def test(self, job):
        return self.sanityCheck(job)
    
    def prepare(self, job):
        return self.reset(job)
        
    def deploy(self, job):
        return self.sanityCheck(job)
    
    def start(self, job):
        if self.sanityCheck(job):
            return self.vm.runningState.create(job)
        else:
            raise dissomniag.taskManager("VM could not be started!")
    
    def stop(self, job):
        return self.sanityCheck(job)
    
    def sanityCheck(self, job):
        self.vm.changeState(dissomniag.model.NodeState.PREPARED)
        return self.vm.runningState.deploy(job)
    
    def reset(self, job):
        self.vm.changeState(dissomniag.model.NodeState.DEPLOYED)
        if self.vm.runningState.reset(job):
            return True
        else:
            self.changeState(dissomniag.model.NodeState.PREPARE_ERROR)
            return False
        