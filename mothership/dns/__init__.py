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
import sys
import time
import shutil
import difflib
import datetime
import mothership.kv
import mothership.validate
import mothership.network_mapper
from mothership.mothership_models import *


class DNSError(Exception):
    pass

def generate_dns_header(cfg, origin, fqdn, realm, site_id, domain):
    """
    Returns zone header for fqdn
    """
    contact = cfg.contact
    serial = int(time.time())
    # try to get a realm-specific master
    nsmaster = mothership.kv.select(cfg, realm+'.'+site_id, key='nsmaster')
    if not nsmaster:
        # if we can't get a realm-specific master, look for a global one
        nsmaster = mothership.kv.select(cfg, None, key='nsmaster')
        if not nsmaster:
            raise DNSError("No nsmaster KV entry for \"%s.%s\", exiting" % (realm, site_id))
    nsmaster = nsmaster.value
    if '@' in contact: contact = contact.replace('@','.')
    if origin:
        header = '$ORIGIN %s.' % fqdn
    else:
        header = ''
    header += """
$TTL %s
@                       IN      SOA     %s. %s. (
                                        %-10d   ; Serial
                                        %-10d   ; Refresh
                                        %-10d   ; Retry
                                        %-10d   ; Expire
                                        %-10d   ; TTL
                                        )

""" % (cfg.zonettl, nsmaster, contact, serial, cfg.dns_refresh,
        cfg.dns_retry, cfg.dns_expire, cfg.zonettl)
    for rec in ['ns', 'mx']:
        header += generate_root_records(cfg, realm+'.'+site_id, domain, rec)
    return header

def generate_root_records(cfg, unqdn, domain, key):
    rec = mothership.kv.collect(cfg, unqdn, key)
    if not rec:
        raise DNSError('''
No %s defined for %s or %s, use:
    ship kv -a %s %s=<ns1>[,<nsN>]
to configure one or more %s
''' % (key, unqdn, domain, unqdn, key, key))
    for r in rec:
        slist = r.value.split(',')
        if r.hostname == unqdn:
            continue
    records = ''
    for server in slist:
        records += '%-20s\tIN\t%-8s%-16s\n' % ('', key.upper(), server)
    return records

def generate_dns_arecords(cfg, realm, site_id, domain):
    """
    Retrieves server list from mothership to create A records
    """
    alist = ''
    for n in cfg.dbsess.query(Network).\
        filter(Network.site_id==site_id).\
        filter(Network.realm==realm).all():
            if n.server_id:
                s = cfg.dbsess.query(Server).\
                    filter(Server.id==n.server_id).first()
                if n.ip and s.hostname:
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
    for n in cfg.dbsess.query(Network).\
        filter(Network.site_id==site_id).\
        filter(Network.realm==realm).\
        order_by(Network.ip).all():
        if n.server_id:
            s = cfg.dbsess.query(Server).\
                    filter(Server.id==n.server_id).first()
            if mothership.network_mapper.within(n.ip, cidr) and n.ip and s.hostname:
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
        if dns and dns.target:
            target = dns.target
        else:
            raise DNSError("Addendum record does not exist: %s" % realm+"."+site_id+"."+domain)
        if not re.search('\d+',dns.target.split('.')[-1]):
            if not target.endswith('.'):
                target += '.'
        alist += '%-20s\tIN\t%-8s%-16s\n' % (dns.host, dns.record_type, target)
    return alist

def generate_dns_output(cfg, domain, opts):
    """
    Creates DNS zonefiles
    """
    tmpdir = cfg.dns_tmpdir 
    # not necessary, see below
    #reload = False
    zones = []
    if opts.system:
        opts.outdir = tmpdir + cfg.zonedir
    if opts.outdir:
        if not os.path.exists(opts.outdir):
            os.makedirs(opts.outdir)
    if opts.all:
        print 'Generating ALL mothership DNS files'
        for site_id in cfg.site_ids:
            for realm in cfg.realms:
                fqn = mothership.validate.v_get_fqn(cfg, realm+'.'+site_id)
                zones.append(generate_dns_forward(cfg, fqn, opts))
                revzones = generate_dns_reverse(cfg, fqn, opts)
                if revzones:
                    for revzone in revzones:
                        zones.append(revzone)
                else: 
                    print "No reverse zones created for %s" % (realm+'.'+site_id)
    else:
        zones.append(generate_dns_forward(cfg, domain, opts))
        revzones = generate_dns_reverse(cfg, domain, opts)
        if revzones:
            for revzone in revzones:
                zones.append(revzone)
        else: 
            print "No ouput directory has been specified, so no reverse zone files were written for %s" % domain
    if opts.system:
        # this is horribad. it only generates a zones.conf for ONE ZONE
        # unless you specify the -a option. i'm ripping this out and managing
        # the zones.conf in puppet. let's fix this crap in the rewrite -dk
        # --- BEGIN AWFULNESS ---
        #validated = validate_zone_config(cfg, tmpdir, zones)
        #reload = reload or validated
        # --- END AWFULNESS ---

        # Remove empty zones
        zones = [ z for z in zones if z ]
        validate_zone_files(cfg, tmpdir, zones)
        if opts.all:
            validate_zone_config(cfg, tmpdir, zones)
        # mothership shouldn't be restarting system services. again, horribad.
        # removing this crap and replacing it with an informational message. -dk
        # --- BEGIN AWFULNESS ---
        #validated = validate_zone_files(tmpdir, zones)
        #if reload or validated:
        #    try:
        #        print 'Reloading named...',
        #        os.system('/sbin/service named reload')
        #        print 'done'
        #    except:
        #        raise DNSError('Error reloading named!')
        # --- END AWFULNESS ---
        print "All zones validated. Please restart named so the changes can take effect."

def validate_zone_files(cfg, prefix, tmpzones):
    to_reload = False
    for tempzone in tmpzones:
        livezone = re.sub('^'+prefix, '', tempzone)
        compare_files(cfg, livezone, tempzone)

def validate_zone_config(cfg, prefix, tmpzones):
    tempconf = prefix + cfg.zonecfg
    zoneconf = ''
    for zone in tmpzones:
        name = os.path.basename(zone)
        zoneconf += create_zone_block(name)
    print 'Creating zone config in temp dir: %s' % tempconf
    if not os.path.exists(os.path.dirname(tempconf)):
        os.makedirs(os.path.dirname(tempconf))
    f = open(tempconf, 'w')
    f.write(zoneconf)
    f.close()
    if compare_files(cfg, cfg.zonecfg, tempconf):
        print "\nNew zones.conf written to temp dir: %s\nPlease install it manually to allow changes to take effect" % tempconf
    else:
        print ""

def create_zone_block(name):
    return 'zone "%s" in {\n\ttype master;\n\tfile "%s";\n};\n\n' \
        % (name, name)

def confirm_change(prefix, zone):
    ans = raw_input('\nTo approve this change, type "%s_%s": ' % (prefix, zone))
    if ans != '%s_%s' % (prefix, zone):
        raise DNSError('Rollout of "%s" zone file aborted.' % (zone))
        print 'Rollout of "%s" zone file aborted.' % (zone)
        return False
    else:
        return True

def rollout_changes(oldfile, newfile):
    if os.path.exists(oldfile):
        backup = oldfile + '.bak'
        if os.path.exists(backup):
            print 'Removing old backup: %s' % backup
            os.remove(backup)
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        print 'Making snapshot: %s.%s' % (newfile, stamp)
        shutil.copy(oldfile, newfile+'.'+stamp)
        print 'Making backup: %s' % backup
        shutil.move(oldfile, backup)
    print 'Overwriting %s with %s' % (oldfile, newfile)
    if not os.path.exists(os.path.dirname(oldfile)):
        os.makedirs(os.path.dirname(oldfile))
    shutil.copy(newfile, oldfile)

def compare_files(cfg, oldfile, newfile):
    reload = False
    print 'Comparing %s %s' % (oldfile, newfile)
    # Ignore extra spaces for comparison
    olddata = []
    if os.path.exists(oldfile):
        olddata = sorted([ re.sub('\s+',' ',x)
            for x in open(oldfile).readlines() ])
    newdata = sorted([ re.sub('\s+',' ',x)
        for x in open(newfile).readlines() ])
    diff = difflib.Differ().compare(olddata, newdata)
    changes = False
    for d in diff:
        # exclude comments, blank/common lines, Serial
        if re.match('[-+]\s+(;|$)', d) \
            or not re.match('[-+]', d) \
            or 'Serial' in d:
            continue
        if not changes:
            print '-'*60
        changes = True
        print d
    if not changes:
        print 'Skipping %s, no changes discovered' % oldfile
        return reload
    else:
        print '-'*60
    if changes and not (cfg.zonecfg == oldfile):
        if confirm_change('dns', os.path.basename(oldfile)):
            rollout_changes(oldfile, newfile)
    return changes

def generate_dns_forward(cfg, domain, opts):
    """
    Creates the forward zonefile for the specified domain
    """
    zone = None
    fqn = mothership.validate.v_get_fqn(cfg, domain)
    realm, site_id, domain = mothership.validate.v_split_fqn(fqn)
    forward = generate_dns_header(cfg, True, fqn, realm, site_id, domain)
    forward += generate_dns_arecords(cfg, realm, site_id, domain)
    forward += generate_dns_addendum(cfg, realm, site_id, domain)
    if opts.outdir:
        zone = '%s/%s' % (opts.outdir, fqn)
        print 'Writing DNS forward zone for %s to %s' % (fqn, zone)
        f = open(zone, 'w')
        f.write(forward)
        f.close()
    else:
        print '\n' + '-'*60 + '\nDNS forward zone for %s:\n' % fqn  + '-'*60
        print forward 
    if zone:
        return zone
    else:
        return None

def generate_dns_reverse(cfg, domain, opts):
    """
    Creates the reverse zonefiles for the specified domain
    """
    zones = []
    fqn = mothership.validate.v_get_fqn(cfg, domain)
    realm, site_id, domain = mothership.validate.v_split_fqn(fqn)
    netblocks = mothership.network_mapper.remap(cfg, 'cidr', dom='.'+fqn)
    if not netblocks:
        print "Skipping reverse zone for %s, undefined in mothership.yaml" % (realm+'.'+site_id)
        return False
    for cidr in netblocks:
        net, rev = generate_dns_arpa(cfg, cidr, fqn, realm, site_id, domain)
        net = '%s.in-addr.arpa' % '.'.join(reversed(net.split('.')))
        reverse = generate_dns_header(cfg, False, fqn, realm, site_id, domain)
        reverse += rev
        if opts.outdir:
            zone = '%s/%s' % (opts.outdir, net)
            print 'Writing DNS reverse zone for %s to %s' % (net, zone)
            f = open(zone, 'w')
            f.write(reverse)
            f.close()
            zones.append(zone)
        else:
            print '\n' + '-'*60 + '\nDNS reverse zone for %s:\n' % net  + '-'*60
            print reverse
    if zones:
        return zones
    else:
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
