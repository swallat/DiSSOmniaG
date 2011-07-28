from sqlalchemy import *
from migrate import *

meta = MetaData()
import datetime

    
jobs = Table('jobs', meta,
             Column('id', Integer, primary_key = True),
             Column('description', Text, nullable = False),
             Column('startTime', DateTime, default = datetime.datetime.now(), nullable = False),
             Column('endTime', DateTime),
             Column('state', Integer, CheckConstraint("0 >= state > 7", name = "jobState"), nullable = False),
             Column('trace', Text),
)

def upgrade(migrate_engine):
    print("Migrate: Add Jobs Table")
    meta.bind = migrate_engine
    jobs.create()

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    jobs.drop()
