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
mothership.API_dns

module controlling various dns interactions
"""
import re
import os
import shutil
import sys
import time
from mothership.validate import *
from mothership.mothership_models import *
from mothership.common import *
from mothership.API_kv import *
from jinja2 import *
from netaddr import *

class DNSError(Exception):
    pass


class API_dns:

    def __init__(self, cfg):
        self.cfg = cfg
        self.common = MothershipCommon(cfg)
        self.kv = API_kv(cfg)
        self.version = 1
        self.namespace = 'API_dns'
        self.metadata = {
            'config': {
                'shortname': 'dns',
                'description': 'manipulates and generates DNS data',
                'module_dependencies': {
                    'mothership_models': 1,
                },
            },
            'methods': {
                'display_forward': {
                    'description': 'displays forward dns data',
                    'short': 'df',
                    'rest_type': 'GET',
                    'admin_only': False, 
                    'required_args': {
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 1,
                        'args': {
                            'unqn': {
                                'vartype': 'str',
                                'desc': 'unqualified name (realm.site_id) to display dns zonefile for',
                                'ol': 'u',
                            },
                            'all': {
                                'vartype': 'bool',
                                'desc': 'display dns zonefile(s) for ALL fqns in the system',
                                'ol': 'a',
                            },
                        },
                    },
                    'return': [
                        {
                            'header': {
                                'fqn': 'realm.site_id.domain.tld',
                                'contact': 'user_email.domain.tld',
                                'serial': 'int',
                                'refresh': 'int',
                                'retry': 'int',
                                'expire': 'int',
                                'ttl': 'int',
                                'ns': ['ns1.domain.tld', 'ns2.domain.tld',],
                                },
                            'records': [
                                {
                                    'host': 'str',
                                    'type': 'str',
                                    'target': 'str',
                                },
                                {
                                    'host': 'str',
                                    'type': 'str',
                                    'target': 'str',
                                },
                                {
                                    'host': 'str',
                                    'type': 'str',
                                    'target': 'str',
                                },
                            ],
                        }
                    ],
                },
                'write_forward': {
                    'description': 'writes forward dns data to disk on mothership master server',
                    'short': 'wf',
                    'rest_type': 'POST',
                    'admin_only': True, 
                    'required_args': {
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 1,
                        'args': {
                            'unqn': {
                                'vartype': 'str',
                                'desc': 'unqualified name (realm.site_id) to write dns zonefile for',
                                'ol': 'u',
                            },
                            'all': {
                                'vartype': 'bool',
                                'desc': 'write dns zonefile(s) for ALL fqns in the system',
                                'ol': 'a',
                            },
                        },
                    },
                    'return': { 
                        'string': 'success',
                    },
                },
                'display_reverse': {
                    'description': 'displays reverse dns data',
                    'short': 'dr',
                    'rest_type': 'GET',
                    'admin_only': False, 
                    'required_args': {
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 1,
                        'args': {
                            'ip': {
                                'vartype': 'str',
                                'desc': 'ip block to display reverse dns zonefile for',
                                'ol': 'i',
                            },
                            'all': {
                                'vartype': 'bool',
                                'desc': 'display dns zonefile(s) for ALL fqns in the system',
                                'ol': 'a',
                            },
                        },
                    },
                    'return': [
                        {
                            'header': {
                                'fqn': 'c.b.a.in-addr.arpa',
                                'contact': 'user_email.domain.tld',
                                'serial': 'int',
                                'refresh': 'int',
                                'retry': 'int',
                                'expire': 'int',
                                'ttl': 'int',
                                'ns': ['ns1.domain.tld', 'ns2.domain.tld',],
                                },
                            'records': [
                                {
                                    'd': 'int', # "d" octet in a.b.c.d ip format
                                    'type': 'str', # this should always be a PTR
                                    'target': 'str',
                                },
                                {
                                    'd': 'int', # "d" octet in a.b.c.d ip format
                                    'type': 'str', # this should always be a PTR
                                    'target': 'str',
                                },
                                {
                                    'd': 'int', # "d" octet in a.b.c.d ip format
                                    'type': 'str', # this should always be a PTR
                                    'target': 'str',
                                },
                            ],
                        }
                    ],
                },
                'write_reverse': {
                    'description': 'writes reverse dns data to disk on mothership master server',
                    'short': 'wr',
                    'rest_type': 'POST',
                    'admin_only': True, 
                    'required_args': {
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 1,
                        'args': {
                            'ip': {
                                'vartype': 'str',
                                'desc': 'ip block to write reverse dns zonefile for',
                                'ol': 'i',
                            },
                            'all': {
                                'vartype': 'bool',
                                'desc': 'write dns zonefile(s) for ALL fqns in the system',
                                'ol': 'a',
                            },
                        },
                    },
                    'return': { 
                        'string': 'success',
                    },
                },
                'add': {
                    'description': 'adds a record to the dns addendum table',
                    'short': 'a',
                    'rest_type': 'POST',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'unqdn': {
                                'vartype': 'str',
                                'desc': 'unqualified hostname (host.realm.site_id) to add record for',
                                'ol': 'u',
                            },
                            'record_type': {
                                'vartype': 'str',
                                'desc': 'record type to add (A, CNAME, TXT, MX, etc.)',
                                'ol': 'r',
                            },
                            'target': {
                                'vartype': 'str',
                                'desc': 'target for the record (ip address for A, fqdn for CNAME, etc.)',
                                'ol': 't',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': { 
                        'string': 'success',
                    },
                },
                'remove': {
                    'description': 'removes a record from the dns addendum table',
                    'short': 'r',
                    'rest_type': 'DELETE',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'unqdn': {
                                'vartype': 'str',
                                'desc': 'unqualified hostname (host.realm.site_id) to remove a record for',
                                'ol': 'u',
                            },
                            'record_type': {
                                'vartype': 'str',
                                'desc': 'record type to remove (A, CNAME, TXT, MX, etc.)',
                                'ol': 'r',
                            },
                            'target': {
                                'vartype': 'str',
                                'desc': 'target for the record to remove (ip address for A, fqdn for CNAME, etc.)',
                                'ol': 't',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': { 
                        'string': 'success',
                    },
                },
            },
        }


    def display_forward(self, query):
        """
        [description]
        display stored/configured forward DNS data 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        returns a list of zones' information if successful, raises an error if not
        """
        # setting our valid query keys
        common = MothershipCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'display_forward')
        try:
            # check for min/max number of optional arguments
            self.common.check_num_opt_args(query, self.namespace, 'display_forward')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_dns/display_forward: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise DNSError("API_dns/display_forward: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # actually doin stuff
            ret = []
            # first, if we have the "all" bit set in the query, we'll need to generate
            # a list of all possible realm.site_id.domain combinations and then display them
            if 'all' in query.keys():
                for site_id in self.cfg.site_ids:
                    for realm in self.cfg.realms:
                        zone = {}
                        zone['header'] = self.__generate_forward_dns_header(realm, site_id)
                        records = self.__generate_primary_dns_records(realm, site_id)
                        zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                        ret.append(zone)
                        zone = {}
                        zone['header'] = self.__generate_forward_dns_header(realm, site_id, mgmt=True)
                        records = self.__generate_mgmt_dns_records(realm, site_id)
                        zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                        ret.append(zone)
                        if self.cfg.drac:
                            zone = {}
                            zone['header'] = self.__generate_forward_dns_header(realm, site_id, drac=True)
                            records = self.__generate_drac_dns_records(realm, site_id)
                            zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                            ret.append(zone)
            # otherwise, just do the one zone 
            elif 'unqn' in query.keys() and query['unqn']:
                # input validation for unqn 
                special_vlan, realm, site_id = v_split_unqn(query['unqn'])
                v_realm(self.cfg, realm)
                v_site_id(self.cfg, site_id)
                zone = {}
                if not special_vlan:
                    zone['header'] = self.__generate_forward_dns_header(realm, site_id)
                    records = self.__generate_primary_dns_records(realm, site_id)
                    zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                    ret.append(zone)
                elif special_vlan == 'mgmt':
                    zone['header'] = self.__generate_forward_dns_header(realm, site_id, mgmt=True)
                    records = self.__generate_mgmt_dns_records(realm, site_id)
                    zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                    ret.append(zone)
                elif special_vlan == 'drac' and not self.cfg.drac:
                    self.cfg.log.debug("API_dns/display_forward: error: drac is not enabled!")
                    raise DNSError("API_dns/display_forward: error: drac is not enabled!")
                elif special_vlan == 'drac' and self.cfg.drac:
                    zone['header'] = self.__generate_forward_dns_header(realm, site_id, drac=True)
                    records = self.__generate_drac_dns_records(realm, site_id)
                    zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                    ret.append(zone)
            else:
                self.cfg.log.debug("API_dns/display_forward: error: malformed unqn")
                raise DNSError("API_dns/display_forward: error: malformed unqn")
            # if nothing has blown up, return 
            return ret
        except Exception, e:
            self.cfg.log.debug("API_dns/display_forward: error: %s" % e)
            raise DNSError("API_dns/display_forward: error: %s" % e)


    def write_forward(self, query):
        """
        [description]
        write stored/configured forward DNS data to disk

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        returns "success" if successful, raises an error if not
        """
        # setting our valid query keys
        common = MothershipCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'write_forward')
        try:
            # check for min/max number of optional arguments
            self.common.check_num_opt_args(query, self.namespace, 'write_forward')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_dns/write_forward: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise DNSError("API_dns/write_forward: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # actually doin stuff
            zonelist = []
            # first, if we have the "all" bit set in the query, we'll need to generate
            # a list of all possible realm.site_id.domain combinations and then write them
            if 'all' in query.keys():
                for site_id in self.cfg.site_ids:
                    for realm in self.cfg.realms:
                        zone = {}
                        zone['header'] = self.__generate_forward_dns_header(realm, site_id)
                        records = self.__generate_primary_dns_records(realm, site_id)
                        zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                        zonelist.append(zone)
                        zone = {}
                        zone['header'] = self.__generate_forward_dns_header(realm, site_id, mgmt=True)
                        records = self.__generate_mgmt_dns_records(realm, site_id)
                        zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                        zonelist.append(zone)
                        if self.cfg.drac:
                            zone = {}
                            zone['header'] = self.__generate_forward_dns_header(realm, site_id, drac=True)
                            records = self.__generate_drac_dns_records(realm, site_id)
                            zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                            zonelist.append(zone)
            # otherwise, just do the one zone 
            elif 'unqn' in query.keys() and query['unqn']:
                # input validation for unqn 
                special_vlan, realm, site_id = v_split_unqn(query['unqn'])
                v_realm(self.cfg, realm)
                v_site_id(self.cfg, site_id)
                zone = {}
                if not special_vlan:
                    zone['header'] = self.__generate_forward_dns_header(realm, site_id)
                    records = self.__generate_primary_dns_records(realm, site_id)
                    zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                    zonelist.append(zone)
                elif special_vlan == 'mgmt':
                    zone['header'] = self.__generate_forward_dns_header(realm, site_id, mgmt=True)
                    records = self.__generate_mgmt_dns_records(realm, site_id)
                    zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                    zonelist.append(zone)
                elif special_vlan == 'drac' and not self.cfg.drac:
                    self.cfg.log.debug("API_dns/write_forward: error: drac is not enabled!")
                    raise DNSError("API_dns/write_forward: error: drac is not enabled!")
                elif special_vlan == 'drac' and self.cfg.drac:
                    zone['header'] = self.__generate_forward_dns_header(realm, site_id, drac=True)
                    records = self.__generate_drac_dns_records(realm, site_id)
                    zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                    zonelist.append(zone)
            else:
                self.cfg.log.debug("API_dns/write_forward: error: malformed unqn")
                raise DNSError("API_dns/write_forward: error: malformed unqn")
            # ensure our zone directory exists
            if not os.path.exists(self.cfg.zonedir):
                raise DNSError("API_dns/write_forward: error, zone directory does not exist: %s" % self.cfg.zonedir)
                self.cfg.log.debug("API_dns/write_forward: error, zone directory does not exist: %s" % self.cfg.zonedir)
            # write a file for each zone
            for zone in zonelist:
                responsedata = {'data': [zone]}
                zfname = self.cfg.zonedir+'/'+zone['header']['fqn']
                zf = open(zfname, 'w')
                env = Environment(loader=FileSystemLoader('mothership/'+self.namespace))
                try:
                    # try to load up a template called template.cmdln.write_forward
                    # this allows us to format output specifically to this call
                    template = env.get_template("template.cmdln.write_forward")
                    zf.write(template.render(r=responsedata))
                except TemplateNotFound:
                    # template.cmdln.write_forward apparently doesn't exist. load the default template
                    template = env.get_template('template.cmdln')
                    zf.write(template.render(r=responsedata))
                except:
                    self.cfg.log.debug("API_dns/write_forward: error, no template found. refusing to write dns zonefiles")
                    raise DNSError("API_dns/write_forward: error, no template found. refusing to write dns zonefiles")
            # if nothing has blown up, return
            return "success" 
        except Exception, e:
            self.cfg.log.debug("API_dns/write_forward: error: %s" % e)
            raise DNSError("API_dns/write_forward: error: %s" % e)


    def display_reverse(self, query):
        """
        [description]
        display stored/configured reverse DNS data 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        returns a list of zones' information if successful, raises an error if not
        """
        # setting our valid query keys
        common = MothershipCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'display_reverse')
        try:
            # check for min/max number of optional arguments
            self.common.check_num_opt_args(query, self.namespace, 'display_reverse')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_dns/display_reverse: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise DNSError("API_dns/display_reverse: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # actually doin stuff
            ret = []
            # if we have the "all" bit set in the query, we'll need to iterate through all configured networks
            if 'all' in query.keys():
                for net in self.cfg.network_map:
                    zone = {}
                    zone['header'] = self.__generate_reverse_dns_header(net)
                    zone['records'] = self.__generate_reverse_dns_records(net)
                    ret.append(zone)
            # otherwise, just do the one network
            elif 'ip' in query.keys() and query['ip']:
                for net in self.cfg.network_map:
                    if IPAddress(query['ip']) in list(IPNetwork(net['cidr'])):
                        zone = {}
                        zone['header'] = self.__generate_reverse_dns_header(net)
                        zone['records'] = self.__generate_reverse_dns_records(net)
                        ret.append(zone)
                        break
            # if nothing has blown up, return 
            return ret
        except Exception, e:
            self.cfg.log.debug("API_dns/display_reverse: error: %s" % e)
            raise DNSError("API_dns/display_reverse: error: %s" % e)


    def write_reverse(self, query):
        """
        [description]
        write stored/configured reverse DNS data to disk

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        returns "success" if successful, raises an error if not
        """
        # setting our valid query keys
        common = MothershipCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'write_reverse')
        try:
            # check for min/max number of optional arguments
            self.common.check_num_opt_args(query, self.namespace, 'write_reverse')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_dns/write_reverse: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise DNSError("API_dns/write_reverse: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # actually doin stuff
            zonelist = []
            # if we have the "all" bit set in the query, we'll need to iterate through all configured networks
            if 'all' in query.keys():
                for net in self.cfg.network_map:
                    zone = {}
                    zone['header'] = self.__generate_reverse_dns_header(net)
                    zone['records'] = self.__generate_reverse_dns_records(net)
                    zonelist.append(zone)
            # otherwise, just do the one network
            elif 'ip' in query.keys() and query['ip']:
                for net in self.cfg.network_map:
                    if IPAddress(query['ip']) in list(IPNetwork(net['cidr'])):
                        zone = {}
                        zone['header'] = self.__generate_reverse_dns_header(net)
                        zone['records'] = self.__generate_reverse_dns_records(net)
                        zonelist.append(zone)
                        break
            # ensure our zone directory exists
            if not os.path.exists(self.cfg.zonedir):
                raise DNSError("API_dns/write_reverse: error, zone directory does not exist: %s" % self.cfg.zonedir)
                self.cfg.log.debug("API_dns/write_reverse: error, zone directory does not exist: %s" % self.cfg.zonedir)
            # write a file for each zone
            for zone in zonelist:
                responsedata = {'data': [zone]}
                zfname = self.cfg.zonedir+'/'+zone['header']['fqn']
                zf = open(zfname, 'w')
                env = Environment(loader=FileSystemLoader('mothership/'+self.namespace))
                try:
                    # try to load up a template called template.cmdln.write_reverse
                    # this allows us to format output specifically to this call
                    template = env.get_template("template.cmdln.write_reverse")
                    zf.write(template.render(r=responsedata))
                except TemplateNotFound:
                    # template.cmdln.write_reverse apparently doesn't exist. load the default template
                    template = env.get_template('template.cmdln')
                    zf.write(template.render(r=responsedata))
                except:
                    self.cfg.log.debug("API_dns/write_reverse: error, no template found. refusing to write dns zonefiles")
                    raise DNSError("API_dns/write_reverse: error, no template found. refusing to write dns zonefiles")
            # if nothing has blown up, return
            return "success" 
        except Exception, e:
            self.cfg.log.debug("API_dns/write_reverse: error: %s" % e)
            raise DNSError("API_dns/write_reverse: error: %s" % e)


    def add(self, query):
        """
        [description]
        add a record to the DNS addendum 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        returns 'success' if successful, raises an error if not
        """
        # setting our valid query keys
        common = MothershipCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'add')
        try:
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_dns/add: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise DNSError("API_dns/add: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # actually doin stuff
            #
            # translate the unqdn
            host, realm, site_id = v_split_unqn(query['unqdn'])
            # let's see if this thing exists already...
            data = self.cfg.dbsess.query(DnsAddendum).\
              filter(DnsAddendum.site_id==site_id).\
              filter(DnsAddendum.realm==realm).\
              filter(DnsAddendum.target==query['target']).\
              filter(DnsAddendum.record_type==query['record_type']).\
              filter(DnsAddendum.host==host).all()
            if data:
                self.cfg.log.debug("API_dns/add: error: record exists already")
                raise DNSError("API_dns/add: error: record exists already")
            # input sanitization for targets
            # target = ip address
            if query['record_type'] == "A":
                IPAddress(query['target']) 
            # target = fqdn
            elif query['record_type'] == ("CNAME" or "MX" or "NS"):
                domregex = re.compile('^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$')
                for word in query['target'].split('.'):
                    if not domregex.match(word):
                        self.cfg.log.debug("API_dns/add: error: malformed CNAME target: %s" % query['target'])
                        raise DNSError("API_dns/add: error: malformed CNAME target: %s" % query['target'])
            # target = one of the MANY other resource record types 
            else:
                pass
            # add the record
            newrec = DnsAddendum(host, query['record_type'], realm, site_id, query['target'])
            self.cfg.dbsess.add(newrec)
            self.cfg.dbsess.commit()
            # if nothing has blown up, return
            return "success"
        except Exception, e:
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_dns/add: error: %s" % e)
            raise DNSError("API_dns/add: error: %s" % e)


    def remove(self, query):
        """
        [description]
        remove a record from the DNS addendum 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        returns 'success' if successful, raises an error if not
        """
        # setting our valid query keys
        common = MothershipCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'remove')
        try:
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_dns/remove: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise DNSError("API_dns/remove: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # actually doin stuff
            #
            # translate the unqdn
            host, realm, site_id = v_split_unqn(query['unqdn'])
            # let's see if this thing exists
            data = self.cfg.dbsess.query(DnsAddendum).\
              filter(DnsAddendum.site_id==site_id).\
              filter(DnsAddendum.realm==realm).\
              filter(DnsAddendum.target==query['target']).\
              filter(DnsAddendum.record_type==query['record_type']).\
              filter(DnsAddendum.host==host).first()
            if not data:
                self.cfg.log.debug("API_dns/remove: error: record does not exist")
                raise DNSError("API_dns/remove: error: record does not exist")
            else:
                self.cfg.dbsess.delete(data)
                self.cfg.dbsess.commit()
            # if nothing has blown up, return
            return "success"
        except Exception, e:
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_dns/remove: error: %s" % e)
            raise DNSError("API_dns/remove: error: %s" % e)


       
    ####################
    # internal methods #
    ####################

    # do we need this thing? investigate
    #def __filter_domain_query(query, table, domain):
    #    """
    #    [description]
    #    display stored/configured DNS data 
    #
    #    [parameter info]
    #    required:
    #        query: the query dict being passed to us from the called URI
    #
    #    [return value]
    #    returns a dict of information if successful, raises an error if not
    #    """
    #    try:
    #        sub = domain.split('.')
    #        if len(sub) >= 4:
    #            query = query.filter(table.realm==sub[-4:-3][0])
    #        if len(sub) >= 3:
    #            query = query.filter(table.site_id==sub[-3:-2][0])
    #        return query, '.'.join(sub[-2:])
    #    except Exception, e:
    #        self.cfg.log.debug("API_dns/__filter_domain_query: error: %s" % e)
    #        raise DNSError("API_dns/__filter_domain_query: error: %s" % e)

 
    def __generate_forward_dns_header(self, realm, site_id, drac=None, mgmt=None):
        """
        [description]
        generates and returns header info for a dns zone 

        [parameter info]
        required:
            realm: the realm to generate for
            site_id: the site_id to generate for
            drac: boolean, whether to generate the drac version of the zone header
            mgmt: boolean, whether to generate the mgmt version of the zone header

        [return value]
        returns a dict of zone header info if successful, raises an error if not
        """
        try:
            zone = {}
            # construct our fqn: realm.site.domain.tld
            unqn = "%s.%s" % (realm, site_id)
            fqn = "%s.%s" % (unqn, self.cfg.domain)
            # figure out if we should write a normal header, drac header, or mgmt header
            if drac and not mgmt:
                ffqn = "drac."+fqn
            elif mgmt and not drac:
                ffqn = "mgmt."+fqn
            elif not mgmt and not drac:
                ffqn = fqn
            else:
                self.cfg.log.debug("API_dns/__generate_forward_dns_header: error in drac/mgmt selection") 
                raise DNSError("API_dns/__generate_forward_dns_header: error in drac/mgmt selection")
            # populate our zone dict with relevant info
            #
            # this uses unix epoch timestamp as a serial. max length for
            # a positive signed 32-bit int is 2147483647, which means
            # the epoch timestamp will be too big after: Tuesday, 19 Jan 2038
            # so i added a bit of math to give us some room. subtracting
            # 1352700000 from epoch time gives us roughly another 42.8 years
            # at which point, we can just jack the number up higher i suppose.
            #
            # let's make sure to revisit sometime before 2080. maybe there will be
            # a better way to do this. maybe there will be hovercars.
            zone['serial'] = int(time.time()) - 1352700000
            if '@' in self.cfg.contact:
                zone['contact'] = self.cfg.contact.replace('@','.')
            else:
                zone['contact'] = self.cfg.contact
            zone['refresh'] = self.cfg.dns_refresh
            zone['retry'] = self.cfg.dns_retry
            zone['expire'] = self.cfg.dns_expire
            zone['ttl'] = self.cfg.dns_ttl
            zone['ns'] = ["ns1.%s" % fqn, "ns2.%s" % fqn]
            zone['fqn'] = ffqn
            # if we have some data, return it
            if zone:
                return zone
        except Exception, e:
            self.cfg.log.debug("API_dns/__generate_forward_dns_header: error: %s" % e)
            raise DNSError("API_dns/__generate_forward_dns_header: error: %s" % e)


    def __generate_reverse_dns_header(self, net):
        """
        [description]
        generates and returns header info for a dns zone 

        [parameter info]
        required:
            arpa: c.b.a.in-addr.arpa to generate for
            unqn: the [""|"mgmt"|"drac"].realm.site_id associated with the arpa block

        [return value]
        returns a dict of zone header info if successful, raises an error if not
        """
        try:
            block, size = net['cidr'].split('/')
            arpa = '%s.in-addr.arpa' % '.'.join(reversed(block.rpartition('.')[0].split('.')))
            zone = {}
            if len(net['dom'].split('.')) > 2:
                discard, nsunqn = net['dom'].split('.', 1)
            else:
                nsunqn = net['dom']
            nsunqn = "%s.%s" % (nsunqn, self.cfg.domain)
            # populate our zone dict with relevant info
            zone['serial'] = int(time.time())
            if '@' in self.cfg.contact:
                zone['contact'] = self.cfg.contact.replace('@','.')
            else:
                zone['contact'] = self.cfg.contact
            zone['refresh'] = self.cfg.dns_refresh
            zone['retry'] = self.cfg.dns_retry
            zone['expire'] = self.cfg.dns_expire
            zone['ttl'] = self.cfg.dns_ttl
            zone['ns'] = ["ns1.%s" % nsunqn, "ns2.%s" % nsunqn]
            zone['fqn'] = arpa 
            # if we have some data, return it
            if zone:
                return zone
        except Exception, e:
            self.cfg.log.debug("API_dns/__generate_reverse_dns_header: error: %s" % e)
            raise DNSError("API_dns/__generate_reverse_dns_header: error: %s" % e)


    def __generate_primary_dns_records(self, realm, site_id):
        """
        [description]
        generates and returns record info for a dns zone based on the primary interface
        (drac and mgmt are done separately)

        [parameter info]
        required:
            realm: the realm to generate for
            site_id: the site_id to generate for

        [return value]
        returns a dict of zone info if successful, raises an error if not
        """
        try:
            ret = []
            # gather dns addendum records
            for a in self.cfg.dbsess.query(DnsAddendum).\
                     filter(DnsAddendum.realm==realm).\
                     filter(DnsAddendum.site_id==site_id).all():
                ret.append({'host': a.host, 'type': a.record_type, 'target': a.target})
            # server table records, primary interface
            for s in self.cfg.dbsess.query(Server).\
                     filter(Server.realm==realm).\
                     filter(Server.site_id==site_id).all():
                n = self.cfg.dbsess.query(Network).\
                    filter(Network.server_id==s.id).\
                    filter(Network.interface==self.cfg.primary_interface).first()
                ret.append({'host': s.hostname, 'type': 'A', 'target': n.ip})
            # if we have some data, return it
            return ret 
        except Exception, e:
            self.cfg.log.debug("API_dns/__generate_primary_dns_records: error: %s" % e)
            raise DNSError("API_dns/__generate_primary_dns_records: error: %s" % e)


    def __generate_mgmt_dns_records(self, realm, site_id):
        """
        [description]
        generates and returns record info for a dns zone based on the mgmt interface 

        [parameter info]
        required:
            realm: the realm to generate for
            site_id: the site_id to generate for

        [return value]
        returns a list of mgmt record info if successful, raises an error if not
        """
        try:
            ret = []
            # server table records, mgmt interface
            for s in self.cfg.dbsess.query(Server).\
                     filter(Server.realm==realm).\
                     filter(Server.site_id==site_id).all():
                n = self.cfg.dbsess.query(Network).\
                    filter(Network.server_id==s.id).\
                    filter(Network.interface==self.cfg.mgmt_vlan_interface).first()
                ret.append({'host': s.hostname, 'type': 'A', 'target': n.ip})
            # if we have some data, return it
            return ret 
        except Exception, e:
            self.cfg.log.debug("API_dns/__generate_mgmt_dns_records: error: %s" % e)
            raise DNSError("API_dns/__generate_mgmt_dns_records: error: %s" % e)


    def __generate_drac_dns_records(self, realm, site_id):
        """
        [description]
        generates and returns record info for a dns zone based on the drac interface

        [parameter info]
        required:
            realm: the realm to generate for
            site_id: the site_id to generate for

        [return value]
        returns a list of drac record info if successful, raises an error if not
        """
        try:
            ret = []
            # server table records, drac interface
            for s in self.cfg.dbsess.query(Server).\
                     filter(Server.realm==realm).\
                     filter(Server.site_id==site_id).all():
                n = self.cfg.dbsess.query(Network).\
                    filter(Network.server_id==s.id).\
                    filter(Network.interface=='drac').first()
                # just in case someone tries to be funny and turn on drac support
                # without putting drac network entires in the network table
                if not n and self.cfg.drac:
                    self.cfg.log.debug("API_dns/__generate_drac_dns_records: no drac entries found in network table, but drac is enable in the configuration yaml. please rectify your configuration.")
                    raise DNSError(" no drac entries found in network table, but drac is enable in the configuration yaml. please rectify your configuration.")
                ret.append({'host': s.hostname, 'type': 'A', 'target': n.ip})
            # if we have some data, return it
            return ret 
        except Exception, e:
            self.cfg.log.debug("API_dns/__generate_drac_dns_records: error: %s" % e)
            raise DNSError("API_dns/__generate_drac_dns_records: error: %s" % e)


    def __generate_reverse_dns_records(self, net):
        """
        [description]
        generates and returns record info for a reverse dns zone based on the ip block

        [parameter info]
        required:
            cidr_block: the netblock to generate for (cidr notation, ie. a.b.c.d/16)
            unqn: the unqn associated with that netblock

        [return value]
        returns a dict of zone info if successful, raises an error if not
        """
        try:
            fqn = ".%s.%s." % (net['dom'], self.cfg.domain)
            ret = []
            for ip in IPNetwork(net['cidr']):
                n = None
                s = None
                last_octet = str(ip).rsplit('.', 1)[1]
                # look up server records by ip
                n = self.cfg.dbsess.query(Network).filter(Network.ip==str(ip)).first()
                if n:
                    s = self.cfg.dbsess.query(Server).filter(Server.id==n.server_id).first()
                    if s:
                        ret.append({'host': last_octet, 'type': 'PTR', 'target': s.hostname+fqn})
            # if we have some data, return it
            return ret 
        except Exception, e:
            self.cfg.log.debug("API_dns/__generate_reverse_dns_records: error: %s" % e)
            raise DNSError("API_dns/__generate_reverse_dns_records: error: %s" % e)
