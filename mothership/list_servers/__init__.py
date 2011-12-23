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
import mothership
import sys
import mothership.kv
from mothership.mothership_models import *
from sqlalchemy import or_, desc, MetaData


class ListServersError(Exception):
    pass

class list_servers:

    def __init__(self, cfg):
        self.cfg = cfg
        self.version = '1'
        self.name = 'list_servers'
        self.namespace = 'list_servers'
        self.metadata = {
            'config': {
                'module_dependencies': {
                    'kv': '1',
                    'mothership_models': '1',
                    'mothership': '1',
                },
            },
            'methods': {
                'lss': {
                    'description': 'list all servers matching a particular criteria',
                    'call': 'lss',
                    'required_args': {
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 1,
                        'args': {
                            'all': {
                                'vartype': 'None',
                                'desc': 'retrieve all servers',
                            },
                            'tag': {
                                'vartype': 'string',
                                'desc': 'filter by tag',
                            },
                            'hw_tag': {
                                'vartype': 'string',
                                'desc': 'filter by hardware tag',
                            },
                            'hostname': {
                                'vartype': 'string',
                                'desc': 'filter by hostname',
                            },
                            'virtual': {
                                'vartype': 'bool',
                                'desc': 'filter by physical/virtual',
                            },
                            'disk': {
                                'vartype': 'int',
                                'desc': 'filter by disk (in GB)',
                            },
                            'ram': {
                                'vartype': 'int',
                                'desc': 'filter by ram (in GB)',
                            },
                            'cores': {
                                'vartype': 'int',
                                'desc': 'filter by number of cores',
                            },
                            'model': {
                                'vartype': 'string',
                                'desc': 'filter by model',
                            },
                            'manufacturer': {
                                'vartype': 'string',
                                'desc': 'filter by manufacturer',
                            },
                            'realm': {
                                'vartype': 'string',
                                'desc': 'filter by realm',
                            },
                            'site_id': {
                                'vartype': 'string',
                                'desc': 'filter by site_id',
                            },
                            'vlan': {
                                'vartype': 'int',
                                'desc': 'filter by (numeric) vlan id',
                            },
                        },
                    },
                    'cmdln_aliases': [
                        'lss',
                        'listservers',
                        'listserver',
                        'list_server',
                    ],
                    'return': {
                        'servers': 'list',
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
            query: the query string being passed to us from the called URI 

        [return value]
        a list containing the names of servers matching the filters
        """

        cfg = self.cfg
        buf = []

        if len(query) > self.metadata['methods']['lss']['optional_args']['max']:
            retval = "too many queries! max number of queries is: %s\n" % self.metadata['methods']['lss']['optional_args']['max']
            retval += "you tried to pass %s queries\n" % len(query)
            if cfg.debug:
                print retval
            raise ListServersError(retval)
        else:
            if cfg.debug:
                print "num queries: %s" % len(query)
                print "max num queries: %s" % self.metadata['methods']['lss']['optional_args']['max']

#        # list servers by manufacturer
#        elif listby == 'manufacturer':
#          if lookfor == None:
#            raise ListServersError("you must supply a value to filter on")
#          else:
#            search_string = '%' + lookfor + '%'
#            for serv, hw in cfg.dbsess.query(Server, Hardware).\
#            filter(Hardware.manufacturer.like(search_string)).\
#            filter(Server.hw_tag==Hardware.hw_tag).\
#            order_by(Server.hostname):
#                buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
#
#        # list servers by model name
#        elif listby == 'model':
#          if lookfor == None:
#            raise ListServersError("you must supply a value to filter on")
#          else:
#            search_string = '%' + lookfor + '%'
#            for serv, hw in cfg.dbsess.query(Server, Hardware).\
#            filter(Hardware.model.like(search_string)).\
#            filter(Server.hw_tag==Hardware.hw_tag).\
#            order_by(Server.hostname):
#                buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
#
#        # list servers by cores
#        elif listby == 'cores':
#          if lookfor.isdigit():
#            raise ListServersError("you must supply a value to filter on")
#          else:
#            for serv in cfg.dbsess.query(Server).\
#            filter(Server.cores==lookfor).\
#            order_by(Server.hostname):
#                buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
#
#        # list servers by ram
#        elif listby == 'ram':
#          if lookfor.isdigit():
#            raise ListServersError("you must supply a value to filter on")
#          else:
#            for serv in cfg.dbsess.query(Server).\
#            filter(Server.ram==lookfor).\
#            order_by(Server.hostname):
#                buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
#
#        # list servers by disk
#        elif listby == 'disk':
#          if lookfor.isdigit():
#            raise ListServersError("you must supply a value to filter on")
#          else:
#            for serv in cfg.dbsess.query(Server).\
#            filter(Server.disk==lookfor).\
#            order_by(Server.hostname):
#                buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
#



        # list all servers
        if 'all' in query.keys():
            if cfg.debug:
                print "list_servers: querying for ALL servers"
            try:
                for serv in cfg.dbsess.query(Server).order_by(Server.hostname):
                    buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
            except:
                if cfg.debug:
                    print "list_servers: query failed for ALL servers"
                raise ListServersError("list_servers: query failed for ALL servers")

        # list servers by name
        if 'hostname' in query.keys():
            if not query['hostname']:
                if cfg.debug:
                    print "list_servers: you must supply a value to filter by hostname"
                raise ListServersError("list_servers: you must supply a value to filter by hostname")
            else:
                try:
                    if cfg.debug:
                        print "list_servers: querying on name: %s" % query['hostname']
                    search_string = '%' + query['hostname'] + '%'
                    for serv in cfg.dbsess.query(Server).\
                    filter(Server.hostname.like(search_string)).\
                    order_by(Server.hostname):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                except:
                    if cfg.debug:
                        print "list_servers: failed query for hostname: %s" % query['hostname']
                    raise ListServersError("list_servers: failed query for hostname: %s" % query['hostname'])

        # list physical (bare metal, non-virtual) servers
        if 'physical' in query.keys():
            try:
                if cfg.debug:
                    print "list_servers: querying for physical (baremetal) servers"
                for serv in cfg.dbsess.query(Server).\
                filter(Server.virtual==False).\
                order_by(Server.hostname):
                    buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
            except:
                if cfg.debug:
                    print "list_servers: failed query for physical servers"
                raise ListServersError("list_servers: failed query for physical servers")

        # list virtual servers
        if 'virtual' in query.keys():
            try:
                if cfg.debug:
                    print "list_servers: querying for virtual servers"
                for serv in cfg.dbsess.query(Server).\
                    filter(Server.virtual==True).\
                    order_by(Server.hostname):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
            except:
                if cfg.debug:
                    print "list_servers: failed query for virtual servers"
                raise ListServersError("list_servers: failed query for virtual servers")

        # list servers by hw_tag
        if 'hw_tag' in query.keys():
            if not query['hw_tag']:
                if cfg.debug:
                    print "list_servers: you must supply a value to filter by hw_tag"
                raise ListServersError("list_servers: you must supply a value to filter by hw_tag")
            else:
                try:
                    if cfg.debug:
                        print "list_servers: querying on hw_tag: %s" % query['hw_tag']
                    for serv in cfg.dbsess.query(Server).\
                    filter(Server.hw_tag==query['hw_tag']):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                except:
                    if cfg.debug:
                        print "list_servers: failed query for hw_tag: %s" % query['hw_tag']
                    raise ListServersError("list_servers: failed query for hw_tag: %s" % query['hw_tag'])

        # list servers by vlan
        if 'vlan' in query.keys():
            if not query['vlan']:
                if cfg.debug:
                    print "list_servers: you must supply a value to filter by vlan"
                raise ListServersError("list_servers: you must supply a value to filter by vlan")
            else:
                try:
                    if cfg.debug:
                        print "list_servers: querying on vlan: %s" % query['vlan']
                    for serv, net in cfg.dbsess.query(Server, Network).\
                    filter(Network.ip!=None).\
                    filter(Network.vlan==query['vlan']).\
                    filter(Server.id==Network.server_id).\
                    order_by(Server.hostname):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                except:
                    if cfg.debug:
                        print "list_servers: failed query for vlan: %s" % query['vlan']
                    raise ListServersError("list_servers: failed query for vlan: %s" % query['vlan'])

        # list servers by site_id
        if 'site_id' in query.keys():
            if not query['site_id']:
                if cfg.debug:
                    print "list_servers: you must supply a value to filter by site_id"
                raise ListServersError("list_servers: you must supply a value to filter by site_id")
            else:
                try:
                    if cfg.debug:
                        print "list_servers: querying on site_id: %s" % query['site_id']
                    for serv in cfg.dbsess.query(Server).\
                    filter(Server.site_id==query['site_id']).\
                    order_by(Server.hostname):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                except:
                    if cfg.debug:
                        print "list_servers: failed query for site_id: %s" % query['vlan']
                    raise ListServersError("list_servers: failed query for site_id: %s" % query['vlan'])

        # list servers by tag
        if 'tag' in query.keys():
            if not query['tag']:
                if cfg.debug:
                    print "list_servers: you must supply a value to filter by tag"
                raise ListServersError("list_servers: you must supply a value to filter by tag")
            else:
                try:
                    if cfg.debug:
                        print "list_servers: querying on tag: %s" % query['tag']
                    servers_primary = []
                    for server in cfg.dbsess.query(Server).\
                    filter(Server.tag==query['tag']).\
                    order_by(Server.hostname):
                        servers_primary.append(server)
                    servers_kv = []
                    kvs = mothership.kv.collect(cfg, None, key='tag')
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
                except:
                    if cfg.debug:
                        print "list_servers: failed query for tag: %s" % query['tag']
                    raise ListServersError("list_servers: failed query for tag: %s" % query['tag'])

        # list servers by realm
        if 'realm' in query.keys():
            if not query['realm']:
                if cfg.debug:
                    print "list_servers: you must supply a value to filter on realm"
                raise ListServersError("list_servers: you must supply a value to filter on realm")
            else:
                try:
                    if cfg.debug:
                        print "list_servers: querying on realm: %s" % query['realm']
                    for serv in cfg.dbsess.query(Server).\
                    filter(Server.realm==query['realm']).\
                    order_by(Server.hostname):
                        buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
                except:
                    if cfg.debug:
                        print "list_servers: failed query for realm: %s" % query['realm']
                    raise ListServersError("list_servers: failed query for realm: %s" % query['realm'])





        return buf
