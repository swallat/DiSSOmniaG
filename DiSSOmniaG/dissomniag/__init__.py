
import migrate.versioning.api
import migrate.versioning.exceptions
import os, logging

import config

import dissomniag.utils.Logging

log = logging.getLogger("dissomniag.__init__")

import dissomniag.config
from dissomniag.config import db

#Migrate DB ti current version
try:
    migrate.versioning.api.version_control(db.db_string, db.migrate_repository, version = None)
except migrate.versioning.exceptions.DatabaseAlreadyControlledError:
    print("DB under version control.")
migrate.versioning.api.upgrade(db.db_string, db.migrate_repository, version = None)

from dissomniag.dbAccess import Session, Base
from dissomniag.utils import *
import api
import cliApi
import config
import auth


from server import startServer

