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
import logging

log = logging.getLogger("tasks.GitTasks")
    
class GitPushAdminRepo(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        try:
            dissomniag.GitEnvironment().update(self.job)
        except Exception as e:
            self.multiLog("GitPushAdminRepo %s" % str(e), log)
            return dissomniag.taskManager.TaskFailed("GitPushAdminRepo %s" % str(e))
        
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
class CheckGitEnvironment(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        try:
            env = dissomniag.GitEnvironment()
            self.multiLog("Entering GitEnvironment()._checkAdmin", log)
            env._checkAdmin(self.job)
            self.multiLog("Entering GitEnvironment()._checkRepoFolder", log)
            env._checkRepoFolder(self.job)
        except Exception as e:
            self.multiLog(str(e), log)
            #Give one retry:
            try:
                self.multiLog("Retry CheckGitEnvironment:", log)
                env = dissomniag.GitEnvironment()
                self.multiLog("Entering GitEnvironment()._checkAdmin", log)
                env._checkAdmin(self.job)
                self.multiLog("Entering GitEnvironment()._checkRepoFolder", log)
                env._checkRepoFolder(self.job)
            except Exception as e:
                self.multiLog(str(e), log)
            
        return dissomniag.taskManager.TaskReturns.SUCCESS
    
    def revert(self):
        return dissomniag.taskManager.TaskReturns.SUCCESS