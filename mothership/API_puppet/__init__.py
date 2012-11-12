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
import mothership.API_kv
import mothership.API_userdata
from mothership.validate import *
from mothership.mothership_models import *
from mothership.common import *

class PuppetError(Exception):
    pass


class API_puppet:

    def __init__(self, cfg):
        self.cfg = cfg
        self.common = MothershipCommon(cfg)
        self.kvobj = mothership.API_kv.API_kv(cfg)
        self.userdataobj = mothership.API_userdata.API_userdata(cfg)
        self.version = 1
        self.namespace = 'API_puppet'
        self.metadata = {
            'config': {
                'shortname': 'p',
                'description': 'creates a puppet manifest for a server (puppet\'s External Node Classifier)',
                'module_dependencies': {
                    'mothership_models': 1,
                    'mothership.API_kv': 1,
                    'mothership.API_userdata': 1,
                },
            },
            'methods': {
                'classify': {
                    'description': 'classify a puppet node',
                    'short': 'c',
                    'rest_type': 'GET',
                    'admin_only': False, 
                    'required_args': {
                        'args': {
                            'unqdn': {
                                'vartype': 'str',
                                'desc': 'unqdn of the server to classify',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'node': {
                            'environment': 'realm',
                            'classes': [
                                'tag',
                                'tag',
                            ],
                            'parameters': {
                                'parameter1': 'str',
                                'parameter2': 'str',
                                'parameter3': [
                                    'sub-parameter',
                                    'sub-parameter',
                                ],
                                'parameter4': 'str',
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
        classes = []
        mtags = []
        environment = ""
        parameters = {}
        groups = []
        security_level = 0
        server_id = None
        mtag = None
        networks = []
        sudoers = []
        node = {}

        # make sure we got a unqdn 
        try:
            if not 'unqdn' in query or not query['unqdn']:
                self.cfg.log.debug("API_puppet/classify: you must specify a unqdn to query for")
                raise PuppetError("API_puppet/classify: you must specify a unqdn to query for")
            self.cfg.log.debug("API_puppet/classify: querying for unqdn : %s" % query['unqdn'])
            # check for min/max number of optional arguments
            self.common.check_num_opt_args(query, self.namespace, 'classify')

            s = v_get_server_obj(self.cfg, query['unqdn'])

            # theoretically this should never happen. holdover from old days
            if type(s) == list:
                self.cfg.log.debug("API_puppet/classify: unqdn is not unique enough")
                raise PuppetError("API_puppet/classify: unqdn is not unique enough")
                

            if s:
                unqdn = "%s.%s.%s" % (s.hostname, s.realm, s.site_id)
                parameters['unqdn'] = unqdn
                parameters['site_id'] = s.site_id
                parameters['realm'] = s.realm
                groups.append("%s_%s_%s" % (s.hostname, s.realm, s.site_id))
                groups.append("%s_%s" % (s.realm, s.site_id))
                groups.append("%s" % (s.site_id))

                mtag = self.cfg.dbsess.query(Tag).filter(Tag.name==s.tag).first()
                parameters['server_id'] = s.id
                networks = self.cfg.dbsess.query(Network).\
                        filter(Network.server_id==s.id).all()
                for network in networks:
                    if network.interface=='eth1':
                        if network.static_route:
                            parameters['default_gateway'] = network.static_route
                        if network.ip:
                            parameters['primary_ip'] = network.ip
                        if network.netmask:
                            parameters['bond_netmask'] = network.netmask
                        if network.bond_options:
                            parameters['bond_options'] = network.bond_options
            else:
                self.cfg.log.debug("API_puppet/classify: unqdn not found: %s" % query['unqdn'])
                raise PuppetError("API_puppet/classify: unqdn not found: %s" % query['unqdn'])
            
            # Tag
            if mtag and mtag.name:
                mtags.append(mtag.name)
                classes.append("tags::%s" % mtag.name)
                parameters['mtag'] = mtag.name

            if s.tag_index:
                parameters['mtag_index'] = s.tag_index

            # Security
            if mtag and mtag.security_level != None:
                security_level = mtag.security_level

            if s.security_level:
                classes.append("security%s" % server.security_level)
                parameters['security_level'] = server.security_level

            # Key/values
            kvquery = {'unqdn': unqdn}
            kvs = self.kvobj.collect(kvquery)
            for kv in kvs:
                if kv['key'] == 'environment':
                    environment = kv['value']
                elif kv['key'] == 'tag':
                    mtags.append(kv['value'])
                    classes.append("tags::%s" % kv['value'])
                elif kv['key'] == 'class':
                    classes.append(kv['value'])
                elif kv['key'] == 'group':
                    groups.append(kv['value'])
                else:
                    parameters[kv['key']] = kv['value']

            # sudoers
            sudoers = self.userdataobj._gen_sudoers_groups(unqdn)
            parameters['mtags'] = mtags
            parameters['groups'] = groups
            if sudoers:
                parameters['sudoers_groups'] = sudoers

            node['classes'] = classes
            node['environment'] = environment
            node['parameters'] = parameters

        except Exception, e:
            self.cfg.log.debug("API_puppet/classify: query failed. Error: %s" % e)
            raise PuppetError("API_puppet/classify: query failed. Error: %s" % e)

        return node
