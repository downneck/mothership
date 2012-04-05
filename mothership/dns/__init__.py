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


def generate_forward_header(cfg, origin, fqdn, realm, site_id):
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
        header += generate_root_records(cfg, rec, unqdn=realm+'.'+site_id)
    return header


def generate_reverse_header(cfg):
    """
    Returns reverse zone header for a netblock 
    """
    contact = cfg.contact
    serial = int(time.time())
    nsmaster = mothership.kv.select(cfg, None, key='nsmaster')
    if not nsmaster:
        raise DNSError("No nsmaster entry in your KV! Please configure one. Aborting.")
    nsmaster = nsmaster.value
    if '@' in contact: contact = contact.replace('@','.')
    header = """
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
    header += generate_root_records(cfg, 'ns', None)    
    return header


# generates either NS or MX records depending on 'key'
# unqdn can be any input KV accepts
def generate_root_records(cfg, key, unqdn=None):
    if not unqdn:
        unqdn='.'
    rec = mothership.kv.collect(cfg, unqdn, key)
    if not rec:
        raise DNSError('''
No %s defined for unqdn: %s or domain: %s, use:
    ship kv -a %s %s=<ns1>[,<nsN>]
to configure one or more %s
''' % (key, unqdn, cfg.domain, unqdn, key, key))
    for r in rec:
        slist = r.value.split(',')
        # why is this? 
        if r.hostname == unqdn:
            continue
        # end WTF
    records = ''
    for server in slist:
        records += '%-20s\tIN\t%-8s%-16s\n' % ('', key.upper(), server)
    return records


# generates arecords. badly.
def generate_dns_arecords(cfg, realm, site_id, drac=False, mgmt=False):
    """
    Retrieves server list from mothership to create A records
    """
    alist = ''
    if not drac and not mgmt:
        for n in cfg.dbsess.query(Network).\
            filter(Network.interface==cfg.primary_interface).\
            filter(Network.site_id==site_id).\
            filter(Network.realm==realm).all():
                if n.server_id:
                    s = cfg.dbsess.query(Server).\
                        filter(Server.id==n.server_id).first()
                    if n.ip and s.hostname:
                        alist += '%-20s\tIN\t%-8s%-16s\n' % (s.hostname, 'A', n.ip)
    elif drac and not mgmt:
        for n in cfg.dbsess.query(Network).\
            filter(Network.interface=='drac').\
            filter(Network.site_id==site_id).\
            filter(Network.realm==realm).all():
                if n.server_id:
                    s = cfg.dbsess.query(Server).\
                        filter(Server.id==n.server_id).first()
                    if n.ip and s.hostname:
                        alist += '%-20s\tIN\t%-8s%-16s\n' % (s.hostname, 'A', n.ip)
    elif mgmt and cfg.mgmt_vlan_interface and not drac:
        for n in cfg.dbsess.query(Network).\
            filter(Network.interface==cfg.mgmt_vlan_interface).\
            filter(Network.site_id==site_id).\
            filter(Network.realm==realm).all():
                if n.server_id:
                    s = cfg.dbsess.query(Server).\
                        filter(Server.id==n.server_id).first()
                    if n.ip and s.hostname:
                        alist += '%-20s\tIN\t%-8s%-16s\n' % (s.hostname, 'A', n.ip)
    elif mgmt and drac:
        raise DNSError("massive problem in mothership code. pick either mgmt or drac in your generate_dns_arecords() call")
    else:
        print "dumping vars. realm: %s, site_id: %s, drac: %s, mgmt: %s" % (realm, site_id, drac, mgmt)
        raise DNSError("something has gone horribly wrong in generate_dns_arecords()")
    return alist


def generate_regular_arpa(cfg, cidr):
    """
    Retrieves server list from mothership to create regular arpa records
    """
    net = mothership.network_mapper.get_network(cidr)
    num = 0
    while re.search('\.0+$', net):
        net = re.sub('\.0+$', '', net)
        num += 1
    alist = ''
    for n in cfg.dbsess.query(Network).\
        filter(Network.interface==cfg.primary_interface).\
        order_by(Network.ip).all():
        if n.server_id:
            s = cfg.dbsess.query(Server).\
                    filter(Server.id==n.server_id).first()
            if mothership.network_mapper.within(n.ip, cidr) and n.ip and s.hostname:
                alist += '%-20s\tIN\t%-8s%s.%s.%s.%s.\n' % (
                    '.'.join(reversed(n.ip.split('.')[-num:])),
                    'PTR', s.hostname, n.realm, n.site_id, cfg.domain)
    return net, alist


def generate_mgmt_arpa(cfg, cidr):
    """
    Retrieves server list from mothership to create mgmt arpa records
    """
    net = mothership.network_mapper.get_network(cidr)
    num = 0
    while re.search('\.0+$', net):
        net = re.sub('\.0+$', '', net)
        num += 1
    alist = ''
    for n in cfg.dbsess.query(Network).\
        filter(Network.interface==cfg.mgmt_vlan_interface).\
        order_by(Network.ip).all():
        if n.server_id:
            s = cfg.dbsess.query(Server).\
                    filter(Server.id==n.server_id).first()
            if mothership.network_mapper.within(n.ip, cidr) and n.ip and s.hostname:
                alist += '%-20s\tIN\t%-8s%s.mgmt.%s.%s.%s.\n' % (
                    '.'.join(reversed(n.ip.split('.')[-num:])),
                    'PTR', s.hostname, n.realm, n.site_id, cfg.domain)
    return net, alist


def generate_drac_arpa(cfg, cidr):
    """
    Retrieves server list from mothership to create drac arpa records
    """
    net = mothership.network_mapper.get_network(cidr)
    num = 0
    while re.search('\.0+$', net):
        net = re.sub('\.0+$', '', net)
        num += 1
    alist = ''
    for n in cfg.dbsess.query(Network).\
        filter(Network.interface=='drac').\
        order_by(Network.ip).all():
        if n.server_id:
            s = cfg.dbsess.query(Server).\
                    filter(Server.id==n.server_id).first()
            if mothership.network_mapper.within(n.ip, cidr) and n.ip and s.hostname:
                alist += '%-20s\tIN\t%-8s%s.drac.%s.%s.%s.\n' % (
                    '.'.join(reversed(n.ip.split('.')[-num:])),
                    'PTR', s.hostname, n.realm, n.site_id, cfg.domain)
    return net, alist


def generate_dns_addendum(cfg, realm, site_id):
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
            raise DNSError("Addendum record does not exist: %s" % realm+"."+site_id+"."+cfg.domain)
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
                zones.extend(generate_dns_forward(cfg, fqn, opts))
        revzones = generate_dns_reverse(cfg, opts)
        if revzones:
            zones.extend(revzones)
        else: 
            print "No reverse zones created"
    else:
        zones.extend(generate_dns_forward(cfg, domain, opts))
        revzones = generate_dns_reverse(cfg, opts)
        if revzones:
            zones.extend(revzones)
        else: 
            print "No ouput directory has been specified, so no reverse zone files were written for %s" % domain
    if opts.system:
        # Remove empty zones
        zones = [ z for z in zones if z ]
        validate_zone_files(cfg, tmpdir, zones)
        if opts.all:
            validate_zone_config(cfg, tmpdir, zones)
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
        # shhhh.
        #print 'Skipping %s, no changes discovered' % oldfile
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
    Creates the mgmt forward zonefile
    Creates the drac forward zonefile (if applicable)
    """
    zones = []
    zone = None
    fqn = mothership.validate.v_get_fqn(cfg, domain)
    realm, site_id, domain = mothership.validate.v_split_fqn(cfg, fqn)
    forward = generate_forward_header(cfg, True, fqn, realm, site_id)
    # generate the main fqn
    forward += generate_dns_arecords(cfg, realm, site_id)
    forward += generate_dns_addendum(cfg, realm, site_id)
    # if we're using drac, generate drac.fqn
    if cfg.drac:
        dracforward = generate_forward_header(cfg, True, 'drac.'+fqn, realm, site_id)
        dracforward += generate_dns_arecords(cfg, realm, site_id, drac=True)
    # generate mgmt.fqn
    mgmtforward = generate_forward_header(cfg, True, 'mgmt.'+fqn, realm, site_id)
    mgmtforward += generate_dns_arecords(cfg, realm, site_id, mgmt=True)
    if opts.outdir:
        # write out the main zone
        zone = '%s/%s' % (opts.outdir, fqn)
        print 'Writing DNS forward zone for %s to %s' % (fqn, zone)
        zones.append(zone)
        f = open(zone, 'w')
        f.write(forward)
        f.close()
        # write out the mgmt zone
        zone = '%s/%s' % (opts.outdir, 'mgmt.'+fqn)
        print 'Writing DNS forward zone for %s to %s' % ('mgmt.'+fqn, zone)
        zones.append(zone)
        f = open(zone, 'w')
        f.write(mgmtforward)
        f.close()
        # write out the drac zone
        if cfg.drac:
            zone = '%s/%s' % (opts.outdir, 'drac.'+fqn)
            print 'Writing DNS forward zone for %s to %s' % ('drac.'+fqn, zone)
            zones.append(zone)
            f = open(zone, 'w')
            f.write(dracforward)
            f.close()
        
    else:
        print '\n' + '-'*60 + '\nDNS forward zone for %s:\n' % fqn + '-'*60
        print forward
        print '\n' + '-'*60 + '\nDNS forward zone for %s:\n' % 'mgmt.'+fqn + '-'*60
        print mgmtforward
        if cfg.drac:
            print '\n' + '-'*60 + '\nDNS forward zone for %s:\n' % 'drac.'+fqn + '-'*60
            print dracforward
    if zones:
        return zones
    else:
        return None


def generate_dns_reverse(cfg, opts):
    """
    Creates the reverse zonefiles for the specified domain
    """
    zones = []
    netblocks = mothership.network_mapper.remap(cfg, 'cidr', nic=cfg.primary_interface)
    mgmtnetblocks = mothership.network_mapper.remap(cfg, 'cidr', nic=cfg.mgmt_vlan_interface)
    if cfg.drac:
        dracnetblocks = mothership.network_mapper.remap(cfg, 'cidr', nic='drac')
    if not netblocks or not mgmtnetblocks or (cfg.drac and not dracnetblocks):
        return False
    # do this whole mess once for the primary networks 
    for cidr in netblocks:
        net, rev = generate_regular_arpa(cfg, cidr)
        net = '%s.in-addr.arpa' % '.'.join(reversed(net.split('.')))
        reverse = generate_reverse_header(cfg)
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
    # redo the whole mess again for the mgmt nets
    for cidr in mgmtnetblocks:
        net, rev = generate_mgmt_arpa(cfg, cidr)
        net = '%s.in-addr.arpa' % '.'.join(reversed(net.split('.')))
        reverse = generate_reverse_header(cfg)
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
    # redo the whole mess again for the dracs
    if dracnetblocks:
        for cidr in dracnetblocks:
            net, rev = generate_drac_arpa(cfg, cidr)
            net = '%s.in-addr.arpa' % '.'.join(reversed(net.split('.')))
            reverse = generate_reverse_header(cfg)
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
