#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on 19.07.2011

@author: Sebastian Wallat
"""
import sys
import dissomniag
    
def printUsage():
    print("DiSSOmniag Starter.")
    print("Usage: %s [--nodaemon]|--daemon [start|stop|restart]" % sys.argv[0])
    print("\t --nodaemon \t\t Starts DiSSOmniaG attached to the users terminal.")
    print("\t --daemon [start|stop|restart] \t Starts, stops or restarts DiSSOmniaG as a daemon process.")

if __name__ == "__main__":
        if len(sys.argv) == 3 and "--daemon" == sys.argv[1]:
                if 'start' == sys.argv[2]:
                        dissomniag.start()
                elif 'stop' == sys.argv[2]:
                        dissomniag.stop()
                elif 'restart' == sys.argv[2]:
                        dissomniag.restart()
                else:
                        print "Unknown command"
                        printUsage()
                        sys.exit(2)
                sys.exit(0)
        elif len(sys.argv) == 1 or (len(sys.argv) == 2 and "--nodaemon" == sys.argv[1]):
            dissomniag.run()
        else:
                printUsage()
                sys.exit(2)
