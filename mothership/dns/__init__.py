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
import mothership.validate


def generate_dns_header(cfg, fqdn):
    """
    Returns zone header for fqdn
    """
    contact = cfg.contact
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

""" % (fqdn, fqdn, contact, serial, fqdn, fqdn)

def generate_dns_arecords(cfg, realm, site_id, domain):
    """
    Retrieves server list from mothership to create A records
    """
    alist = ''
    for s,n in cfg.dbsess.query(Server, Network).\
        filter(Network.server_id==Server.id).\
        filter(Network.site_id==site_id).\
        filter(Network.realm==realm).\
        order_by(Server.hostname).all():
        if n.ip:
            alist += '%-20s\tIN\t%-8s%-16s\n' % (s.hostname, 'A', n.ip)
    return alist

def generate_dns_addendum(cfg, realm, site_id, domain):
    """
    Turns the dns_addendum table into usable records
    """
    alist = ''
    for dns in cfg.dbsess.query(DnsAddendum).\
        filter(DnsAddendum.site_id==site_id).\
        filter(DnsAddendum.realm==realm).\
        order_by(DnsAddendum.record_type, DnsAddendum.host).all():
        target = dns.target
        if not re.search('\d+',dns.target.split('.')[-1]):
            if not target.endswith('.'):
                target += '.'
        alist += '%-20s\tIN\t%-8s%-16s\n' % (dns.host, dns.record_type, target)
    return alist

def generate_dns_output(cfg, domain, opts):
    """
    Creates the zonefile for the specified domain
    """
    fqn = mothership.validate.v_get_fqn(cfg, domain)
    sfqn = mothership.validate.v_split_fqn(fqn)
    forward = generate_dns_header(cfg, fqn)
    forward += generate_dns_arecords(cfg, *sfqn)
    forward += generate_dns_addendum(cfg, *sfqn)
    f = sys.stdout
    if opts.outdir:
        zone = '%s/%s' % (opts.outdir, fqn)
        f = open(zone, 'w')
    else:
        print '-'*60 + '\n\nDNS forward zone for %s:\n' % fqn  + '-'*60
    f.write(forward)
    if opts.outdir:
       f.close()

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
            if len(info['target'].split('.')) < 4 and \
                (info['record_type'] == 'A' or info['record_type'] == 'CNAME'):
                print 'Target should end with ip or fqdn for A and CNAME types, aborting'
                return
            data = DnsAddendum(info['host'], info['record_type'],
                info['realm'], info['site_id'], info['target'])
            cfg.dbsess.add(data)
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
            if not ans or int(ans) not in idlist:
                print 'Delete DNS entry aborted.'
                return
            else:
                print 'Deleting DNS entry %d' % int(ans)
                data = cfg.dbsess.query(DnsAddendum).\
                    filter(DnsAddendum.id==int(ans)).one()
                cfg.dbsess.delete(data)
    cfg.dbsess.commit()
