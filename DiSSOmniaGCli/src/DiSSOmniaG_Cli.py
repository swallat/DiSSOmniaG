#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on 12.07.2011

@author: sw
"""
import xmlrpclib

def DiSSOmniaG_Cli():
    server = xmlrpclib.Server('http://localhost:8000')
    print server.getSay()

if __name__ == "__main__":
    DiSSOmniaG_Cli()