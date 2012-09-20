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
from mothership.common import *

class ListValuesError(Exception):
    pass


class API_list_values:

    def __init__(self, cfg):
        self.cfg = cfg
        self.common = MothershipCommon(cfg)
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
                    'short': 'l',
                    'rest_type': 'GET',
                    'admin_only': False,
                    'required_args': {
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 1,
                        'args': {
                            'available_hardware': {
                                'vartype': 'bool',
                                'desc': 'all hardware available for provisioning servers on',
                                'ol': 'a',
                            },
                            'ips': {
                                'vartype': 'bool',
                                'desc': 'all ip addresses in use',
                                'ol': 'i',
                            },
                            'vlans': {
                                'vartype': 'bool',
                                'desc': 'all vlans',
                                'ol': 'v',
                            },
                            'tags': {
                                'vartype': 'bool',
                                'desc': 'all tags',
                                'ol': 't',
                            },
                            'groups': {
                                'vartype': 'bool',
                                'desc': 'all groups',
                                'ol': 'g',
                            },
                            'users': {
                                'vartype': 'bool',
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

        buf = []

        # verify the number of query arguments
        if len(query.keys()) > self.metadata['methods']['lsv']['optional_args']['max']:
            retval = "API_list_values/lsv: too many queries! max number of queries is: %s\n" % self.metadata['methods']['lsv']['optional_args']['max']
            retval += "API_list_values/lsv: you tried to pass %s queries\n" % len(query.keys())
            self.cfg.log.debug(retval)
            raise ListValuesError(retval)
        else:
            self.cfg.log.debug("API_list_values/lsv: num queries: %s" % len(query.keys()))
            self.cfg.log.debug("API_list_values/lsv: max num queries: %s" % self.metadata['methods']['lsv']['optional_args']['max'])

        # make sure we are being passed a valid query
        if query.keys()[0] not in self.metadata['methods']['lsv']['optional_args']['args'].keys():
            self.cfg.log.debug("API_list_values/lsv: unsupported listing for: %s. please specify one of the following: %s" % (query.keys()[0], " ".join(self.metadata['methods']['lsv']['optional_args']['args'].keys())))
            raise ListValuesError("API_list_values/lsv: unsupported listing for: %s. please specify one of the following: %s" % (query.keys()[0], " ".join(self.metadata['methods']['lsv']['optional_args']['args'].keys())))
        # check for min/max number of optional arguments
        self.common.check_num_opt_args(query, self.namespace, 'lsv')

        # look up all vlans
        if 'vlans' in query.keys():
            self.cfg.log.debug("API_list_values/lsv: querying for all vlans")
            try:
                for result in self.cfg.dbsess.query(Network.vlan).\
                    filter(Network.vlan!=0).\
                    order_by(Network.vlan).\
                    distinct().all():
                        buf.append(result.vlan)
                self.cfg.log.debug(buf)
            except Exception, e:
                self.cfg.log.debug("API_list_values/lsv: query failed for: vlans. Error: %s" % e)
                cfg.dbsess.rollback()
                raise ListValuesError("API_list_values/lsv: query failed for: vlans. Error: %s" % e)

        elif 'ips' in query.keys():
            self.cfg.log.debug("API_list_values/lsv: querying for all ips")
            try:
                for net in self.cfg.dbsess.query(Network).order_by(Network.ip):
                    if net.ip != '0.0.0.0' and net.ip != None:
                        buf.append(net.ip)
                self.cfg.log.debug(buf)
            except Exception, e:
                self.cfg.log.debug("API_list_values/lsv: query failed for: ips. Error: %s" % e)
                cfg.dbsess.rollback()
                raise ListValuesError("API_list_values/lsv: query failed for: ips. Error: %s" % e)

        elif 'tags' in query.keys():
            self.cfg.log.debug("API_list_values/lsv: querying for all tags")
            try:
                for tag in self.cfg.dbsess.query(Tag):
                    buf.append(tag.name)
                self.cfg.log.debug(buf)
            except Exception, e:
                self.cfg.log.debug("API_list_values/lsv: query failed for tags. Error: %s" % e)
                cfg.dbsess.rollback()
                raise ListValuesError("API_list_values/lsv: query failed for tags. Error: %s" % e)

        elif 'groups' in query.keys():
            self.cfg.log.debug("API_list_values/lsv: querying for all groups")
            try:
                for g in self.cfg.dbsess.query(Groups):
                    buf.append("%s.%s.%s gid:%s" % (g.groupname, g.realm, g.site_id, g.gid))
                self.cfg.log.debug(buf)
            except Exception, e:
                self.cfg.log.debug("API_list_values/lsv: query failed for groups. Error: %s" % e)
                cfg.dbsess.rollback()
                raise ListValuesError("API_list_values/lsv: query failed for groups. Error: %s" % e)

        elif 'users' in query.keys():
            self.cfg.log.debug("API_list_values/lsv: querying for all users")
            try:
                for u in self.cfg.dbsess.query(Users):
                    if u.active:
                        act = "active"
                    else:
                        act = "inactive"
                    buf.append("%s.%s.%s uid:%s %s" % (u.username, u.realm, u.site_id, u.uid, act))
                self.cfg.log.debug(buf)
            except Exception, e:
                self.cfg.log.debug("API_list_values/lsv: query failed for users. Error: %s" % e)
                cfg.dbsess.rollback()
                raise ListValuesError("API_list_values/lsv: query failed for groups. Error: %s" % e)

        elif 'available_hardware' in query.keys():
            self.cfg.log.debug("API_list_values/lsv: querying for all available hardware")
            try:
                # setting up some vars
                all_hw = []
                alloc_hw = []
                # fetch list of all hardware tags
                for h in self.cfg.dbsess.query(Hardware):
                    all_hw.append(h.hw_tag)
                # fetch list of all hardware tags assigned to servers
                for s in self.cfg.dbsess.query(Server):
                    alloc_hw.append(s.hw_tag)
                # diff 'em
                buf = [item for item in all_hw if not item in alloc_hw]
                self.cfg.log.debug(buf)
            except Exception, e:
                cfg.dbsess.rollback()
                raise ListValuesError("API_list_values/lsv: query failed for available_hardware" % e)


        # return our listing
        return buf
