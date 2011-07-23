
import migrate.versioning.api
import migrate.versioning.exceptions
import os

import api
import cliApi
import config
import auth
from dissomniag.config import DB_FILE

#Migrate DB ti current version
if not config.MAINTANANCE:
    try:
        migrate.versioning.api.version_control(config.DB_STRING, config.MIGRATE_REPOSITORY, version = None)
    except migrate.versioning.exceptions.DatabaseAlreadyControlledError:
        print("DB under version controll.")
    migrate.versioning.api.upgrade(config.DB_STRING, config.MIGRATE_REPOSITORY, version = None)

from server import startServer

