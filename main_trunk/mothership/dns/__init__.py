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
various dns operations
"""

# import some useful stuff
import re
import os
import shutil
import sys
import time
from mothership.mothership_models import *


def filter_domain_query(query, table, domain):
    sub = domain.split('.')
    if len(sub) >= 4:
        query = query.filter(table.realm==sub[-4:-3][0])
    if len(sub) >= 3:
        query = query.filter(table.site_id==sub[-3:-2][0])
    return query, '.'.join(sub[-2:])

def generate_dns_header(domainname, contact):
    """Prints out a DNS Zone header for domainname"""
    serial = int(time.time())
    if '@' in contact: contact = contact.replace('@','.')
    return """
$ORIGIN %s.
$TTL 86400
@                       IN      SOA     %s. %s. (
                                        %s   ; Serial
                                        21600        ; Refresh
                                        3600         ; Retry
                                        604800       ; Expire
                                        86400        ; TTL
                                        )

                        IN      NS      ns1.%s.
                        IN      NS      ns2.%s.

""" % (domainname, domainname, contact, serial, domainname, domainname)

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
                        f.write(generate_dns_header('%s.%s.%s' \
                            % (dns.realm, dns.site_id, tld), cfg.contact))
                else:
                    print 'Generating boilerplate header for %s/%s.%s.%s' \
                        % (outdir, dns.realm, dns.site_id, tld)
                    f=open(zone, 'w')
                    f.write(generate_dns_header('%s.%s.%s' \
                        % (dns.realm, dns.site_id, tld), cfg.contact))
                    f=open(zone, 'a')
            else:
                f=sys.stdout
                f.write(generate_dns_header('%s.%s.%s' \
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
