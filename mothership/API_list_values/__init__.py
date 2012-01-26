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
    supports the listing of various types of values
"""

# imports
from sqlalchemy import or_, desc, MetaData
from mothership.mothership_models import *
import mothership.common

class ListValuesError(Exception):
    pass


class API_list_values:

    def __init__(self, cfg):
        self.cfg = cfg
        self.log = mothership.common.MothershipLogger(self.cfg)
        self.version = 1
        self.namespace = 'API_list_values'
        self.metadata = {
            'config': {
                'shortname': 'lsv',
                'description': 'retrieves and lists values from the database',
                'module_dependencies': {
                    'mothership_models': 1,
                },
            },
            'methods': {
                'lsv': {
                    'description': 'list all values of a given type',
                    'rest_type': 'GET',
                    'required_args': {
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 1,
                        'args': {
                            'available_hardware': {
                                'vartype': 'None',
                                'desc': 'all hardware available for provisioning servers on',
                                'ol': 'a',
                            },
                            'ips': {
                                'vartype': 'None',
                                'desc': 'all ip addresses in use',
                                'ol': 'i',
                            },
                            'vlans': {
                                'vartype': 'None',
                                'desc': 'all vlans',
                                'ol': 'v',
                            },
                            'tags': {
                                'vartype': 'None',
                                'desc': 'all tags',
                                'ol': 't',
                            },
                            'groups': {
                                'vartype': 'None',
                                'desc': 'all groups',
                                'ol': 'g',
                            },
                            'users': {
                                'vartype': 'None',
                                'desc': 'all users',
                                'ol': 'u',
                            },
                        },
                    },
                    'return': {
                        'values': ['value', 'value',], # in the case of users and groups, this will be a list of dicts
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
        if len(query.keys()) > self.metadata['methods']['lsv']['optional_args']['max']:
            retval = "API_list_values/lsv: too many queries! max number of queries is: %s\n" % self.metadata['methods']['lsv']['optional_args']['max']
            retval += "API_list_values/lsv: you tried to pass %s queries\n" % len(query.keys())
            self.log.debug(retval)
            raise ListServersError(retval)
        else:
            self.log.debug("API_list_values/lsv: num queries: %s" % len(query.keys()))
            self.log.debug("API_list_values/lsv: max num queries: %s" % self.metadata['methods']['lsv']['optional_args']['max'])

        # make sure we are being passed a valid query
        if query.keys()[0] not in self.metadata['methods']['lsv']['optional_args']['args'].keys():
            self.log.debug("API_list_values/lsv: unsupported listing for: %s. please specify one of the following: %s" % (query.keys()[0], " ".join(self.metadata['methods']['lsv']['optional_args']['args'].keys())))
            raise ListValuesError("API_list_values/lsv: unsupported listing for: %s. please specify one of the following: %s" % (query.keys()[0], " ".join(self.metadata['methods']['lsv']['optional_args']['args'].keys())))

        # look up all vlans
        if 'vlans' in query.keys():
            self.log.debug("API_list_values/lsv: querying for all vlans")
            try:
                for result in cfg.dbsess.query(Network.vlan).\
                    filter(Network.vlan!=0).\
                    order_by(Network.vlan).\
                    distinct().all():
                        buf.append(result.vlan)
                self.log.debug(buf)
            except Exception, e:
                self.log.debug("API_list_values/lsv: query failed for: vlans. Error: %s" % e)
                raise ListValuesError("API_list_values/lsv: query failed for: vlans. Error: %s" % e)

        elif 'ips' in query.keys():
            self.log.debug("API_list_values/lsv: querying for all ips")
            try:
                for net in cfg.dbsess.query(Network).order_by(Network.ip):
                    if net.ip != '0.0.0.0' and net.ip != None:
                        buf.append(net.ip)
                self.log.debug(buf)
            except Exception, e:
                self.log.debug("API_list_values/lsv: query failed for: ips. Error: %s" % e)
                raise ListValuesError("API_list_values/lsv: query failed for: ips. Error: %s" % e)

        elif 'tags' in query.keys():
            self.log.debug("API_list_values/lsv: querying for all tags")
            try:
                for tag in cfg.dbsess.query(Tag):
                    buf.append(tag.name)
                self.log.debug(buf)
            except Exception, e:
                self.log.debug("API_list_values/lsv: query failed for tags. Error: %s" % e)
                raise ListValuesError("API_list_values/lsv: query failed for tags. Error: %s" % e)

        elif 'groups' in query.keys():
            self.log.debug("API_list_values/lsv: querying for all groups")
            try:
                for g in cfg.dbsess.query(Groups):
                    buf.append("%s.%s.%s gid:%s" % (g.groupname, g.realm, g.site_id, g.gid))
                self.log.debug(buf)
            except Exception, e:
                self.log.debug("API_list_values/lsv: query failed for groups. Error: %s" % e)
                raise ListValuesError("API_list_values/lsv: query failed for groups. Error: %s" % e)

        elif 'users' in query.keys():
            self.log.debug("API_list_values/lsv: querying for all users")
            try:
                for u in cfg.dbsess.query(Users):
                    if u.active:
                        act = "active"
                    else:
                        act = "inactive"
                    buf.append("%s.%s.%s uid:%s %s" % (u.username, u.realm, u.site_id, u.uid, act))
                self.log.debug(buf)
            except Exception, e:
                self.log.debug("API_list_values/lsv: query failed for users. Error: %s" % e)
                raise ListValuesError("API_list_values/lsv: query failed for groups. Error: %s" % e)

        elif 'available_hardware' in query.keys():
            self.log.debug("API_list_values/lsv: querying for all available hardware")
            try:
                # setting up some vars
                all_hw = []
                alloc_hw = []
                # fetch list of all hardware tags
                for h in cfg.dbsess.query(Hardware):
                    all_hw.append(h.hw_tag)
                # fetch list of all hardware tags assigned to servers
                for s in cfg.dbsess.query(Server):
                    alloc_hw.append(s.hw_tag)
                # diff 'em
                buf = [item for item in all_hw if not item in alloc_hw]
                self.log.debug(buf)
            except Exception, e:
                raise ListValuesError("API_list_values/lsv: query failed for available_hardware" % e)


        # return our listing
        return buf
