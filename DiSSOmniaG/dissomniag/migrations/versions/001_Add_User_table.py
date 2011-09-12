from sqlalchemy import *
from migrate import *
import uuid
import datetime

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

jobs = Table('jobs', meta,
             Column('id', Integer, primary_key = True),
             Column('description', Text, nullable = False),
             Column('startTime', DateTime, default = datetime.datetime.now(), nullable = False),
             Column('endTime', DateTime),
             Column('state', Integer, CheckConstraint("0 <= state < 7", name = "jobState"), nullable = False),
             Column('trace', Text),
             Column('user_id', Integer, ForeignKey('users.id')),
)

 
sshNodeKeys = Table('sshNodeKeys', meta,
           Column('id', Integer, primary_key = True),
           Column('privateKey', Binary(1000), unique = True, nullable = True),
           Column('privateKeyFile', String, nullable = True),
           Column('publicKey', Binary(1000), unique = True, nullable = True),
           Column('publicKeyFile', String, nullable = True),
)

nodes = Table('nodes', meta,
           Column('id', Integer, primary_key = True),
           Column('uuid', String(36), nullable = False, unique = True),
           Column('commonName', String(40), nullable = False, unique = True),
           Column('sshKey_id', Integer, ForeignKey('sshNodeKeys.id')),
           Column('administrativeUserName', String(), default = "root", nullable = False),
           Column('utilityFolder', String(200), nullable = True),
           Column('state', Integer, CheckConstraint("0 <= state < 7", name = "nodeState"), nullable = False),
           Column('type', String(50), nullable = False),
)

hosts = Table('hosts', meta,
           Column('id', Integer, ForeignKey('nodes.id'), primary_key = True),
           Column('qemuConnector', String(100)),
           Column('bridgedInterfaceName', String(10)),
           Column('lastChecked', DateTime, nullable = True, default = None),
           Column('configurationMissmatch', Boolean, nullable = True, default = None),
           Column('libvirtVersion', String(10), nullable = True, default = None),
           Column('kvmUsable', Boolean, nullable = True, default = None),
           Column('freeDiskspace', String(20), nullable = True, default = None),
           Column('ramCapacity', String(20), nullable = True, default = None),
           Column('libvirtCapabilities', String, nullable = True, default = None),
)

interfaces = Table('interfaces', meta,
           Column('id', Integer, primary_key = True),
           Column('macAddress', String(17), nullable = False, unique = True),
           Column('name', String(20), nullable = False),
           Column('node_id', Integer, ForeignKey('nodes.id')),
           Column('maintainanceInterface', Boolean, nullable = False, default = False),
           UniqueConstraint('id', 'node_id', 'name'),
)

networks = Table('networks', meta,
           Column('id', Integer, primary_key = True),
           Column('uuid', String(36), nullable = False, unique = True),
           Column('name', String, nullable = False),
           Column('netAddress', String(39), nullable = False),
           Column('netMask', String(39), nullable = False),
           Column('type', String(50), nullable = False),
)

genNetworks = Table('genNetworks', meta,
           Column('id', Integer, ForeignKey('networks.id'), primary_key = True),
           Column('topology_id', Integer, ForeignKey('topologies.id')),
           Column('state', Integer, CheckConstraint("0 <= state < 4", name = "genNetState"), nullable = True),
           Column('withQos', Boolean, nullable = False, default = False),
           Column('inboundAverage', Integer),
           Column('inboundPeak', Integer),
           Column('inboundBurst', Integer),
           Column('outboundAverage', Integer),
           Column('outboundPeak', Integer),
           Column('outboundBurst', Integer),
)

topologies = Table('topologies', meta,
           Column('id', Integer, primary_key = True),
           Column('name', String, nullable = False),
           Column('host_id', Integer, ForeignKey('hosts.id')),
)

node_network = Table('node_network', meta,
                          Column('node_id', Integer, ForeignKey('nodes.id')),
                          Column('network_id', Integer, ForeignKey('networks.id')),
)

ipAddresses = Table('ipAddresses', meta,
           Column('id', Integer, primary_key = True),
           Column('addr', String(39), nullable = False),
           Column('isV6', Boolean, nullable = False, default = False),
           Column('isDhcpAddress', Boolean, nullable = False, default = False),
           Column('isMaintainance', Boolean, nullable = False, default = False),
           Column('node_id', Integer, ForeignKey('nodes.id')), #One to many style
           Column('interface_id', Integer, ForeignKey('interfaces.id')), # One to many style
           Column('network_id', Integer, ForeignKey('networks.id')), # Many to One style
           Column('topology_id', Integer, ForeignKey('topologies.id')), #Many to One style
           UniqueConstraint('addr', 'node_id', name = "uniqueAddressPerNode"),
)

user_topology = Table('user_topology', meta,
          Column('user_id', Integer, ForeignKey('users.id')),
          Column('topology_id', Integer, ForeignKey('topologies.id')),
)

liveCds = Table('livecds', meta,
           Column('id', Integer, primary_key = True),
           Column('buildDir', String, nullable = False),
           Column('staticAptList', String),
           Column('pxeInternalPath', String),
           Column('pxeExternalPath', String),
)

vms = Table('vms', meta,
           Column('id', Integer, ForeignKey('nodes.id'), primary_key = True),
           Column('ramSize', String, default = "1024MB", nullable = False),
           Column('hdSize', String, default = "5GB"),
           Column('isHdCreated', Boolean, default = False, nullable = False),
           Column('useHD', Boolean, default = False, nullable = False),
           Column('enableVNC', Boolean, default = False, nullable = False),
           Column('vncPort', String),
           Column('vncPassword', String(40)),
           Column('dynamicAptList', String),
           Column('topology_id', Integer, ForeignKey('topologies.id')),
           Column('host_id', Integer, ForeignKey('hosts.id')),
           Column('liveCd_id', Integer, ForeignKey('livecds.id')),
)


topology_connections = Table('topologyConnections', meta,
          Column('id', Integer, primary_key = True),
          Column('fromVM_id', Integer, ForeignKey('vms.id'), nullable = False),
          Column('viaGenNetwork_id', Integer, ForeignKey('networks.id'), nullable = False),
          Column('toVm_id', Integer, ForeignKey('vms.id'), nullable = False),
          Column('topology_id', Integer, ForeignKey('topologies.id')),
)





def upgrade(migrate_engine):
    meta.bind = migrate_engine
    print("Migrate: Add User Table")
    users.create()
    print("Migrate: Add Public Key Table")
    public_keys.create()
    print("Migrate: Add User_publickey Table")
    user_publickey.create()
    print("Migrate: Add Job Table")
    jobs.create()
    print("Migrate: Add sshHostKeys Table")
    sshNodeKeys.create()
    print("Migrate: Add Nodes Table")
    nodes.create()
    print("Migrate: Add Hosts Table")
    hosts.create()
    print("Migrate: Add Interfaces Table")
    interfaces.create()
    print("Migrate: Add Topologies Table")
    topologies.create()
    print("Migrate: Add Networks Table")
    networks.create()
    print("Migrate: Add genNetworks Table")
    genNetworks.create()
    print("Migrate: Add Node_Network Table")
    node_network.create()
    print("Migrate: Add ipAddresses Table")
    ipAddresses.create()
    print("Migrate: Add user_topology Table")
    user_topology.create()
    print("Migrate: Add LiveCds Table")
    liveCds.create()
    print("Migrate: Add VMs Table")
    vms.create()
    print("Migrate: Add Topology_Connections Table")
    topology_connections.create()
    

def downgrade(migrate_engine):
    meta.bind = migrate_engine
    topology_connections.drop()
    vms.drop()
    liveCds.drop()
    user_topology.drop()
    ipAddresses.drop()
    node_network.drop()
    genNetworks.drop()
    networks.drop()
    topologies.drop()
    interfaces.drop()
    hosts.drop()
    nodes.drop()
    sshNodeKeys.drop()
    jobs.drop()
    user_publickey.drop()
    public_keys.drop()
    users.drop()
