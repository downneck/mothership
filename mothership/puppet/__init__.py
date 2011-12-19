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
"""
mothership.puppet

module controlling various puppet interactions
"""

import mothership
import mothership.kv
import mothership.users
import mothership.network_mapper
from mothership.mothership_models import *

def classify(cfg, name):
    """
    Puppet external node classifier.  Returns the hash to dump as yaml.
    """
    classes = []
    mtags = []
    environment = ""
    parameters = {}
    groups = []
    security_level = 0
    server = None
    server_id = None
    mtag = None
    networks = []
    sudoers = []
    hostname, realm, site_id = mothership.get_unqdn(cfg, name)

    # Unique or unqualified domain name
    unqdn = "%s.%s.%s" % (hostname, realm, site_id)
    parameters['unqdn'] = unqdn
    parameters['site_id'] = site_id
    parameters['realm'] = realm

    # LDAP groups
    for g in mothership.add_ldap_groups(hostname, realm, site_id):
        groups.append(g)

    # Server
    server = cfg.dbsess.query(Server).\
        filter(Server.hostname==hostname).\
        filter(Server.realm==realm).\
        filter(Server.site_id==site_id).\
        first()
    if server:
        mtag = cfg.dbsess.query(Tag).filter(Tag.name==server.tag).first()

    if server and server.id:
        parameters['server_id'] = server.id
        networks = cfg.dbsess.query(Network).\
                filter(Network.server_id==server.id).all()
        for network in networks:
            if network.interface=='eth0':
                if network.static_route:
                    parameters['mgmt_gateway'] = network.static_route
                if network.ip:
                    parameters['mgmt_ip'] = network.ip
                if network.netmask:
                    parameters['mgmt_netmask'] = network.netmask
                if network.ip and network.netmask:
                    mgmt_cidr = mothership.network_mapper.remap(cfg,
                        'cidr', nic=network.interface, siteid=site_id)
                    parameters['mgmt_subnet'] = mothership.\
                        network_mapper.get_network(mgmt_cidr)
            if network.interface=='eth1':
                if network.static_route:
                    parameters['default_gateway'] = network.static_route
                if network.ip:
                    parameters['primary_ip'] = network.ip
                if network.netmask:
                    parameters['primary_netmask'] = network.netmask
                if network.bond_options:
                    parameters['bond_options'] = network.bond_options

    # Tag
    if mtag and mtag.name:
        mtags.append(mtag.name)
        classes.append("tags::%s" % mtag.name)
        parameters['mtag'] = mtag.name

    if server and server.tag_index:
        parameters['mtag_index'] = server.tag_index

    # Security
    if mtag and mtag.security_level != None:
        security_level = mtag.security_level

    if server and server.security_level != None:
        security_level = server.security_level

    if security_level != None:
        classes.append("security%s" % security_level)
        parameters['security_level'] = security_level

    # Key/values
    kvs = mothership.kv.collect(cfg, unqdn)
    for kv in kvs:
        key = kv.key
        value = kv.value
        if key == 'environment':
            environment = value
        elif key == 'tag':
            mtags.append(value)
            classes.append("tags::%s" % value)
        elif key == 'class':
            classes.append(value)
        elif key == 'group':
            groups.append(value)
        else:
            parameters[key] = value

    # if no environment defined, use site_id
    if not environment:
        environment = site_id

    # sudoers
    sudoers = mothership.users.gen_sudoers_groups(cfg, unqdn)

    parameters['mtags'] = mtags
    parameters['groups'] = groups
    if sudoers:
        parameters['sudoers_groups'] = sudoers

    node = {}
    node['classes'] = classes
    node['environment'] = environment
    node['parameters'] = parameters

    return node
