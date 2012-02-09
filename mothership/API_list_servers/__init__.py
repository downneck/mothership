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
import mothership.common
import mothership.API_kv
from mothership.mothership_models import *

from sqlalchemy import or_, desc, MetaData


class ListServersError(Exception):
    pass


class API_list_servers:

    def __init__(self, cfg):
        self.cfg = cfg
        self.kvobj = mothership.API_kv.API_kv(cfg)
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
                    'admin_only': False,
                    'required_args': {
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 2,
                        'args': {
                            'all': {
                                'vartype': 'bool',
                                'desc': 'retrieve all servers',
                                'ol': 'a',
                            },
                            'tag': {
                                'vartype': 'str',
                                'desc': 'filter by tag',
                                'ol': 't',
                            },
                            'hw_tag': {
                                'vartype': 'str',
                                'desc': 'filter by hardware tag',
                                'ol': 'w',
                            },
                            'hostname': {
                                'vartype': 'str',
                                'desc': 'filter by hostname',
                                'ol': 'n',
                            },
                            'virtual': {
                                'vartype': 'bool',
                                'desc': 'filter by physical/virtual',
                                'ol': 'V',
                            },
                            'physical': {
                                'vartype': 'bool',
                                'desc': 'filter by physical/virtual',
                                'ol': 'p',
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
                                'vartype': 'str',
                                'desc': 'filter by model',
                                'ol': 'm',
                            },
                            'manufacturer': {
                                'vartype': 'str',
                                'desc': 'filter by manufacturer',
                                'ol': 'M',
                            },
                            'realm': {
                                'vartype': 'str',
                                'desc': 'filter by realm',
                                'ol': 'r',
                            },
                            'site_id': {
                                'vartype': 'str',
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

        result = []

        if len(query.keys()) > self.metadata['methods']['lss']['optional_args']['max']:
            retval = "API_list_servers/lss: too many queries! max number of queries is: %s\n" % self.metadata['methods']['lss']['optional_args']['max']
            retval += "API_list_servers/lss: you tried to pass %s queries\n" % len(query.keys())
            self.cfg.log.debug(retval)
            raise ListServersError(retval)
        else:
            self.cfg.log.debug("API_list_servers/lss: num queries: %s" % len(query.keys()))
            self.cfg.log.debug("API_list_servers/lss: max num queries: %s" % self.metadata['methods']['lss']['optional_args']['max'])
        if len(query.keys()) < self.metadata['methods']['lss']['optional_args']['min']:
            retval = "API_list_servers/lss: too few queries! min number of queries is: %s\n" % self.metadata['methods']['lss']['optional_args']['min']
            retval += "API_list_servers/lss: you tried to pass %s queries\n" % len(query.keys())
            self.cfg.log.debug(retval)
            raise ListServersError(retval)
        else:
            self.cfg.log.debug("API_list_servers/lss: min num queries: %s" % self.metadata['methods']['lss']['optional_args']['min'])
        if 'physical' in query.keys() and 'virtual' in query.keys():
            self.cfg.log.debug("API_list_servers/lss: cannot specify both physical and virtual")
            raise ListServersError("cannot specify both physical and virtual")

        for key in query.keys():
            if key == 'all':
                result = self._get_all_servers()
            elif key == 'hostname':
                result = self._get_servers_by_hostname(query)
            elif key == 'physical':
                result = self._get_physical_servers()
            elif key == 'virtual':
                result = self._get_virtual_servers()
            elif key == 'hw_tag':
                result = self._get_servers_from_hw_tag(query)
            elif key == 'vlan':
                result = self._get_servers_from_vlan(query)
            elif key == 'site_id':
                result =  self._get_servers_from_site_id(query)
            elif key == 'tag':
                result =  self._get_servers_from_tag(query)
            elif key == 'realm':
                result = self._get_servers_from_realm(query)
            elif key == 'manufacturer':
                result = self._get_servers_from_manufacturer(query)
            elif key == 'model':
                result =  self._get_servers_from_model(query)
            elif key == 'cores':
                result = self._get_servers_from_cores(query)
            elif key == 'ram':
                result = self._get_servers_from_ram(query)
            elif key == 'disk':
                result = self._get_servers_from_disk(query)
        # send the result back up to the API layer 
        return result


    def _get_all_servers(self):
        """
        [description]
        retrieves and returns a list of all servers 

        [parameter info]
        none, just the self object

        [return value]
        a list containing the names of servers matching the filters
        """
        result = []
        self.cfg.log.debug("API_list_servers/lss: querying for ALL servers")
        try:
            for serv in self.cfg.dbsess.query(Server).order_by(Server.hostname):
                result.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
        except Exception, e:
            raise ListServersError("API_list_servers/lss: query failed for ALL servers. Error: %s" % e)
        return result

    def _get_servers_by_hostname(self, query):
        """
        [description]
        retrieves and returns a list of all servers matching "hostname"

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        a list containing the names of servers matching the filters
        """
        result = []
        self.cfg.log.debug("API_list_servers/lss: querying on name: %s" % query['hostname'])
        try:
            search_string = '%' + query['hostname'].split('.')[0] + '%'
            for serv in self.cfg.dbsess.query(Server).\
                    filter(Server.hostname.like(search_string)).\
                    order_by(Server.hostname):
                result.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
        except Exception, e:
            raise ListServersError("API_list_servers/lss: query failed for _get_servers_by_hostname. Error: %s" % e)
        return result

    def _get_physical_servers(self):
        """
        [description]
        retrieves and returns a list of all baremetal servers matching

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        a list containing the names of servers matching the filters
        """
        result = []
        self.cfg.log.debug("API_list_servers/lss: querying for physical (baremetal) servers")
        try:
            for serv in self.cfg.dbsess.query(Server).\
                    filter(Server.virtual==False).\
                    order_by(Server.hostname):
                result.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
        except Exception, e:
            raise ListServersError("API_list_servers/lss: query failed for _get_physical_servers. Error: %s" % e)
        return result

    def _get_virtual_servers(self):
        """
        [description]
        retrieves and returns a list of all virtual servers matching

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        a list containing the names of servers matching the filters
        """
        result = []
        self.cfg.log.debug("API_list_servers/lss: querying for virtual servers")
        try:
            for serv in self.cfg.dbsess.query(Server).\
                    filter(Server.virtual==True).\
                    order_by(Server.hostname):
                result.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
        except Exception, e:
            raise ListServersError("API_list_servers/lss: query failed for _get_virtual_servers. Error: %s" % e)
        return result

    def _get_servers_from_hw_tag(self, query):
        """
        [description]
        retrieves and returns a list of all servers with a particular hardware tag

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        a list containing the names of servers matching the filters
        """
        result = []
        self.cfg.log.debug("API_list_servers/lss: querying on hw_tag: %s" % query['hw_tag'])
        try:
            for serv in self.cfg.dbsess.query(Server).\
                    filter(Server.hw_tag==query['hw_tag']):
                result.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
        except Exception, e:
            raise ListServersError("API_list_servers/lss: query failed for _get_servers_from_hw_tag. Error: %s" % e)
        return result
    

    def _get_servers_from_vlan(self, query):
        """
        [description]
        retrieves and returns a list of all servers in a particular vlan

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        a list containing the names of servers matching the filters
        """
        result = []
        self.cfg.log.debug("API_list_servers/lss: querying on vlan: %s" % query['vlan'])
        try:
            # half-assed type checking, to ensure we don't pass a
            # non-int value and freak out the database
            vlan = int(query['vlan'])
            for serv, net in self.cfg.dbsess.query(Server, Network).\
                    filter(Network.ip!=None).\
                    filter(Network.vlan==vlan).\
                    filter(Server.id==Network.server_id).\
                    order_by(Server.hostname):
                result.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
        except Exception, e:
            raise ListServersError("API_list_servers/lss: query failed for _get_servers_from_vlan. Error: %s" % e)
        return result

    def _get_servers_from_site_id(self, query):
        """
        [description]
        retrieves and returns a list of all servers in a particular site_id 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        a list containing the names of servers matching the filters
        """
        result = []
        self.cfg.log.debug("API_list_servers/lss: querying on site_id: %s" % query['site_id'])
        try:
            for serv in self.cfg.dbsess.query(Server).\
                    filter(Server.site_id==query['site_id']).\
                    order_by(Server.hostname):
                result.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
        except Exception, e:
            raise ListServersError("API_list_servers/lss: query failed for _get_servers_from_site_id. Error: %s" % e)
        return result
    
    def _get_servers_from_tag(self, query):
        """
        [description]
        retrieves and returns a list of all servers with a particular tag

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        a list containing the names of servers matching the filters
        """
        self.cfg.log.debug("API_list_servers/lss: querying on tag: %s" % query['tag'])

        servers_primary = []
        servers_kv = []
        result = []
       
        try: 
            for server in self.cfg.dbsess.query(Server).\
                    filter(Server.tag==query['tag']).\
                    order_by(Server.hostname):
                servers_primary.append(server)
        
            qq = {'key': 'tag', 'value': query['tag']} 
            kvs = self.kvobj.collect(qq)
            for i in kvs:
                if i['key'] == "tag" and i['value'] == query['tag']:
                    servers_kv.append(i['hostname']+"."+i['realm']+"."+i['site_id'])
        
            if servers_primary:
                for serv in servers_primary:
                    result.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))

            if servers_kv:
                for serv in servers_kv:
                    result.append(serv)
        except Exception, e:
            raise ListServersError("API_list_servers/lss: query failed for _get_servers_from_tag. Error: %s" % e)
        return result
    
    def _get_servers_from_realm(self, query):
        """
        [description]
        retrieves and returns a list of all servers in a particular realm 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        a list containing the names of servers matching the filters
        """
        result = []
        self.cfg.log.debug("API_list_servers/lss: querying on realm: %s" % query['realm'])
        try:
            for serv in self.cfg.dbsess.query(Server).\
                    filter(Server.realm==query['realm']).\
                    order_by(Server.hostname):
                result.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
        except Exception, e:
            raise ListServersError("API_list_servers/lss: query failed for _get_servers_from_realm. Error: %s" % e)
        return result
    
    def _get_servers_from_manufacturer(self, query):
        """
        [description]
        retrieves and returns a list of all servers with a particular manufacturer 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        a list containing the names of servers matching the filters
        """
        self.cfg.log.debug("API_list_servers/lss: querying on manufacturer: %s" % query['manufacturer'])
        result = []
        try:
            search_string = '%' + query['manufacturer'] + '%'
            for serv, hw in self.cfg.dbsess.query(Server, Hardware).\
                    filter(Hardware.manufacturer.like(search_string)).\
                    filter(Server.hw_tag==Hardware.hw_tag).\
                    order_by(Server.hostname):
                result.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
        except Exception, e:
            raise ListServersError("API_list_servers/lss: query failed for _get_servers_from_manufacturer. Error: %s" % e)
        return result

    def _get_servers_from_model(self, query):
        """
        [description]
        retrieves and returns a list of all servers of a particular model type

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        a list containing the names of servers matching the filters
        """
        self.cfg.log.debug("API_list_servers/lss: querying on model: %s" % query['model'])
        result = []
        try:
            search_string = '%' + query['model']+ '%'
            for serv, hw in self.cfg.dbsess.query(Server, Hardware).\
                    filter(Hardware.model.like(search_string)).\
                    filter(Server.hw_tag==Hardware.hw_tag).\
                    order_by(Server.hostname):
                result.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
        except Exception, e:
            raise ListServersError("API_list_servers/lss: query failed for _get_servers_from_model. Error: %s" % e)
        return result

    def _get_servers_from_cores(self, query):
        """
        [description]
        retrieves and returns a list of all servers with a particular number of cores 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        a list containing the names of servers matching the filters
        """
        self.cfg.log.debug("API_list_servers/lss: querying on number of cores: %s" % query['cores'])
        result = []
        try:
            # half-assed type checking, to ensure we don't pass a
            # non-int value and freak out the database
            cores = int(query['cores'])
            for serv in self.cfg.dbsess.query(Server).\
                    filter(Server.cores==cores).\
                    order_by(Server.hostname):
                result.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
        except Exception, e:
            raise ListServersError("API_list_servers/lss: query failed for _get_servers_from_cores. Error: %s" % e)
        return result
    
    def _get_servers_from_ram(self, query):
        """
        [description]
        retrieves and returns a list of all servers with a particular amount of ram 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        a list containing the names of servers matching the filters
        """
        self.cfg.log.debug("API_list_servers/lss: querying on ram size in GB: %s" % query['ram'])
        result = []
        try:
            # half-assed type checking, to ensure we don't pass a
            # non-int value and freak out the database
            ram = int(query['ram'])
            for serv in self.cfg.dbsess.query(Server).\
                    filter(Server.ram==ram).\
                    order_by(Server.hostname):
                result.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
        except Exception, e:
            raise ListServersError("API_list_servers/lss: query failed for _get_servers_from_ram. Error: %s" % e)
        return result

    def _get_servers_from_disk(self, query):
        """
        [description]
        retrieves and returns a list of all servers with a particular amount of disk

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        a list containing the names of servers matching the filters
        """
        self.cfg.log.debug("API_list_servers/lss: querying on disk size in GB: %s" % query['disk'])
        result = []
        try:
            # half-assed type checking, to ensure we don't pass a
            # non-int value and freak out the database
            disk = int(query['disk'])
            for serv in self.cfg.dbsess.query(Server).\
                    filter(Server.disk==disk).\
                    order_by(Server.hostname):
                result.append("%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id))
        except Exception, e:
            raise ListServersError("API_list_servers/lss: query failed for _get_servers_from_disk. Error: %s" % e)
        return result
