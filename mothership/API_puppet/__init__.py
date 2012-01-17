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
mothership.API_puppet

module controlling various puppet interactions
"""

import mothership
import mothership.kv
import mothership.users
from mothership.mothership_models import *

class PuppetError(Exception):
    pass

class API_puppet:

    def __init__(self, cfg):
        self.cfg = cfg
        self.version = 1
        self.name = 'API_puppet'
        self.namespace = 'API_puppet'
        self.metadata = {
            'config': {
                'description': 'creates a puppet manifest for a server (puppet\'s External Node Classifier)',
                'module_dependencies': {
                    'mothership_models': 1,
                    'mothership.kv': 1,
                    'mothership.users': 1,
                },
            },
            'methods': {
                'classify': {
                    'description': 'classify a puppet node',
                    'rest_type': 'GET',
                    'required_args': {
                        'args': {
                            'hostname': {
                                'vartype': 'string',
                                'desc': 'hostname of the server to classify',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'cmdln_aliases': [
                        'p',
                        'puppet_classify',
                        'classify_puppet',
                    ],
                    'return': {
                        'node': {
                            'environment': 'realm',
                            'classes': [
                                'tag',
                                'tag',
                            ],
                            'parameters': {
                                'parameter1': 'string',
                                'parameter2': 'string',
                                'parameter3': [
                                    'sub-parameter',
                                    'sub-parameter',
                                ],
                                'parameter4': 'string',
                            },
                        },
                    },
                },
            },
        }


    def classify(self, query):
        """
        [description]
        search for a host based on info supplied, spit back a dict to be used to construct a puppet manifest

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        returns a dict of information if successful
        """
        cfg = self.cfg
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
        node = {}

        # make sure we got a hostname
        try:
            name = query['hostname']
            if name:
                if cfg.debug:
                    print "API_puppet/classify: querying for hostname: %s" % name
            else:
                if cfg.debug:
                    print "API_puppet/classify: you must specify a (string) value in order to query by hostname"
                raise PuppetError("API_puppet/classify: you must specify a (string) value in order to query by hostname")

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
                mtag = cfg.dbsess.query(Tag).filter(Tag.name==server.tag).first()

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

            # sudoers
            sudoers = mothership.users.gen_sudoers_groups(cfg, unqdn)

            parameters['mtags'] = mtags
            parameters['groups'] = groups
            if sudoers:
                parameters['sudoers_groups'] = sudoers

            node['classes'] = classes
            node['environment'] = environment
            node['parameters'] = parameters

        except:
            if cfg.debug:
                print "API_puppet/classify: query failed for hostname: %s" % name
            raise PuppetError("API_puppet/classify: query failed for hostname: %s" % name)

        return node
