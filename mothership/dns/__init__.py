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
import difflib
import mothership.kv
import mothership.validate
import mothership.network_mapper
from mothership.mothership_models import *


class DNSError(Exception):
    pass

def generate_dns_header(cfg, fqdn, realm, site_id, domain):
    """
    Returns zone header for fqdn
    """
    contact = cfg.contact
    serial = int(time.time())
    if '@' in contact: contact = contact.replace('@','.')
    header = """
$ORIGIN %s.
$TTL %s
@                       IN      SOA     %s. %s. (
                                        %s   ; Serial
                                        21600        ; Refresh
                                        3600         ; Retry
                                        604800       ; Expire
                                        %-5d        ; TTL
                                        )

""" % (fqdn, cfg.dns_ttl, fqdn, contact, serial, cfg.dns_ttl)
    key = 'nameservers'
    ns = mothership.kv.collect(cfg, realm+'.'+site_id, key)
    if not ns:
        raise DNSError('''
No nameservers defined for %s.%s or %s, use:
    ship kv -a %s.%s nameservers=<ns1>[,<nsN>]
to configure one or more nameservers
''' % (realm, site_id, domain, realm, site_id))
    for n in ns:
        slist = n.value.split(',')
        if n.hostname == realm+'.'+site_id:
            continue
    nlist = ''
    for server in slist:
        nlist += '%-20s\tIN\t%-8s%-16s\n' % ('', 'NS', server)
    header += nlist
    return header

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

def generate_dns_arpa(cfg, cidr, fqdn, realm, site_id, domain):
    """
    Retrieves server list from mothership to create arpa records
    """
    net = mothership.network_mapper.get_network(cidr)
    num = 0
    while re.search('\.0+$', net):
        net = re.sub('\.0+$', '', net)
        num += 1
    alist = ''
    for s,n in cfg.dbsess.query(Server, Network).\
        filter(Network.server_id==Server.id).\
        filter(Network.site_id==site_id).\
        filter(Network.realm==realm).\
        order_by(Network.ip).all():
        if mothership.network_mapper.within(n.ip, cidr):
            alist += '%-20s\tIN\t%-8s%s.%s.\n' % (
                '.'.join(reversed(n.ip.split('.')[-num:])),
                'PTR', s.hostname, fqdn)
    return net, alist

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
    Creates DNS zonefiles
    """
    tmpdir = '/tmp'
    tmpzones = []
    if opts.system:
        opts.outdir = tmpdir + cfg.dns_zone
    if opts.outdir:
        if not os.path.exists(opts.outdir):
            os.makedirs(opts.outdir)
    if opts.all:
        print 'Generating ALL mothership DNS files'
        for site_id in cfg.site_ids:
            for realm in cfg.realms:
                fqn = mothership.validate.v_get_fqn(cfg, realm+'.'+site_id)
                zone = generate_dns_forward(cfg, fqn, opts)
                if zone: tmpzones.append(zone)
                zone = generate_dns_reverse(cfg, fqn, opts)
                if zone: tmpzones.append(zone)
    elif opts.reverse:
        zone = generate_dns_reverse(cfg, domain, opts)
        if zone: tmpzones.append(zone)
    else:
        zone = generate_dns_forward(cfg, domain, opts)
        if zone: tmpzones.append(zone)
    if opts.system:
        for zone in tmpzones:
            print 'Diff %s %s' % (zone, re.sub('^'+tmpdir, '', zone))
            tempdata = open(zone).read().split('\n')
            livedata = open(re.sub('^'+tmpdir, '', zone)).read().split('\n')
            print '\n'.join(difflib.Differ().compare(tempdata, livedata))

def generate_dns_forward(cfg, domain, opts):
    """
    Creates the forward zonefile for the specified domain
    """
    fqn = mothership.validate.v_get_fqn(cfg, domain)
    sfqn = mothership.validate.v_split_fqn(fqn)
    forward = generate_dns_header(cfg, fqn, *sfqn)
    forward += generate_dns_arecords(cfg, *sfqn)
    forward += generate_dns_addendum(cfg, *sfqn)
    f = sys.stdout
    if opts.outdir:
        zone = '%s/%s' % (opts.outdir, fqn)
        print 'Writing DNS forward zone for %s to %s' % (fqn, zone)
        f = open(zone, 'w')
    else:
        print '\n' + '-'*60 + '\nDNS forward zone for %s:\n' % fqn  + '-'*60
    f.write(forward)
    if opts.outdir:
       f.close()
       return zone
    return None

def generate_dns_reverse(cfg, domain, opts):
    """
    Creates the reverse zonefile for the specified domain
    """
    fqn = mothership.validate.v_get_fqn(cfg, domain)
    sfqn = mothership.validate.v_split_fqn(fqn)
    cidr = mothership.network_mapper.remap(cfg, 'cidr', domain=fqn)
    net, rev = generate_dns_arpa(cfg, cidr, fqn, *sfqn)
    reverse = generate_dns_header(cfg, fqn, *sfqn)
    reverse += rev
    f = sys.stdout
    if opts.outdir:
        zone = '%s/%s' % (opts.outdir, net)
        print 'Writing DNS reverse zone for %s to %s' % (net, zone)
        f = open(zone, 'w')
    else:
        print '\n' + '-'*60 + '\nDNS reverse zone for %s:\n' % net  + '-'*60
    f.write(reverse)
    if opts.outdir:
       f.close()
       return zone
    return None

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
