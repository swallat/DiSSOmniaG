from sqlalchemy import *
from migrate import *

meta = MetaData()

users = Table('users', meta,
             Column('id', Integer, primary_key = True),
             Column('username', String(40), nullable = False, unique = True),
             Column('passwd', String(40), nullable = False),
             Column('isAdmin', Boolean, default = False),
             Column('loginRPC', Boolean, default = False),
             Column('loginSSH', Boolean, default = False),
             Column('loginManhole', Boolean, default = False),
             Column('isHtpasswd', Boolean, default = False),
)

public_keys = Table('public_keys', meta,
                    Column('id', Integer, primary_key = True),
                    Column('publicKey', Binary(1000), nullable = False, unique = True),
)

user_publickey = Table('user_publickey', meta,
                       Column('user_id', Integer, ForeignKey('users.id')),
                       Column('key_id', Integer, ForeignKey('public_keys.id')),
)

def upgrade(migrate_engine):
    print("Migrate: Add User Table")
    meta.bind = migrate_engine
    users.create()
    print("Migrate: Add Public Key Table")
    public_keys.create()
    print("Migrate: Add User_publickey Table")
    user_publickey.create()

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    users.drop()
    public_keys.drop()
    user_publickey.drop()
