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
    supports the listing of various types of DB data
"""

# imports
from sqlalchemy import or_, desc, MetaData
from mothership.mothership_models import *

class ListValuesError(Exception):
    pass

class list_values:

    def __init__(self, cfg)
        self.cfg = cfg
        self.version = 1
        self.name = 'list_values'
        self.namespace = 'list_values'
        self.metadata = {
            'config': {
                'module_dependencies': {
                    'mothership_models': 1,
                },
            },
            'methods': {
                'lsv': {
                    'description': 'list all values of a given type',
                    'call': 'lsv',
                    'required_args': {
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 1,
                        'args': {
                            'available_hardware': {
                                'vartype': 'None',
                                'desc': 'all hardware available for provisioning servers on',
                            },
                            'ips': {
                                'vartype': 'None',
                                'desc': 'all ip addresses in use',
                            },
                            'vlans': {
                                'vartype': 'None',
                                'desc': 'all vlans',
                            },
                            'tags': {
                                'vartype': 'None',
                                'desc': 'all tags',
                            },
                            'groups': {
                                'vartype': 'None',
                                'desc': 'all groups',
                            },
                            'users': {
                                'vartype': 'None',
                                'desc': 'all users',
                            },
                        },
                    },
                    'cmdln_aliases': [
                        'lsv',
                        'listvalues',
                        'list_values',
                        'listvalue',
                        'list_value',
                    ],
                    'return': {
                        'values': 'list',
                    },
                },
            },
        }


    def lsv(self, query):
        """
        [description]
        lists all values of a given type
    
        [parameter info]
        required:
            query: the query dict being passed to us from the called URI
    
        [return value]
        returns an integer representing the next available UID
        """

        cfg = self.cfg
        buf = []

        # verify the number of query arguments
        if len(query.keys()) > self.metadata['methods']['lss']['optional_args']['max']:
            retval = "too many queries! max number of queries is: %s\n" % self.metadata['methods']['lss']['optional_args']['max']
            retval += "you tried to pass %s queries\n" % len(query.keys())
            if cfg.debug:
                print retval
            raise ListServersError(retval)
        else:
            if cfg.debug:
                print "num queries: %s" % len(query.keys())
                print "max num queries: %s" % self.metadata['methods']['lss']['optional_args']['max']

        if listing not in self.metadata['methods']['lsv']['optional_args']['args'].keys():
            print 'Unsupported listing for: %s' % listing
            print 'Please specify one of the following:\n\t%s' % '\n\t'.join(avail)
            return
        if listing == 'vlan' or listing == 'vlans':
            vlist = []
            for result in cfg.dbsess.query(Network.vlan).\
                filter(Network.vlan!=0).\
                order_by(Network.vlan).\
                distinct().all():
                    vlist.append(result.vlan)
            print '\n'.join(map(str, vlist))
        elif listing == 'ip' or listing == 'ips':
            for net in cfg.dbsess.query(Network).order_by(Network.ip):
                if net.ip != '0.0.0.0' and net.ip != None:
                    print net.ip
        elif listing == 'tag' or listing == 'tags':
            for tag in cfg.dbsess.query(Tag):
              print tag.name
        elif listing == 'group' or listing == 'groups':
            if not quiet:
                print "GID, Group Name, Location"
                print "--------------------------------------------------"
            for g in cfg.dbsess.query(Groups):
                print "%s %s %s.%s" % (g.gid, g.groupname, g.realm, g.site_id)
        elif listing == 'user' or listing == 'users':
            if not quiet:
                print "UID, User Name, Location"
                print "--------------------------------------------------"
            for u in cfg.dbsess.query(Users):
                print "%s %s %s.%s" % (u.uid, u.username, u.realm, u.site_id)
        elif listing == 'available_hardware' or listing == 'free_hardware':
            # setting up some vars
            all_hw = []
            alloc_hw = []
            unalloc_hw = []
            # fetch list of all hardware tags
            for h in cfg.dbsess.query(Hardware):
                all_hw.append(h.hw_tag)
            # fetch list of all hardware tags assigned to servers
            for s in cfg.dbsess.query(Server):
                alloc_hw.append(s.hw_tag)
            # diff 'em
            unalloc_hw = [item for item in all_hw if not item in alloc_hw]
            # display the diff
            if not quiet:
                print "unallocated hardware tags:"
            print '\n'.join(unalloc_hw)
