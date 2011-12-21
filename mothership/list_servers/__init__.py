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
                    'url': '/'+self.namespace,
                    'class': self.name,
                    'namespace': self.namespace,
                    'version': self.version,
                    'call': 'lss',
                    'required_args': {
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 1,
                        'args': {
                            'tag': {
                                'vartype': 'string',
                                'desc': 'filter by tag',
                            },
                            'hw_tag': {
                                'vartype': 'string',
                                'desc': 'filter by hardware tag',
                            },
                            'name': {
                                'vartype': 'string',
                                'desc': 'filter by name',
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
            cfg: the config object. useful everywhere
            listby: what parameter to list by (vlan, site_id, etc.)
            lookfor: filter to apply to the parameter
            (ie. to look in vlan 105, listby=vlan lookfor=105)

        [return value]
        a list containing the names of servers matching the filters
        """

        cfg = self.cfg
        buf = []

        if len(query) > self.metadata['methods']['lss']['optional_args']['max']:
            retval = "too many queries! max number of queries is: %s\n" % self.metadata['methods']['lss']['optional_args']['max']
            retval += "you tried to pass %s queries\n" % len(query)
            print retval
            raise ListServersError(retval)
        else:
            print "num queries: %s" % len(query)
            print "max num queries: %s" % self.metadata['methods']['lss']['optional_args']['max']

#        # list servers by vlan
#        if listby == 'vlan':
#          if lookfor == None:
#            raise ListServersError("you must supply a value to filter on")
#          else:
#            for serv, net in cfg.dbsess.query(Server, Network).\
#            filter(Network.ip!=None).\
#            filter(Network.vlan==lookfor).\
#            filter(Server.id==Network.server_id).\
#            order_by(Server.hostname):
#              buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
#
#        # list servers by site_id
#        elif listby == 'site_id':
#          if lookfor == None:
#            raise ListServersError("you must supply a value to filter on")
#          else:
#            for serv in cfg.dbsess.query(Server).\
#            filter(Server.site_id==lookfor).\
#            order_by(Server.hostname):
#                buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
#
#        # list servers by tag
#        elif listby == 'tag':
#          if lookfor == None:
#            raise ListServersError("you must supply a value to filter on")
#          else:
#            servers_primary = []
#            for server in cfg.dbsess.query(Server).\
#            filter(Server.tag==lookfor).\
#            order_by(Server.hostname):
#              servers_primary.append(server)
#            servers_kv = []
#            kvs = mothership.kv.collect(cfg, None, key='tag')
#            for i in kvs:
#               namespace,key = str(i).split(' ')
#               if key == "tag="+lookfor:
#                 servers_kv.append(i.hostname+"."+i.realm+"."+i.site_id)
#               else:
#                 pass
#            if servers_primary:
#              for serv in servers_primary:
#                buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
#            elif servers_kv:
#              for serv in servers_kv:
#                buf.append(serv)
#            else:
#              pass
#
#        # list servers by realm
#        elif listby == 'realm':
#          if lookfor == None:
#            raise ListServersError("you must supply a value to filter on")
#          else:
#            for serv in cfg.dbsess.query(Server).\
#            filter(Server.realm==lookfor).\
#            order_by(Server.hostname):
#              buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
#
#
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
#        # list servers by hw_tag
#        elif listby == 'hw_tag':
#          if lookfor == None:
#            raise ListServersError("you must supply a value to filter on")
#          else:
#            for serv in cfg.dbsess.query(Server).\
#            filter(Server.hw_tag==lookfor):
#                buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
#
#
#        # list servers by virtual
#        elif listby == 'virtual':
#          for serv in cfg.dbsess.query(Server).\
#          filter(Server.virtual==True).\
#          order_by(Server.hostname):
#              buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
#
#        # list servers by physical
#        elif listby == 'physical':
#          for serv in cfg.dbsess.query(Server).\
#          filter(Server.virtual==False).\
#          order_by(Server.hostname):
#              buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
#
#        # list servers by name
#        elif listby == 'name':
#          if lookfor == None:
#            raise ListServersError("you must supply a value to filter on")
#          else:
#            search_string = '%' + lookfor + '%'
#            for serv in cfg.dbsess.query(Server).\
#            filter(Server.hostname.like(search_string)).\
#            order_by(Server.hostname):
#                buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
#
        # list all servers by default
        if not query:
          for serv in cfg.dbsess.query(Server).order_by(Server.hostname):
              buf.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))

        return buf
