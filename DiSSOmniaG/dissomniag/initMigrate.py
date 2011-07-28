# -*- coding: utf-8 -*-
"""
Created on 27.07.2011

@author: Sebastian Wallat
"""
import migrate.versioning.api
import migrate.versioning.exceptions
import dissomniag.config as config

def init():
    """
    Initial Database Migration
    """
    try:
        migrate.versioning.api.version_control(config.db.db_string, config.db.migrate_repository)
    except migrate.versioning.exceptions.DatabaseAlreadyControlledError:
        print("DB under version control.")
      
    migrate.versioning.api.upgrade(config.db.db_string, config.db.migrate_repository)
