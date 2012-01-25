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
    mothership.serverinfo

    Collects and displays information about servers
"""

# import some modules
import sys

import mothership
import mothership.API_kv
from mothership.mothership_models import *

from sqlalchemy import or_, desc, MetaData


class ListServersError(Exception):
    pass


class API_list_servers:

    def __init__(self, cfg):
        self.cfg = cfg
        kvobj = mothership.API_kv.API_kv(cfg)
        self.version = 1
        self.namespace = 'API_list_servers'
        self.metadata = {
            'config': {
                'shortname': 'lss',
                'description': 'lists servers according to certain criteria',
                'module_dependencies': {
                    'API_kv': 1,
                    'mothership_models': 1,
                },
            },
            'methods': {
                'lss': {
                    'description': 'list all servers matching a particular criteria',
                    'rest_type': 'GET',
                    'required_args': {
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 1,
                        'args': {
                            'all': {
                                'vartype': 'None',
                                'desc': 'retrieve all servers',
                                'ol': 'a',
                            },
                            'tag': {
                                'vartype': 'string',
                                'desc': 'filter by tag',
                                'ol': 't',
                            },
                            'hw_tag': {
                                'vartype': 'string',
                                'desc': 'filter by hardware tag',
                                'ol': 'w',
                            },
                            'hostname': {
                                'vartype': 'string',
                                'desc': 'filter by hostname',
                                'ol': 'n',
                            },
                            'virtual': {
                                'vartype': 'bool',
                                'desc': 'filter by physical/virtual',
                                'ol': 'V',
                            },
                            'disk': {
                                'vartype': 'int',
                                'desc': 'filter by disk (in GB)',
                                'ol': 'd',
                            },
                            'ram': {
                                'vartype': 'int',
                                'desc': 'filter by ram (in GB)',
                                'ol': 'R',
                            },
                            'cores': {
                                'vartype': 'int',
                                'desc': 'filter by number of cores',
                                'ol': 'c',
                            },
                            'model': {
                                'vartype': 'string',
                                'desc': 'filter by model',
                                'ol': 'm',
                            },
                            'manufacturer': {
                                'vartype': 'string',
                                'desc': 'filter by manufacturer',
                                'ol': 'M',
                            },
                            'realm': {
                                'vartype': 'string',
                                'desc': 'filter by realm',
                                'ol': 'r',
                            },
                            'site_id': {
                                'vartype': 'string',
                                'desc': 'filter by site_id',
                                'ol': 's',
                            },
                            'vlan': {
                                'vartype': 'int',
                                'desc': 'filter by (numeric) vlan id',
                                'ol': 'v',
                            },
                        },
                    },
                    'return': {
                        'servers': ['fqdn', 'fqdn',],
                    },
                },
            },
        }


    def lss(self, query):
        """
        [description]
        creates a list of all servers found for a given parameter

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        a list containing the names of servers matching the filters
        """

        cfg = self.cfg
        buf = []

        if len(query.keys()) > self.metadata['methods']['lss']['optional_args']['max']:
            retval = "API_list_servers/lss: too many queries! max number of queries is: %s\n" % self.metadata['methods']['lss']['optional_args']['max']
            retval += "API_list_servers/lss: you tried to pass %s queries\n" % len(query.keys())
            if cfg.debug:
                print retval
            raise ListServersError(retval)
        else:
            if cfg.debug:
                print "API_list_servers/lss: num queries: %s" % len(query.keys())
                print "API_list_servers/lss: max num queries: %s" % self.metadata['methods']['lss']['optional_args']['max']

        # list all servers
        if 'all' in query.keys():
            if cfg.debug:
                print "API_list_servers/lss: querying for ALL servers"
            try:
                for serv in cfg.dbsess.query(Server).order_by(Server.hostname):
                    buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
            except Exception, e:
                raise ListServersError("API_list_servers/lss: query failed for ALL servers. Error: %s" % e)

        # list servers by name
        if 'hostname' in query.keys():
            if not query['hostname']:
                if cfg.debug:
                    print "API_list_servers/lss: you must supply a value to filter by hostname"
                raise ListServersError("API_list_servers/lss: you must supply a value to filter by hostname")
            else:
                try:
                    if cfg.debug:
                        print "API_list_servers/lss: querying on name: %s" % query['hostname']
                    search_string = '%' + query['hostname'] + '%'
                    for serv in cfg.dbsess.query(Server).\
                    filter(Server.hostname.like(search_string)).\
                    order_by(Server.hostname):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                except Exception, e:
                    raise ListServersError("API_list_servers/lss: failed query for hostname: %s. Error: %s" % (query['hostname'], e))

        # list physical (bare metal, non-virtual) servers
        if 'physical' in query.keys():
            try:
                if cfg.debug:
                    print "API_list_servers/lss: querying for physical (baremetal) servers"
                for serv in cfg.dbsess.query(Server).\
                filter(Server.virtual==False).\
                order_by(Server.hostname):
                    buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
            except Exception, e:
                raise ListServersError("API_list_servers/lss: failed query for physical servers. Error: %s" % e)

        # list virtual servers
        if 'virtual' in query.keys():
            try:
                if cfg.debug:
                    print "API_list_servers/lss: querying for virtual servers"
                for serv in cfg.dbsess.query(Server).\
                    filter(Server.virtual==True).\
                    order_by(Server.hostname):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
            except Exception, e:
                raise ListServersError("API_list_servers/lss: failed query for virtual servers. Error: %s" % e)

        # list servers by hw_tag
        if 'hw_tag' in query.keys():
            if not query['hw_tag']:
                if cfg.debug:
                    print "API_list_servers/lss: you must supply a value to filter by hw_tag"
                raise ListServersError("API_list_servers/lss: you must supply a value to filter by hw_tag")
            else:
                try:
                    if cfg.debug:
                        print "API_list_servers/lss: querying on hw_tag: %s" % query['hw_tag']
                    for serv in cfg.dbsess.query(Server).\
                    filter(Server.hw_tag==query['hw_tag']):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                except Exception, e:
                    raise ListServersError("API_list_servers/lss: failed query for hw_tag: %s. Exception: %s" % (query['hw_tag'], e))

        # list servers by vlan
        if 'vlan' in query.keys():
            if not query['vlan']:
                if cfg.debug:
                    print "API_list_servers/lss: you must supply a value to filter by vlan"
                raise ListServersError("API_list_servers/lss: you must supply a value to filter by vlan")
            else:
                try:
                    if cfg.debug:
                        print "API_list_servers/lss: querying on vlan: %s" % query['vlan']
                    for serv, net in cfg.dbsess.query(Server, Network).\
                    filter(Network.ip!=None).\
                    filter(Network.vlan==query['vlan']).\
                    filter(Server.id==Network.server_id).\
                    order_by(Server.hostname):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                except Exception, e:
                    raise ListServersError("API_list_servers/lss: failed query for vlan: %s. Error: %s" % (query['vlan'], e))

        # list servers by site_id
        if 'site_id' in query.keys():
            if not query['site_id']:
                if cfg.debug:
                    print "API_list_servers/lss: you must supply a value to filter by site_id"
                raise ListServersError("API_list_servers/lss: you must supply a value to filter by site_id")
            else:
                try:
                    if cfg.debug:
                        print "API_list_servers/lss: querying on site_id: %s" % query['site_id']
                    for serv in cfg.dbsess.query(Server).\
                    filter(Server.site_id==query['site_id']).\
                    order_by(Server.hostname):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                except Exception, e:
                    raise ListServersError("API_list_servers/lss: failed query for site_id: %s. Error: %s" % (query['vlan'], e))

        # list servers by tag
        if 'tag' in query.keys():
            if not query['tag']:
                if cfg.debug:
                    print "API_list_servers/lss: you must supply a value to filter by tag"
                raise ListServersError("API_list_servers/lss: you must supply a value to filter by tag")
            else:
                try:
                    if cfg.debug:
                        print "API_list_servers/lss: querying on tag: %s" % query['tag']
                    servers_primary = []
                    for server in cfg.dbsess.query(Server).\
                    filter(Server.tag==query['tag']).\
                    order_by(Server.hostname):
                        servers_primary.append(server)
                    servers_kv = []
                    kvs = kvobj.collect(cfg, None, key='tag')
                    for i in kvs:
                        namespace,key = str(i).split(' ')
                        if key == "tag="+query['tag']:
                            servers_kv.append(i.hostname+"."+i.realm+"."+i.site_id)
                        else:
                            pass
                    if servers_primary:
                        for serv in servers_primary:
                            buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                    elif servers_kv:
                        for serv in servers_kv:
                            buf.append(serv)
                    else:
                        pass
                except Exception, e:
                    raise ListServersError("API_list_servers/lss: failed query for tag: %s. Error: %s" % (query['tag'], e))

        # list servers by realm
        if 'realm' in query.keys():
            if not query['realm']:
                if cfg.debug:
                    print "API_list_servers/lss: you must supply a value to filter on realm"
                raise ListServersError("API_list_servers/lss: you must supply a value to filter on realm")
            else:
                try:
                    if cfg.debug:
                        print "API_list_servers/lss: querying on realm: %s" % query['realm']
                    for serv in cfg.dbsess.query(Server).\
                    filter(Server.realm==query['realm']).\
                    order_by(Server.hostname):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                except Exception, e:
                    raise ListServersError("API_list_servers/lss: failed query for realm: %s. Error: %s" % (query['realm'], e))

        # list servers by manufacturer
        if 'manufacturer' in query.keys():
            if not query['manufacturer']:
                if cfg.debug:
                    print "API_list_servers/lss: you must supply a value to filter on manufacturer"
                raise ListServersError("API_list_servers/lss: you must supply a value to filter on manufacturer")
            else:
                try:
                    if cfg.debug:
                        print "API_list_servers/lss: querying on manufacturer: %s" % query['manufacturer']
                    search_string = '%' + query['manufacturer'] + '%'
                    for serv, hw in cfg.dbsess.query(Server, Hardware).\
                    filter(Hardware.manufacturer.like(search_string)).\
                    filter(Server.hw_tag==Hardware.hw_tag).\
                    order_by(Server.hostname):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                except Exception, e:
                    raise ListServersError("API_list_servers/lss: failed query for manufacturer: %s. Error: %s" % (query['manufacturer'], e))

        # list servers by model name
        if 'model' in query.keys():
            if not query['model']:
                if cfg.debug:
                    print "API_list_servers/lss: you must supply a value to filter on model"
                raise ListServersError("API_list_servers/lss: you must supply a value to filter on model")
            else:
                try:
                    if cfg.debug:
                        print "API_list_servers/lss: querying on model: %s" % query['model']
                    search_string = '%' + query['model']+ '%'
                    for serv, hw in cfg.dbsess.query(Server, Hardware).\
                    filter(Hardware.model.like(search_string)).\
                    filter(Server.hw_tag==Hardware.hw_tag).\
                    order_by(Server.hostname):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                except Exception, e:
                    raise ListServersError("API_list_servers/lss: failed query for model: %s. Error: %s" % (query['model'], e))

        # list servers by cores
        if 'cores' in query.keys():
            if not query['cores'].isdigit():
                if cfg.debug:
                    print "API_list_servers/lss: you must supply an int to filter by number of cores"
                raise ListServersError("API_list_servers/lss: you must supply an int to filter by number of cores")
            else:
                try:
                    if cfg.debug:
                        print "API_list_servers/lss: querying on number of cores: %s" % query['cores']
                    for serv in cfg.dbsess.query(Server).\
                    filter(Server.cores==query['cores']).\
                    order_by(Server.hostname):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                except Exception, e:
                    raise ListServersError("API_list_servers/lss: query failed for number of cores: %s. Error: %s" % (query['cores'], e))

        # list servers by ram
        if 'ram' in query.keys():
            if not query['ram'].isdigit():
                if cfg.debug:
                    print "API_list_servers/lss: you must supply an int to filter by ram size (in GB)"
                raise ListServersError("API_list_servers/lss: you must supply an int to filter by ram size (in GB)")
            else:
                try:
                    if cfg.debug:
                        print "API_list_servers/lss: querying on ram size in GB: %s" % query['ram']
                    for serv in cfg.dbsess.query(Server).\
                    filter(Server.ram==query['ram']).\
                    order_by(Server.hostname):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                except Exception, e:
                    raise ListServersError("API_list_servers/lss: query failed for ram size in GB: %s. Error: %s" % (query['ram'], e))

        # list servers by disk
        if 'disk' in query.keys():
            if not query['disk'].isdigit():
                if cfg.debug:
                    print "API_list_servers/lss: you must supply an int to filter by disk size (in GB)"
                raise ListServersError("API_list_servers/lss: you must supply an int to filter by disk size (in GB)")
            else:
                try:
                    if cfg.debug:
                        print "API_list_servers/lss: querying on disk size in GB: %s" % query['disk']
                    for serv in cfg.dbsess.query(Server).\
                    filter(Server.disk==query['disk']).\
                    order_by(Server.hostname):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                except Exception, e:
                    raise ListServersError("API_list_servers/lss: query failed for disk size in GB: %s. Error: %s" % (query['disk'], e))


        # return the list of servers we've found
        return buf
