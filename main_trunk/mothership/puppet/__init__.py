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
from mothership_models import *

def classify(cfg, name):
    """
    Puppet external node classifier.  Returns the hash to dump as yaml.
    """
    classes = []
    tags = []
    environment = ""
    parameters = {}
    groups = []
    security_level = 0
    server = None
    server_id = None
    tag = None
    networks = []
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
    server = cfg.dbsess.query(Server).filter(Server.hostname==hostname).first()
    if server:
        tag = cfg.dbsess.query(Tag).filter(Tag.name==server.tag).first()

    if server and server.id:
        server_id = server.id
        parameters['server_id'] = server_id
        networks = cfg.dbsess.query(Network).\
                filter(Network.server_id==server_id).all()
        for network in networks:
            if network.interface=='eth1':
                if network.static_route:
                    default_gateway = network.static_route
                    parameters['default_gateway'] = default_gateway
                if network.ip:
                    bond_ip = network.ip
                    parameters['bond_ip'] = bond_ip
                if network.netmask:
                    bond_netmask = network.netmask
                    parameters['bond_netmask'] = bond_netmask
                if network.bond_options:
                    bond_options = network.bond_options
                    parameters['bond_options'] = bond_options

    # Tag
    if tag and tag.name:
        tags.append(tag.name)
        classes.append("tags::%s" % tag.name)
        parameters['tag'] = tag.name

    if server and server.tag_index:
        parameters['tag_index'] = server.tag_index

    # Security
    if tag and tag.security_level != None:
        security_level = tag.security_level

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
            tags.append(value)
            classes.append("tags::%s" % value)
        elif key == 'class':
            classes.append(value)
        elif key == 'group':
            groups.append(value)
        else:
            parameters[key] = value

    parameters['tags'] = tags
    parameters['groups'] = groups

    node = {}
    node['classes'] = classes
    node['environment'] = environment
    node['parameters'] = parameters

    return node
