# Copyright 2011 Gilt Groupe, INC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref

Base = declarative_base()

class KV(Base):
    __tablename__ = 'kv'

    key = Column(String)
    value = Column(String)
    hostname = Column(String)
    site_id = Column(String)
    realm = Column(String)
    id = Column(Integer, primary_key=True)

    def __init__(self, key, value, hostname, realm, site_id):
        self.key = key
        self.value = value
        self.hostname = hostname
        self.realm = realm
        self.site_id = site_id

    def __repr__(self):
        namespace = [self.hostname, self.realm, self.site_id]
        namespace = filter(None, namespace)
        display = ".".join(namespace)
        return "%s %s=%s" % (display, self.key, self.value)

class Tag(Base):
    __tablename__ = 'tags'

    name = Column(String)
    start_port = Column(Integer)
    stop_port = Column(Integer)
    id = Column(Integer, primary_key=True)
    security_level = Column(Integer)

    def __init__(self, name, start_port, stop_port, security_level):
        self.name = name
        self.start_port = start_port
        self.stop_port = stop_port
        self.security_level = security_level

class Server(Base):
    __tablename__ = 'servers'

    id = Column(Integer, primary_key=True)
    hostname = Column(String)
    cores = Column(Integer)
    site_id = Column(String)
    realm = Column(String)
    tag = Column(String)
    tag_index = Column(Integer)
    cores = Column(Integer)
    ram = Column(Integer)
    disk = Column(Integer)
    hw_tag = Column(String)
    os = Column(String)
    cobbler_profile = Column(String)
    comment = Column(String)
    virtual = Column(Boolean)
    provision_date = Column(Date)
    security_level = Column(Integer)
    cost = Column(Integer)
    active = Column(Boolean)

    def __init__(self, hostname):
        self.name = hostname

    def __repr__(self):
       return "<Server('%s', '%s', '%s', '%s')>" % (self.hostname,
               self.realm, self.site_id, self.hw_tag)

class ServerGraveyard(Base):
    __tablename__ = 'server_graveyard'

    id = Column(Integer, primary_key=True)
    hostname = Column(String)
    cores = Column(Integer)
    site_id = Column(String)
    realm = Column(String)
    tag = Column(String)
    tag_index = Column(Integer)
    cores = Column(Integer)
    ram = Column(Integer)
    disk = Column(Integer)
    hw_tag = Column(String)
    os = Column(String)
    cobbler_profile = Column(String)
    comment = Column(String)
    virtual = Column(Boolean)
    provision_date = Column(Date)
    deprovision_date = Column(Date)
    security_level = Column(Integer)
    cost = Column(Integer)

    def __init__(self, hostname):
        self.name = hostname

    def __repr__(self):
       return "<Server('%s', '%s', '%s', '%s')>" % (self.hostname,
               self.realm, self.site_id, self.hw_tag)

class Hardware(Base):
    __tablename__ = 'hardware'

    id = Column(Integer, primary_key=True)
    hw_tag = Column(String)
    purchase_date = Column(Date)
    manufacturer = Column(String)
    cores = Column(Integer)
    ram = Column(Integer)
    disk = Column(String)
    site_id = Column(String)
    rack_id = Column(String)
    cost = Column(Integer)
    kvm_switch = Column(String)
    kvm_port = Column(Integer)
    power_port = Column(Integer)
    power_switch  = Column(String)
    model  = Column(String)
    cpu_sockets = Column(Integer)
    cpu_speed  = Column(String)
    rma = Column(Boolean)

    def __init__(self, hw_tag):
        self.hw_tag = hw_tag

    def __repr__(self):
       return "<Hardware('%s','%s', '%s', '%s')>" % (self.hw_tag, self.cores, self.ram, self.disk)

class DnsAddendum(Base):
    __tablename__ = 'dns_addendum'

    id = Column(Integer, primary_key=True)
    realm = Column(String)
    site_id = Column(String)
    host = Column(String)
    target = Column(String)
    record_type = Column(String)

    def __init__(self, host, record_type, realm, site_id, target):
        self.site_id = site_id
        self.realm = realm
        self.host = host
        self.target = target
        self.record_type = record_type

    def __repr__(self):
       return "<DnsAddendum('%s','%s', '%s', '%s')>" % (self.host, self.record_type, self.site_id, self.realm)

class Network(Base):
    __tablename__ = 'network'

    id = Column(Integer, primary_key=True)
    mac = Column(String)
    site_id = Column(String)
    realm = Column(String)
    vlan = Column(Integer)
    netmask = Column(String)
    server_id = Column(Integer, ForeignKey(Server.id))
    interface = Column(String)
    switch = Column(String)
    switch_port = Column(String)
    bond_options = Column(String)
    ip = Column(String)             # ip is actually an inet in PG
    static_route = Column(String)   # static_route is actually an inet in PG
    public_ip = Column(String)      # public_ip is actually an inet in PG
    hw_tag = Column(String)
 
    def __init__(self, ip, interface, netmask, mac):
        self.ip = ip
        self.interface = interface
        self.netmask = netmask
        self.mac = mac

    def __repr__(self):
       return "<Network('%s', '%s', '%s', '%s', '%s')>" % (self.ip, self.mac, self.interface, self.site_id, self.realm)

class XenPools(Base):
    __tablename__ = 'xen_pools'

    realm = Column(String)
    pool_id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey(Server.id))
    server = relation(Server)
    
    def __init__(self, realm, pool_id):
        self.realm = realm
        self.pool_id = pool_id

    def __repr__(self):
       return "<XenPools('%s', '%s')>" % (self.realm, self.pool_id)

class Users(Base):
    __tablename__ = 'users'

    first_name = Column(String)
    last_name = Column(String)
    ssh_public_key = Column(String)
    username = Column(String, primary_key=True)
    site_id = Column(String, primary_key=True)
    realm = Column(String, primary_key=True)
    uid = Column(Integer)
    id = Column(Integer, primary_key=True)
    type = Column(String)
    hdir = Column(String)
    shell = Column(String)
    email = Column(String)
    active = Column(Boolean, server_default='true')

    def __init__(self, first_name, last_name, ssh_public_key, username, site_id, realm, uid, type, hdir, shell, email, active):
        self.first_name = first_name
        self.last_name = last_name
        self.ssh_public_key = ssh_public_key
        self.username = username
        self.site_id = site_id
        self.realm = realm
        self.uid = uid
        self.type = type
        self.hdir = hdir
        self.shell = shell
        self.email = email
        self.active = active

    def __repr__(self):
        return "<Users('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')>" % (self.first_name, self.last_name, self.ssh_public_key, self.username, self.site_id, self.realm, self.uid, self.type, self.hdir, self.shell, self.email, self.active)

class Groups(Base):
    __tablename__ = 'groups'

    description = Column(String)
    sudo_cmds = Column(String)
    groupname = Column(String, primary_key=True)
    site_id = Column(String, primary_key=True)
    realm = Column(String, primary_key=True)
    gid = Column(Integer)
    id = Column(Integer, primary_key=True)

    def __init__(self, description, sudo_cmds, groupname, site_id, realm, gid):
        self.description = description
        self.sudo_cmds = sudo_cmds
        self.groupname = groupname
        self.site_id = site_id
        self.realm = realm
        self.gid = gid

    def __repr__(self):
        return "<Groups('%s', '%s', '%s', '%s', '%s')>" % (self.description, self.groupname, self.site_id, self.realm, self.sudo_cmds)

class UserGroupMapping(Base):
    __tablename__ = 'user_group_mapping'

    groups_id = Column(Integer, ForeignKey(Groups.id))
    users_id = Column(Integer, ForeignKey(Users.id))
    id = Column(Integer, primary_key=True)

    def __init__(self, groups_id, users_id):
        self.groups_id = groups_id
        self.users_id = users_id

    def __repr__(self):
        return "<UserGroupMapping('%s', '%s')>" % (self.groups_id, self.users_id)
