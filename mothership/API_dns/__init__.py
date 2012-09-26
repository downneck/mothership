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

class DNSError(Exception):
    pass


class API_dns:

    def __init__(self, cfg):
        self.cfg = cfg
        self.common = MothershipCommon(cfg)
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
                'display': {
                    'description': 'displays dns data',
                    'short': 'd',
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
            },
        }


    def display(self, query):
        """
        [description]
        display stored/configured DNS data 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        returns a list of zones' information if successful, raises an error if not
        """
        # setting our valid query keys
        common = MothershipCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'display')
        try:
            # check for min/max number of optional arguments
            self.common.check_num_opt_args(query, self.namespace, 'display')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_dns/display: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise TagError("API_dns/display: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # actually doin stuff
            ret = []
            # first, if we have the "all" bit set in the query, we'll need to generate
            # a list of all possible realm.site_id.domain combinations and then display them
            if 'all' in query.keys():
                for site_id in self.cfg.site_ids:
                    for realm in self.cfg.realms:
                        zone = {}
                        zone['header'] = self.__generate_dns_header(realm, site_id)
                        records = self.__generate_primary_dns_records(realm, site_id)
                        zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                        ret.append(zone)
                        zone = {}
                        zone['header'] = self.__generate_dns_header(realm, site_id, mgmt=True)
                        records = self.__generate_mgmt_dns_records(realm, site_id)
                        zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                        ret.append(zone)
                        if self.cfg.drac:
                            zone = {}
                            zone['header'] = self.__generate_dns_header(realm, site_id, drac=True)
                            records = self.__generate_drac_dns_records(realm, site_id)
                            zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                            ret.append(zone)
            # otherwise, just do the one zone 
            elif 'unqn' in query.keys() and query['unqn']:
                # input validation for unqn 
                blank, realm, site_id = v_split_unqn(query['unqn'])
                v_realm(self.cfg, realm)
                v_site_id(self.cfg, site_id)
                zone = {}
                zone['header'] = self.__generate_dns_header(realm, site_id)
                records = self.__generate_primary_dns_records(realm, site_id)
                zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                ret.append(zone)
                zone = {}
                zone['header'] = self.__generate_dns_header(realm, site_id, mgmt=True)
                records = self.__generate_mgmt_dns_records(realm, site_id)
                zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                ret.append(zone)
                if self.cfg.drac:
                    zone = {}
                    zone['header'] = self.__generate_dns_header(realm, site_id, drac=True)
                    records = self.__generate_drac_dns_records(realm, site_id)
                    zone['records'] = self.common.multikeysort(records, ['type', 'host'])
                    ret.append(zone)
            # if nothing has blown up, return 
            return ret
        except Exception, e:
            self.cfg.log.debug("API_dns/display: error: %s" % e)
            raise DNSError("API_dns/display: error: %s" % e)

           
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

 
    def __generate_dns_header(self, realm, site_id, drac=None, mgmt=None):
        """
        [description]
        generates and returns header info for a dns zone 

        [parameter info]
        required:
            realm: the realm to generate for
            site_id: the site_id to generate for

        [return value]
        returns a dict of zone header info if successful, raises an error if not
        """
        try:
            zone = {}
            fqn = "%s.%s.%s" % (realm, site_id, self.cfg.domain)
            if drac and not mgmt:
                ffqn = "drac."+fqn
            elif mgmt and not drac:
                ffqn = "mgmt."+fqn
            elif not mgmt and not drac:
                ffqn = fqn
            else:
                self.cfg.log.debug("API_dns/__generate_dns_header: error in drac/mgmt selection") 
                raise DNSError("API_dns/__generate_dns_header: error in drac/mgmt selection") 
            zone['serial'] = int(time.time())
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
            return zone
        except Exception, e:
            self.cfg.log.debug("API_dns/__generate_dns_header: error: %s" % e)
            raise DNSError("API_dns/__generate_dns_header: error: %s" % e)


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
        returns a dict of zone header info if successful, raises an error if not
        """
        try:
            ret = []
            # dns addendum records
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
        returns a dict of zone header info if successful, raises an error if not
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
        returns a dict of zone header info if successful, raises an error if not
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
                if not n and self.cfg.drac:
                    self.cfg.log.debug("API_dns/__generate_drac_dns_records: no drac entries found in network table, but drac is enable in the configuration yaml. please rectify your configuration.")
                    raise DNSError(" no drac entries found in network table, but drac is enable in the configuration yaml. please rectify your configuration.")
                ret.append({'host': s.hostname, 'type': 'A', 'target': n.ip})
            return ret 
        except Exception, e:
            self.cfg.log.debug("API_dns/__generate_drac_dns_records: error: %s" % e)
            raise DNSError("API_dns/__generate_drac_dns_records: error: %s" % e)

    def generate_dns_output(cfg, domain, outdir, usecobbler=False):
        """
        Turns the dns_addendum table into usable zonefiles
        Optionally, will insert the zone into cobbler
        """
        head = []
        da = DnsAddendum
        check,tld = filter_domain_query(cfg.dbsess.query(da.realm,da.site_id), da, domain)
        if not outdir:
            if check.distinct().count() > 1:
                print 'More than one domain matches %s in mothership:' % domain
                count = 0
                selection = []
                for pair in check.distinct().all():
                    count += 1
                    print str(count) + ') %s.%s.' % pair + tld
                    selection.append('%s.%s.' % pair + tld)
                ans = raw_input('Please select the one you want to generate: ')
                if int(ans) < 1 or int(ans) > count:
                    print 'Generate DNS aborted.'
                    return
                else:
                    domain = selection[int(ans)-1]
        data,tld = filter_domain_query(cfg.dbsess.query(da), da, domain)
        data = data.order_by(da.site_id, da.realm, da.record_type, da.host).all()
        for dns in data:
            zone = '%s/%s.%s.%s' % (outdir, dns.realm, dns.site_id, tld)
            if '%s.%s' % (dns.realm,dns.site_id) not in head:
                head.append('%s.%s' % (dns.realm,dns.site_id))
                if outdir:
                    if usecobbler:
                        if os.path.exists(zone+'_header'):
                            print 'Using header: %s_header' % zone
                            shutil.copyfile(zone+'_header', zone)
                            print 'Updating %s/%s.%s.%s with dns_addendum table' \
                                % (outdir, dns.realm, dns.site_id, tld)
                            f=open(zone, 'a')
                        else:
                            print '\nFile does not exist: %s_header' % zone
                            print 'Using stdout instead:'
                            f=sys.stdout
                            f.write(__generate_dns_header('%s.%s.%s' \
                                % (dns.realm, dns.site_id, tld), cfg.contact))
                    else:
                        print 'Generating boilerplate header for %s/%s.%s.%s' \
                            % (outdir, dns.realm, dns.site_id, tld)
                        f=open(zone, 'w')
                        f.write(__generate_dns_header('%s.%s.%s' \
                            % (dns.realm, dns.site_id, tld), cfg.contact))
                        f=open(zone, 'a')
                else:
                    f=sys.stdout
                    f.write(__generate_dns_header('%s.%s.%s' \
                        % (dns.realm, dns.site_id, tld), cfg.contact))
            # if last octet of target is non-numerical and does not end with
            # period, add one
            target = dns.target
            if not re.search('\d+',dns.target.split('.')[-1]):
                if not target.endswith('.'):
                    target += '.'
            f.write("%-20s\tIN\t%-8s%-16s\n" % (dns.host, dns.record_type, target))
        if usecobbler:
            f.write("\n$host_record\n")
    
    def update_table_dnsaddendum(cfg, info, delete=False):
        """
        updates the dns_addendum table
        can be used to add or delete dns records
        """
        if not delete:
            data = cfg.dbsess.query(DnsAddendum).\
                filter(DnsAddendum.site_id==info['site_id']).\
                filter(DnsAddendum.realm==info['realm']).\
                filter(DnsAddendum.target==info['target']).\
                filter(DnsAddendum.record_type==info['record_type']).\
                filter(DnsAddendum.host==info['host']).all()
            if data:
                print 'The following already exist in the database'
                for d in data:
                    print '%d) %s IN %s %s' % (d.id, d.host, d.record_type, d.target)
                print 'Please delete first before adding again'
                return
            else:
                if len(info['target'].split('.')) < 4 and (info['record_type'] == 'A' or info['record_type'] == 'CNAME'):
                    print 'Target should end with ip or fqdn for A and CNAME types, aborting'
                    return
                cfg.dbconn.execute(DnsAddendum.__table__.insert(), [ info ])
        else:
            idlist = []
            print 'For %s.%s, we found:' % (info['realm'], info['site_id'])
            for d in cfg.dbsess.query(DnsAddendum).\
                filter(DnsAddendum.site_id==info['site_id']).\
                filter(DnsAddendum.realm==info['realm']).\
                filter(DnsAddendum.host==info['host']).all():
                idlist.append(d.id)
                print '%d) %s IN %s %s' % (d.id, d.host, d.record_type, d.target)
            if len(idlist) == 0:
                print '    no DNS entries for %s.%s.%s' % (info['host'],
                    info['realm'], info['site_id'])
            else:
                ans = raw_input('Which ID do you wish to delete? ')
                if int(ans) not in idlist:
                    print 'Delete DNS entry aborted.'
                    return
                else:
                    print 'Deleting DNS entry %d' % int(ans)
                    cfg.dbconn.execute(DnsAddendum.__table__.delete().\
                        where(DnsAddendum.id==int(ans)))
