# -*- coding: utf-8 -*-
"""
Created on 10.08.2011

@author: Sebastian Wallat
"""

import dissomniag

class CheckHostUpTask(dissomniag.taskManager.AtomicTask):
    
    def run(self):
        if not hasattr(self.context, "host") or  type(self.context.host) != dissomniag.model.Host:
            self.job.trace("CheckHostUpTask: In Context missing host object.")
            raise dissomniag.taskManager.UnrevertableFailure("In Context missing host object.")
        
        ip = self.context.host.maintainanceIP.addr
        if dissomniag.utils.PingUtils.isIpPingable(ip):
            self.context.host.changeState(dissomniag.model.NodeStates.UP)
        else:
            self.context.host.changeState(dissomniag.model.NodeStates.DOWN)
    
    def revert(self):
        pass
