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
   The mothership module encompasses many of the operations that
   would need to be done against the mothership DB that cannot
   be easily encapsulated within the sqlalchemy models
"""
# imports
import mothership.network_mapper
import os
import re
import sys
import types

import mothership.kv
import mothership.list_values
import mothership.users
import mothership.validate

from mothership.mothership_models import *
from sqlalchemy import or_, desc, MetaData


# Mothership's main exception type
class MothershipError(Exception):
    pass


# Add a tag
def add_tag(cfg, name, start_port=None, stop_port=None, security_level=None):
    badtag = cfg.dbsess.query(Tag).\
              filter(Tag.name==name).first()

    if badtag:
        raise MothershipError("tag \"%s\" already exists, aborting" % name)

    r = Tag(name, start_port, stop_port, security_level)
    cfg.dbsess.add(r)
    cfg.dbsess.commit()


# Remove a tag
def rm_tag(cfg, name):
    r = cfg.dbsess.query(Tag).\
        filter(Tag.name==name).first()

    if not r:
        raise MothershipError("tag \"%s\" not found, aborting" % name)

    # modify all servers entries with pending delete tag
    for s in cfg.dbsess.query(Server).\
        filter(Server.tag==name):
        unqdn = '.'.join([s.hostname, s.realm, s.site_id])
        print '%s has primary tag: %s' % (unqdn, s.tag)
        ans = raw_input("specify replacement primary tag for %s: " % unqdn)
        mothership.modify_server_column(cfg, unqdn, 'tag', ans, True)
    # remove all kv entries with pending delete tag
    kvs = mothership.kv.collect(cfg, fqdn=None, key='tag', value=name)
    if kvs:
        print 'The following hosts have tag=%s:' % name
        for k in kvs:
            unqdn = '.'.join([k.hostname, k.realm, k.site_id])
            print '\t%s' % unqdn
    ans = raw_input("to delete tag \"%s\" please type \"delete_%s\": " % (name, name))
    if ans != "delete_%s" % name:
        raise MothershipError("aborted by user")
    else:
        for k in kvs:
            unqdn = '.'.join([k.hostname, k.realm, k.site_id])
            print 'Removing tag=%s from %s' % (name, unqdn)
            mothership.kv.delete(cfg, unqdn, key='tag', value=name)
        print 'Deleting tag: %s' % name
        cfg.dbsess.delete(r)
        cfg.dbsess.commit()


# display a tag
def display_tag(cfg, name):
    r = cfg.dbsess.query(Tag).\
        filter(Tag.name==name).first()

    if not r:
        raise MothershipError("tag \"%s\" not found, aborting" % name)
    else:
        print "name: %s\nstart_port: %s\nstop_port: %s\nsecurity level: %s" % (r.name, r.start_port, r.stop_port, r.security_level)


def calculate_last_virtual_ipaddress(cfg, vlan):
    data = cfg.dbsess.query(Network).\
        filter(Network.vlan==vlan).\
        filter(Network.hw_tag==cfg.dbnull)
    if data.first():
        data = data.order_by(Network.ip.desc()).first()
        return data.ip, data.realm, data.site_id
    else:
        # Assuming that all prod virtuals start on 1st_dyn_ip 
        ip,site_id = mothership.network_mapper.remap(cfg, ['1st_dyn_ip','siteid'], vlan=int(vlan))
        return ip, 'prod', site_id

def calculate_next_baremetal_vlan_ipaddress(cfg, vlan):
    data = cfg.dbsess.query(Network).\
        filter(Network.vlan==vlan).\
        filter(Network.ip!=cfg.dbnull).\
        filter(Network.hw_tag!=cfg.dbnull)
    lowest = mothership.network_mapper.remap(cfg, '1st_static_ip', vlan=int(vlan))
    try:
        first = data.order_by(Network.ip).first().ip
        last = data.order_by(Network.ip.desc()).first().ip
        #print 'RANGE: %s - %s' % (first, last)
    except:
        first = lowest
        last = first
    if first < lowest:
        first = lowest

    # compare the sequential list to the shiplist
    shiplist = []
    for i in data.order_by(Network.ip).all():
        shiplist.append(i.ip)

    # determine the next free ip and return it
    nextip = None
    for i in mothership.network_mapper.generate_ipaddress_list(first, last=last):
        if i not in shiplist:
            pingcheck = os.popen("ping -q -c2 -t2 "+i,"r")
            while 1:
                line = pingcheck.readline()
                if not line: break
                match = re.findall(re.compile(r"(\d)( packets)? received"),line)
                if match:
                    if int(match[0][0]) == 0:
                        return i
    if not nextip:
        nextip = mothership.network_mapper.next_ip(last)
    return nextip

def clear_serverinfo_from_network(cfg, server_id):
    for row in retrieve_network_rows(cfg, serverid=server_id):
        intf = getattr(row, 'interface')
        if intf not in ['drac', 'eth0']:
            for col in ['vlan', 'ip', 'netmask',
                'bond_options', 'public_ip', 'static_route']:
                setattr(row, col, cfg.dbnull)
        setattr(row, 'server_id', cfg.dbnull)
    cfg.dbsess.commit()

def confirm_column_change(curr_val, new_val, colname, tblname):
    print 'Please confirm the following change to:\n'
    print '%-10s | %-20s' % ('Table', 'Column')
    print '=' * 60
    print '%-10s | %-20s' % (tblname, colname)
    print ''
    print '%-20s --> %-20s' % (curr_val, new_val)
    ans = raw_input('\nTo confirm this change, type "modify_%s": ' % colname)
    if ans != 'modify_%s' % colname:
        print 'Modification of "%s" column in %s aborted.' % (colname, tblname)
        return False
    else:
        return True

def convert_drac_dict_to_network(cfg, drac_sysinfo, ip):
    dracip, siteid = mothership.network_mapper.remap(cfg,
        ['ip','siteid'], nic='drac', ip=ip)
    mgmtip = mothership.network_mapper.remap(cfg,
        'ip', nic='eth0', siteid=siteid)
    for k in sorted(drac_sysinfo.keys()):
        netdrac_sysinfo = drac_sysinfo.copy()
        netdrac_sysinfo.update({'realm':None,
            'interface':k, 'mac':netdrac_sysinfo[k]})
        if not k.startswith('eth') and k != 'drac': continue
        print 'Importing %s' % k
        net = mothership.network_mapper.remap(cfg,
            ['vlan','mask','ip', 'dom'], nic=k, siteid=siteid)
        if net:
            realm = mothership.validate.v_split_fqn(net[3])[1]
            if k!='eth1': # due to multiple vlans
                if net[2] == mgmtip:
                    netdrac_sysinfo.update({'ip':ip.replace(dracip,mgmtip)})
            netdrac_sysinfo.update({'vlan':net[0],
                'netmask':net[1], 'realm':realm})
        update_table_network(cfg, netdrac_sysinfo)

def convert_table_objects_to_dict(tables):
    d = {}
    for table in tables.keys():
        for k in getattr(tables, table).__dict__.keys():
            if k.startswith('_') or k=='id':
                continue
            d[k] = getattr(tables,table).__dict__[k]
    return d

def count_graveyard_server_by_date(cfg, hostname, when):
    host,realm,site_id = mothership.get_unqdn(cfg, hostname)
    try:
        return cfg.dbsess.query(ServerGraveyard).\
            filter(ServerGraveyard.deprovision_date==when).\
            filter(ServerGraveyard.hostname==host).\
            filter(ServerGraveyard.realm==realm).\
            filter(ServerGraveyard.site_id==site_id).\
            count()
    except:
        return 0

def delete_server(cfg, hostname, relatives=None):
    host,realm,site_id = mothership.get_unqdn(cfg, hostname)
    s = cfg.dbsess.query(Server).\
        filter(Server.hostname==host).\
        filter(Server.realm==realm).\
        filter(Server.site_id==site_id).\
        one()
    # mapper/delete-cascade does not seem to override foreign constraint, so
    # delete constrained foreign keys first, replace if better method found
    for r in relatives:
        print 'DEBUG: %s' % r
        print 'Deleting %s records that are related to server_id %d' % (r, s.id)
        cfg.dbconn.execute(r.delete().where(Column('server_id')==s.id))
    # Then remove the servers record
    print 'Deleting %s (id=%d) from servers' % (
        '.'.join(mothership.get_unqdn(cfg, hostname)), s.id)
    cfg.dbsess.delete(s)
    cfg.dbsess.commit()

def expire_server(cfg, hostname, when, delete_entry=True):
    unqdn = '.'.join(mothership.get_unqdn(cfg, hostname))
    cols = retrieve_server_dict(cfg, hostname)
    if not cols['id']:
        print 'There is no server named %s to delete' % unqdn
        return
    cols['delid'] = cols['id']
    del cols['id']
    cols['deprovision_date'] = when
    # retrieve all server_id related info and display
    print '\nThe following info is related to %s (id=%d)' % (unqdn, cols['delid'])
    meta = MetaData()
    meta.reflect(bind=cfg.dbengine)
    relatives = []  # while displaying related tables, build list for deletion
    for table in meta.sorted_tables:
        for col in table._columns:
            if table.name == 'network': continue    # leave network table alone
            if '.server_id' in str(col):
                q = cfg.dbsess.query(table).filter(col==cols['delid']).all()
                if q:
                    print '\nFrom the "%s" table:' % table.name
                    relatives.append(table)
                    for line in q:
                        for k in line.keys():
                            if k == 'server_id': continue
                            if k.startswith('_'): del line[k]
                            print '%20s : %s' % (k,getattr(line,k))
    if delete_entry:
        # Confirm with user before acting
        print '\nTo confirm that you want ALL of this removed,'
        ans = raw_input('Please type "delete_%s": ' % hostname)
        if ans != 'delete_%s' % hostname:
            print 'Expire server aborted.'
            return
        print 'Inserting %s into server_graveyard' % unqdn
        insert_server_into_graveyard(cfg, cols) # Insert into server graveyard
        # Check hostname exists in server_graveyard and continue only if found
        if count_graveyard_server_by_date(cfg, hostname, when) > 0:
            # remove the server's group
            server_groupname = unqdn.replace('.', '_') + \
                "." + cols['realm'] + "." + cols['site_id']
            try:
                mothership.users.gremove(cfg, server_groupname)
            except Exception, e:
                print e
                if not 'does not exist' in str(e):
                    return
            # clear server info from network table
            clear_serverinfo_from_network(cfg, cols['delid'])
            # Remove server from servers table and related tables
            delete_server(cfg, hostname, relatives)
            if cols['virtual']: return 'virtual'
            return True
    else:
        # Handle the case we want to add to server_graveyard (rekicking)
        print 'Inserting %s into server_graveyard' % hostname
        insert_server_into_graveyard(cfg, cols) # Insert into server graveyard
        return True

def snh(cfg, host, realm, site_id):
    """
        Finds first entry based on host.realm.site_id and returns
        a join of server, network, and hardware information as
        a tuple
    """
    s, h = cfg.dbsess.query(Server, Hardware).\
    filter(Server.hostname==host).\
    filter(Server.realm==realm).\
    filter(Server.site_id==site_id).\
    filter(Hardware.hw_tag==Server.hw_tag).\
    first()

    n = cfg.dbsess.query(Network).\
    filter(Network.server_id==s.id)

    if s and n and h:
        return (s, n, h)
    else:
        return None

def generate_ipaddress_range(cfg, first, count=None, last=None, realm=None, site_id=None):
    """
       Generates all the ip addresses between first and last ip specified
       determines the vlan, netmask and interface and inserts into network
       e.g. generate_ips('10.50.50.15','10.50.50.30')
    """
    for ip in mothership.network_mapper.generate_ipaddress_list(first, count=count, last=last):
        vlan, netmask, interface = mothership.network_mapper.remap(cfg,
            ['vlan','mask','nic'], ip=ip, siteid=site_id)
        mac = mothership.network_mapper.ip_to_mac(ip)
        update_table_network(cfg, { 'ip':ip, 'realm':realm, 'site_id':site_id,
            'mac':mac, 'vlan':vlan, 'netmask':netmask, 'interface':interface })

def import_multiple_table_info(cfg, info, when):
    sid = None
    hwtag = None
    for table in sorted(info.keys(), reverse=True):  # server MUST comes first
        for rec in info[table]:                      # to retrieve rec info
            if sid and 'server_id' not in rec: rec['server_id'] = sid
            if hwtag and 'hw_tag' not in rec: rec['hw_tag'] = hwtag
            if table == 'server':
                sid,hwtag = update_table_server(cfg, rec, when)
            elif table == 'hardware':
                update_table_hardware(cfg, rec, when)
            elif table == 'network':
                if hwtag: rec['hw_tag'] = hwtag
                update_table_network(cfg, rec)
            else:
                print 'Unsupported table (%s) for import, skipping' % table
                continue

def insert_server_into_graveyard(cfg, values):
    g = ServerGraveyard(values['hostname'])
    for k in values.keys():
        setattr(g, k, values[k])
    cfg.dbsess.add(g)
    cfg.dbsess.commit()

def merge_dictlists(master, slave, key):
    for m in master:
        for s in slave:
            if key not in m or key not in s:
                continue
            if m[key] == s[key]:
                m.update(s)
    return master

def modify_network_vlan(cfg, hostname, vlan, interface='eth1', force=False):
    host,realm,site_id = mothership.get_unqdn(cfg, hostname)
    ip = calculate_next_baremetal_vlan_ipaddress(cfg, vlan)
    try:
        data = cfg.dbsess.query(Server,Network).\
            filter(Server.hostname==host).\
            filter(Server.realm==realm).\
            filter(Server.site_id==site_id).\
            filter(Server.id==Network.server_id).\
            filter(Network.interface==interface).\
            one().Network
    except:
        data = None
    if data and data.vlan is not None:
        print 'For %s: %s already set to ip=%s on vlan=%s' \
            % (hostname, interface, data.ip, data.vlan)
        if int(vlan) == int(data.vlan) and data.ip is not None:
            print 'No changes necessary'
            return
        if not force:
            print 'The next available ip on vlan=%s is %s' % (vlan, ip)
            ans = raw_input('Do you wish to overwrite (y/N)? ')
            if ans not in ['Y','y']:
                print 'Modify VLAN aborted.'
                return
    new = {'ip':ip, 'vlan':vlan,
            'netmask':cfg.dbnull, 'static_route':cfg.dbnull}
    mask = mothership.network_mapper.remap(cfg, 'mask', ip=ip,
            nic=interface, siteid=data.site_id)
    gw = mothership.network_mapper.remap(cfg, 'gw', ip=ip,
            nic=interface, siteid=data.site_id)
    if mask:    new['netmask'] = mask
    if gw:      new['static_route'] = gw
    print 'Updating %s: setting %s to ip=%s on vlan=%s' % (
            hostname, interface, ip, vlan)
    for k in new.keys():
        setattr(data, k, new[k])
    cfg.dbsess.commit()

def modify_network_column(cfg, hostname, interface, col, value):
    """
        Modify a row in the network table where column
        is named 'col' and value is the value to change
        key_dict is the set of keys to try lookup on.
        Note that this method can only modify '1' row
        so any key_dict that returns multiple rows will
        modify nothing
    """
    row = retrieve_network_rows_by_unqdn(cfg, hostname, interface=interface)
    curr_val = getattr(row, col)
    if confirm_column_change(curr_val, value, col, row.__tablename__):
        setattr(row, col, value)
        cfg.dbsess.commit()
        print "Changes committed.  %s is now %s" % (col, value)
    else:
        print "Nothing confirmed. Nothing modified"

def modify_server_column(cfg, hostname, col, value, force=False):
    """
        Modify a row in the server column using the same exact
        technique in the modify_network_column function (public_ip
        will be removed from this function since it belongs to the
        network table)
    """
    host,realm,site_id = mothership.get_unqdn(cfg, hostname)
    unqdn = '.'.join([host,realm,site_id])
    row = retrieve_server_row_by_unqdn(cfg, unqdn)
    curr_val = getattr(row, col)
    if col == 'tag':
        tags = []
        for tag in cfg.dbsess.query(Tag):
            tags.append(tag.name)
        if value not in tags:
            raise MothershipError('You specified an invalid tag: %s' % value)
    if force or confirm_column_change(curr_val, value, col, row.__tablename__):
        setattr(row, col, value)
        cfg.dbsess.commit()
        print "Changes committed.  %s is now %s" % (col, value)
        if not force and col == 'hostname':
            # update or add groupname for host
            oldgroupname = unqdn.replace('.', '_')
            newgroupname = oldgroupname.replace(host, value)
            g = cfg.dbsess.query(Groups).\
                filter(Groups.groupname==oldgroupname).\
                filter(Groups.realm==realm).\
                filter(Groups.site_id==site_id).first()
            if g:
                print "changing group %s to %s" % (oldgroupname, newgroupname)
                setattr(g, 'groupname', newgroupname)
                cfg.dbsess.commit()
            else:
                print "adding group: %s" % newgroupname
                mothership.users.gadd(cfg, newgroupname+"."+realm+"."+site_id)
            # create a group for the new machine's sudoers
            oldsudogroup = oldgroupname+'_sudo'
            newsudogroup = newgroupname+'_sudo'
            g = cfg.dbsess.query(Groups).\
                filter(Groups.groupname==oldsudogroup).\
                filter(Groups.realm==realm).\
                filter(Groups.site_id==site_id).first()
            if g:
                print "changing sudo group %s to %s" % (oldsudogroup, newsudogroup)
                setattr(g, 'groupname', newsudogroup)
                cfg.dbsess.commit()
            else:
                print "adding sudo group: %s" % newsudogroup
                mothership.users.gadd(cfg, newsudogroup+"."+realm+"."+site_id)
    else:
        print "Nothing confirmed. Nothing modified"

def get_hwtag_from_dracip(cfg, dracip):
    return cfg.dbsess.query(Network).filter(Network.interface=='drac').\
        filter(Network.ip==dracip).one().hw_tag

def get_hwtag_from_mgmtip(cfg, mgmtip):
    return cfg.dbsess.query(Network).filter(Network.interface=='eth0').\
        filter(Network.ip==mgmtip).one().hw_tag

def get_hwtag_from_vlan(cfg, vlan):
    return cfg.dbsess.query(Server,Network).filter(Network.vlan==vlan).\
        filter(Server.id==Network.server_id).\
        filter(Server.cobbler_profile.like('xenserver%')).\
        first().Server.hw_tag

def check_server_tag(cfg, hostname, tag=None):
    # set the primary tag to be the hostname without the trailing integers
    if not tag:
        tag = re.sub('\d+$', '', hostname.split('.')[0])
    # check to make sure that the tag is valid before proceeding
    try:
        cfg.dbsess.query(Tag).filter(Tag.name==tag).one()
        print 'Setting primary tag to %s' % tag
        return tag
    except:
        print '%s is not a valid tag, provisioning of %s aborted' % (tag, hostname)
        return False

def check_server_exists(cfg, hostname):
    unqdn = '.'.join(mothership.get_unqdn(cfg, hostname))
    try:
        row = retrieve_server_row_by_unqdn(cfg, unqdn)
        if row:
            sys.stderr.write('%s already provisioned, skipping\n' % unqdn)
            return True
    except:
        return False

def get_os_configs(osdict, profile, osname=None):
    if osname:
        if osname in osdict['profile'].keys():
            profile = osname
            osprofile = osdict['profile'][profile]
        elif osname in osdict['profile'].values():
            osprofile = osname
            for k in osdict['profile'].keys():
                if osprofile == osdict['profile'][k]:
                    profile = k
        else:
            print 'Unknown profile or OS specified! Existing values are:'
            for k in osdict['profile'].keys():
                if k != 'default':
                    print '\t%s\t\t%s' % (osdict['profile'][k], k)
            print 'Disabling cobbler, setting OS to: %s' % osname
            osprofile = osname
            profile = None
    else:
        osprofile = osdict['profile'][profile]
    return profile, osprofile

def build_model_dict(model, obj, vars, nullobj=False, nullvar=False):
    info = {}
    for s in dir(model):
        if not s.startswith('_'):
            if s in dir(obj):
                if getattr(obj, s) or nullobj:
                    info[s] = getattr(obj, s)
            elif vars.has_key(s):
                if vars[s] or nullvar:
                    info[s] = vars[s]
    return info

def provision_server(cfg, fqdn, vlan, when, osdict, opts):
    if not is_unqdn(cfg, fqdn):
        print 'fqdn MUST contain hostname.realm.site_id'
        return

    if check_server_exists(cfg, fqdn): return
    setattr(opts, 'tag', check_server_tag(cfg, fqdn, opts.tag))
    if not opts.tag: return

    hostname,realm,site_id = split_fqdn(fqdn)

    setattr(opts, 'vlan', vlan)
    virtual = False
    if not opts.hw_tag:
        for o in ['dracip', 'mgmtip', 'vlan']:
            exec 'test = opts.%s' % o
            if test:
                try:
                    exec 'setattr(opts, "hw_tag", get_hwtag_from_%s(cfg, opts.%s))' % (o, o)
                    if o == 'vlan':
                        virtual = True
                        profile = osdict['default']['virtual']
                    break
                except:
                    print '%s=%s was not found in database, aborting' % (o, test)
                    return

    if not virtual:
        try:    # check to see if hwtag already belongs to a server
            check = retrieve_network_row_by_ifname(cfg,
                    'eth0', filter={'hw_tag':opts.hw_tag})
            if check.server_id:
                print '%s already provisioned as server id %s' % (opts.hw_tag, check.id)
                return
        except:
            print 'Hardware tag %s does NOT exist in mothership' % opts.hw_tag
            return
        if hostname.startswith('xen'):    # xen server
            profile = osdict['default']['xenserver']
        else:                             # default
            profile = osdict['default']['baremetal']
    opts.cobbler_profile, opts.os = get_os_configs(osdict, profile, opts.osname)

    if virtual:
        # make sure the vlan specified is primary eth1
        if mothership.network_mapper.remap(cfg, 'nic', vlan=int(vlan), siteid=site_id) != 'eth1':
            print 'Please specify the primary vlan for eth1 for virtual hosts'
            return

        # if specs are not provided, get the minimum values from configuration
        for key in cfg.vm_spec.keys():
            if not getattr(opts, key):
                setattr(opts, key, cfg.vm_spec[key])

        # check eth1 and eth0 for valid ips before continuing
        iplist = []
        vlist = [ mothership.network_mapper.remap(cfg, 'vlan', nic='eth0', siteid=site_id), vlan ]
        for v in vlist:
            iplist.append(retrieve_next_virtual_ip(cfg, v, autogen=True))

        # build dict for server insert
        svr_info = build_model_dict(Server(''), opts, locals(), nullvar=True)
        server_id, opts.hw_tag = update_table_server(cfg, svr_info, when)

        # build dict for eth1 network insert
        ip = iplist[1]
        interface = 'eth1'
        static_route, netmask = mothership.network_mapper.remap(cfg, ['gw', 'mask'],
            nic=interface, ip=iplist[1], siteid=site_id)
        if not opts.public_ip or mothership.network_mapper.remap(
            cfg, 'ip', ip=opts.public_ip):
            print 'Invalid public_ip %s, using default %s' \
                % (opts.public_ip, cfg.def_public_ip)
            opts.public_ip = cfg.def_public_ip
        setattr(opts, 'hw_tag', None)
        net_info = build_model_dict(Network('','','',''), opts, locals())
        update_table_network(cfg, net_info)

        # update network for eth0
        realm = mothership.validate.v_split_fqn(
            mothership.network_mapper.remap(cfg,
               'dom', nic='eth0', siteid=site_id))[1]
        mgmt_info = {'server_id': server_id, 'realm':realm,
            'interface':'eth0', 'ip':iplist[0]}
        update_table_network(cfg, mgmt_info)
        print 'Added virtual host %s to mothership' % fqdn
    else:
        # check to make sure that hardware is not marked for RMA
        data = retrieve_hardware_row(cfg, opts.hw_tag)
        if data.rma:
            print '%s is marked for RMA so cannot be provisioned' % opts.hw_tag
            return

        # build dict for server insert
        svr_info = build_model_dict(Server(''), opts, locals(), nullvar=True)
        server_id, opts.hw_tag = update_table_server(cfg, svr_info, when)

        # update the server_id in the network table rows and return the id
        for net in retrieve_network_rows(cfg, hwtag=opts.hw_tag):
            ip = net.ip
            interface = net.interface
            if interface == 'eth1':
                ip = calculate_next_baremetal_vlan_ipaddress(cfg, vlan)
                opts.vlan = vlan
                if not opts.public_ip or network_mapper.remap(
                    cfg, 'ip', ip=opts.public_ip):
                    print 'Invalid public_ip %s, using default %s' \
                        % (opts.public_ip, cfg.def_public_ip)
                    opts.public_ip = cfg.def_public_ip
            else:
                opts.vlan = net.vlan
                opts.public_ip = None
            # never retrieve the gw without ip=, especially when eth1
            if ip:
                domain,static_route,netmask = mothership.network_mapper.remap(
                    cfg, ['dom', 'gw', 'mask'],
                    nic=interface, ip=ip, siteid=site_id)
                realm = mothership.validate.v_split_fqn(domain)[1]
            else:
                static_route = None
                netmask = None
                realm = None
            bond_options = None
            net_info = build_model_dict(Network('','','',''), opts, locals())
            update_table_network(cfg, net_info)
            if re.match('eth[12]', interface):
                bond_options = 'mode=active-backup miimon=10'
                net_info = build_model_dict(Network('','','',''), opts, locals())
                update_table_network(cfg, net_info)
        print 'Added baremetal host %s to mothership' % hostname

    # create a group for the new machine
    newgroupname = fqdn.replace('.', '_')
    g = cfg.dbsess.query(Groups).\
        filter(Groups.groupname==newgroupname).\
        filter(Groups.realm==realm).\
        filter(Groups.site_id==site_id).first()
    if g:
        print "group exists, skipping: %s" % newgroupname
    else:
        mothership.users.gadd(cfg, newgroupname+"."+realm+"."+site_id)

    # create a group for the new machine's sudoers
    newsudogroup = newgroupname+'_sudo'
    g = cfg.dbsess.query(Groups).\
        filter(Groups.groupname==newsudogroup).\
        filter(Groups.realm==realm).\
        filter(Groups.site_id==site_id).first()
    if g:
        print "group exists, skipping: %s" % newsudogroup
    else:
        print "creating sudo group (default commands = ALL, use gmodify to change): "+newsudogroup
        mothership.users.gadd(cfg, newsudogroup+"."+realm+"."+site_id, sudo_cmds='ALL')
    return server_id


def remove_method_keys(dict, empty=False):
    for k in dict.keys():
        if empty: dict[k] = None
        if k.startswith('_'): del dict[k]
    return dict

def retrieve_cobbler_network_rows(cfg, hostname):
    host,realm,site_id = mothership.get_unqdn(cfg, hostname)
    return cfg.dbsess.query(Server,Network).\
            filter(Server.hostname==host).\
            filter(Server.realm==realm).\
            filter(Server.site_id==site_id).\
            filter(Server.id==Network.server_id).\
            order_by(Network.interface).all()

def retrieve_cobbler_system_dict(cfg, hostname, xen=False):
    sysdict = convert_table_objects_to_dict(
        retrieve_cobbler_system_row(cfg,hostname))
    netdict = {}
    for net in retrieve_cobbler_network_rows(cfg, hostname):
        ifname = net.Network.__dict__['interface']
        #if ifname != 'drac':
        netdict[ifname] = convert_table_objects_to_dict(net)
    sysdict['interfaces'] = netdict
    if sysdict['virtual']:
        sysdict['power_type'] = 'xenapi'
        power = cfg.dbsess.query(Server,Network).\
            filter(Network.vlan==netdict['eth1']['vlan']).\
            filter(Server.id==Network.server_id).\
            filter(Server.cobbler_profile.like('xenserver%'))
        if xen:
            host,realm,site_id = mothership.get_unqdn(cfg, xen)
            power = power.\
                filter(Server.hostname==host).\
                filter(Server.realm==realm).\
                filter(Server.site_id==site_id)
        try:
            s = power.first().Server
            sysdict['power_switch'] = '.'.join([s.hostname, s.realm, s.site_id])
        except:
            print "Server %s not found or not part of vlan %s" % (xen,netdict['eth1']['vlan'])
            sys.exit(1)
    else:
        sysdict['power_type'] = 'ipmitool'
    return sysdict

def retrieve_cobbler_system_row(cfg, hostname):
    host,realm,site_id = mothership.get_unqdn(cfg, hostname)
    try:
        return cfg.dbsess.query(Server,Hardware).\
            filter(Server.hostname==host).\
            filter(Server.realm==realm).\
            filter(Server.site_id==site_id).\
            filter(Server.hw_tag==Hardware.hw_tag).one()
    except:
        print "Server %s not found in cobbler database" % hostname
        sys.exit(1)

def retrieve_fqdn(cfg, hostname, interface='eth1'):
    q = retrieve_server_dict(cfg, hostname)
    append = mothership.network_mapper.remap(cfg, 'dom', nic=interface, siteid=q['site_id'])
    return q['hostname'] + append

def retrieve_hardware_row(cfg, hwtag):
    try:
        return cfg.dbsess.query(Hardware).filter(Hardware.hw_tag==hwtag).one()
    except:
        print "hwtag %s not found in database" % hwtag
        return None

def retrieve_network_rows_by_unqdn(cfg, unqdn, interface = None):
    """
        Retrieve all network rows associated with a particular unqdn
        Takes an optional interface parameter which will narrow
        down the row retrieved
    """
    server = retrieve_server_row_by_unqdn(cfg, unqdn)
    if server:
        server_id = server.id
        if interface:
            network_rows = retrieve_network_row_by_ifname(cfg, interface, 
                    filter={'server_id':server_id})
        else:
            network_rows = retrieve_network_rows(cfg, serverid = server_id)
        return network_rows
    else:
        return []

def retrieve_network_rows_by_servername(cfg, hostname):
    """
        Retrieve all network rows associated with a particular hostname
    """
    unqdn = '.'.join(mothership.get_unqdn(cfg, hostname))
    server = retrieve_server_row_by_unqdn(cfg, unqdn)
    if server:
        server_id = server.id
        network_rows = retrieve_network_rows(cfg, serverid = server_id)
        return network_rows
    else:
        return []

def retrieve_network_row_by_ifname(cfg, ifname, filter):
    data = cfg.dbsess.query(Network).filter(Network.interface==ifname)
    for k in filter.keys():
        exec 'data = data.filter(Network.%s==filter["%s"])' % (k,k)
    if data.count() > 0:
        return data.one()
    else:
        return False

def retrieve_network_rows(cfg, hwtag=None, serverid=None):
    data = cfg.dbsess.query(Network)
    if hwtag:       data = data.filter(Network.hw_tag==hwtag)
    if serverid:    data = data.filter(Network.server_id==serverid)
    return data.all()

def retrieve_next_virtual_ip(cfg, vlan, autogen=False):
    for next in cfg.dbsess.query(Network).\
        filter(Network.server_id==cfg.dbnull).\
        filter(Network.hw_tag==cfg.dbnull).\
        filter(Network.vlan==vlan).\
        order_by(Network.ip).all():
        pingcheck = os.popen("ping -q -c2 -t2 "+next.ip,"r")
        while 1:
            line = pingcheck.readline()
            if not line: break
            match = re.findall(re.compile(r"(\d)( packets)? received"),line)
            if match:
                if int(match[0][0]) == 0:
                    return next.ip
    if autogen:
        ip,realm,site_id = calculate_last_virtual_ipaddress(cfg, vlan)
        generate_ipaddress_range(cfg, ip, count=5, realm=realm, site_id=site_id)
        return cfg.dbsess.query(Network).\
            filter(Network.server_id==cfg.dbnull).\
            filter(Network.hw_tag==cfg.dbnull).\
            filter(Network.vlan==vlan).\
            order_by(Network.ip).first().ip
    return False

def retrieve_server_dict(cfg, hostname):
    unqdn = '.'.join(mothership.get_unqdn(cfg, hostname))
    empty = False
    try:
        values = retrieve_server_row_by_unqdn(cfg, unqdn).__dict__.copy()
    except:
        values = Server.__dict__.copy()
        empty = True
    for k in values.keys():
        if empty: values[k] = None
        if k.startswith('_'): del values[k]
    return values

def retrieve_server_row_by_unqdn(cfg, unqdn):
    hostname,realm,site_id  = mothership.get_unqdn(cfg, unqdn)
    try:
        data = cfg.dbsess.query(Server).\
            filter(Server.hostname==hostname).\
            filter(Server.realm==realm).\
            filter(Server.site_id==site_id).\
            one()
        return data
    except:
        return None

def retrieve_ssh_data(results, cmd, virtual=False):
    parsers = [
        #r'(^core\sid\s+:\s(?P<coreid>\d+))',
        #r'(^siblings\s+:\s+(?P<threads>\d+))',
        r'(^processor\s+:\s+(?P<cpus>\d+))',
        r'(^physical\sid\s+:\s(?P<chips>\d+))',
        r'(^cpu\scores\s+:\s(?P<cores>\d+))',
        r'(^cpu_count\s+:\s(?P<cpus>\d+))',
        r'(^MemTotal:\s+(?P<ram>\d+)\skB)',
        r'(\s+memory-total.+:\s(?P<xeram>\d+))',
        r'(^Disk.+,\s(?P<disk>\d+))',
        #r'(^Disk\s\/dev\/\w+:.+,\s(?P<disk>\d+)\sbytes)',
        #r'(^\sgeometry.+sectors\s=\s(?P<disk>\d+))',
        ]

    stat = {}
    info = os.popen(cmd,"r")
    while 1:
        line = info.readline()
        if not line: break
        for pattern in parsers:
            match = re.search(pattern, line)
            if match:
                for key in match.groupdict().keys():
                    if key.startswith('c'):
                        if key not in stat or int(stat[key]) <= int(match.group(key)):
                            stat[key] = str(int(match.group(key)) + 1)
                    elif key.startswith('xe'):
                        results[key.replace('xe','')]['host'] = str(int(match.group(key))/1024)
                    else:
                        results[key]['host'] = match.group(key)
    if not virtual:
        if 'cpus' in stat:
            # xenservers only list the number of cpus, not cores
            # so assume fixed divisor, like 2, to offset hyperthreading
            results['cores']['host'] = str(int(stat['cpus'])/2)
        elif 'chips' in stat:
            results['cores']['host'] = str(int(stat['chips'])*int(stat['cores']))
    else:
        # therefore, we must recalculate the cpus for cobbler or
        # the cores defined for virtuals will be inaccurate
        results['cores']['host'] = stat['cpus']

    # Check if matched using standard equality
    for key in results.keys():
        if 'host' not in results[key].keys(): continue
        if int(results[key]['database']) == int(results[key]['host']):
            results[key]['match'] = True
        else:
            results[key]['match'] = False
            if not virtual:
                pct = int(results[key]['host']) * 100 / int(results[key]['database'])
                #print 'percentage of %s: %d' % (key, pct)
                # for baremetal, within 90% should be sufficient
                if pct > 90 and pct < 100:
                    results[key]['match'] = True
    return results

def swap_server(cfg, when, hosts=[]):
    swaplist = []
    for hostname in hosts:
        hostdict = retrieve_server_dict(cfg, hostname)
        swaplist.append(hostdict)
    # Confirm that both hosts not NOT virtual
    for s in swaplist:
        if s['virtual']:
            print 'Only baremetal hosts can be swapped!'
            return
    if swaplist[0]['realm'] != swaplist[1]['realm']:
        print 'Swap hosts must be in the same realm!'
        return
    if swaplist[0]['site_id'] != swaplist[1]['site_id']:
        print 'Swap hosts must have the same site_id!'
        return
    # First, copy them to the server_graveyard
    for i in range(0,len(swaplist)):
        del swaplist[i]['id']
        swaplist[i]['deprovision_date'] = when
        insert_server_into_graveyard(cfg, swaplist[i]) # Insert into server graveyard
    print 'Swapping hardware for ' + ' and '.join(hosts)
    # Rename server0 to tmpserver0, server1 to server0, then tmpserver0 to server1
    modify_server_column(cfg, hosts[0],
        'hostname', 'tmp'+swaplist[0]['hostname'], force=True)
    modify_server_column(cfg, hosts[1],
        'hostname', swaplist[0]['hostname'], force=True)
    modify_server_column(cfg, 'tmp'+hosts[0],
        'hostname', swaplist[1]['hostname'], force=True)

def update_table_hardware(cfg, info, when):
    data = retrieve_hardware_row(cfg, info['hw_tag'])
    if not data:
        info.update({'purchase_date':when, 'rma':False})
        # insert if it does not exist
        print 'Inserting into hardware table'
        data = Hardware(info['hw_tag'])
    else:
        print 'Updating hardware table'
    for k in info.keys():
        setattr(data, k, info[k])
    if not data.id:
        cfg.dbsess.add(data)
    cfg.dbsess.commit()

def update_table_network(cfg, info, noinsert=False):
    data = None
    for key in ['mac', 'ip', 'hw_tag', 'server_id']:
        if not data and key in info:
            data = retrieve_network_row_by_ifname(cfg,
                info['interface'], filter={key:info[key]})
    if not data:
        if noinsert:
            return
        # insert if it does not exist and noinsert=False
        print 'Inserting into network table'
        if 'ip' not in info:
            info.update({'ip':None, 'netmask':None})
        data = Network(info['ip'], info['interface'],
               info['netmask'], info['mac'])
    else:
        print 'Updating network table'
    for k in info.keys():
        setattr(data, k, info[k])
    if not data.id:
        cfg.dbsess.add(data)
    cfg.dbsess.commit()

def update_table_server(cfg, info, when=None, rename=None):
    unqdn =  '%s.%s.%s' % (info['hostname'], info['realm'], info['site_id'])
    data = retrieve_server_row_by_unqdn(cfg, unqdn)
    if rename: unqdn = '.'.join(mothership.get_unqdn(cfg, rename))
    if not data:
        # insert if it does not exist
        print 'Inserting into server table'
        data = Server(unqdn)
    else:
        print 'Updating server table'
    if 'purchase_date' not in dir(data):
        setattr(data, 'purchase_date', when)
    for k in info.keys():
        setattr(data, k, info[k])
    if not data.id:
        cfg.dbsess.add(data)
    cfg.dbsess.commit()
    ans = retrieve_server_row_by_unqdn(cfg, unqdn)
    return ans.id, ans.hw_tag

def verify_host_data(cfg, hostname):
    host,realm,site_id = mothership.get_unqdn(cfg, hostname)
    virtual = False
    results = {}
    tests = {
        'cores': 1,
        'ram': 1024 * 1024,
        'disk': 1024 * 1024 * 1024,
    }
    print 'Verifying %s' % host
    q = cfg.dbsess.query(Server).\
        filter(Server.hostname==host).\
        filter(Server.realm==realm).\
        filter(Server.site_id==site_id).\
        one().__dict__

    if q['virtual']:
        virtual = True
        hddev = 'xvda'
        for k in q.keys():
            if k in tests.keys():
                if not q[k]:
                    dbv = 0
                else:
                    dbv = q[k]
                #print '%s: %s' % (k, dbv * tests[k])
                if k not in results.keys(): results[k] = {}
                results[k]['database'] = dbv * tests[k]
    else:
        hddev = 'sda'
        h = cfg.dbsess.query(Hardware).filter(Hardware.hw_tag==q['hw_tag']).one().__dict__
        for k in h.keys():
            if k in tests.keys():
                if not h[k]:
                    dbv = 1
                else:
                    dbv = h[k]
                    if k == 'disk':
                        match = re.search('(\d+)\sx\s(\d+)GB\s(\w+)', h[k])
                        if match:
                            if match.group(3) == 'SATA':
                                dbv = int(match.group(1)) * int(match.group(2))
                            elif match.group(3) == 'SAS':
                                dbv = int(match.group(1))/2 * int(match.group(2))
                if k not in results.keys(): results[k] = {}
                #print '%s: %s' % (k, dbv)
                results[k]['database'] = dbv * tests[k]
    #print results
    if q['cobbler_profile'].startswith('xen'):
        # Xenservers /proc/???info is not accurate, must use the XE command
        results = retrieve_ssh_data(results, "ssh %s sudo xe host-cpu-info" % host)
        info = os.popen("ssh %s sudo xe host-list name-label=%s params=uuid" % (host, host),"r")
        match = re.search('^uuid.+:\s*([-\w]+)', info.readline())
        if match:
            uuid = match.group(1)
            results = retrieve_ssh_data(results, "ssh %s sudo xe host-param-list uuid=%s" % (host, uuid))
    else:
        results = retrieve_ssh_data(results, "ssh %s cat /proc/???info" % hostname, virtual)
    #results = retrieve_ssh_data(results, "ssh %s sudo /sbin/hdparm -g /dev/%s" % (hostname, hddev))
    results = retrieve_ssh_data(results, "ssh %s sudo /sbin/fdisk -l /dev/%s" % (hostname, hddev))
    print '%15s' % 'ATTRIBUTE' ,
    header = False
    for row in sorted(results.keys()):
        if not header:
            for col in sorted(results[row].keys()):
                print '%15s' % col.upper() ,
        header = True
        print '\n%15s' % row ,
        for col in sorted(results[row].keys()):
            print '%15s' % results[row][col] ,
    print
    
def split_fqdn(fqdn):
    """
    Unpack fully qualified domain name parts.
    """
    if not fqdn:
        return [None] * 3
    parts = fqdn.split(".")
    return [None] * (3 - len(parts)) + parts[0:3]

def add_ldap_groups(hostname, realm, site_id):
    groups = []
    if hostname and realm and site_id:
        groups.append("%s_%s_%s" % (hostname, realm, site_id))
    if realm and site_id:
        groups.append("%s_%s" % (realm, site_id))
    groups.append("%s" % (site_id))
    return groups

def get_unqdn(cfg, name):
    """
    Append domains from search path to complete unqdn.
    """
    if re.search(r'[^\da-zA-Z\.\-]', name):
        print 'Invalid DNS characters in hostname: %s' % name
        sys.exit(1)
    parts = name.split(".")

    if len(parts) > 3:
        return split_fqdn(name)

    search_path = cfg.search_path

    for domain in search_path:
        if len(domain) + len(parts) == 3:
            break

    return parts + domain

def is_unqdn(cfg, name):
    """
    Returns True if name has enough elements to
    be a unqdn (hostname.realm.site_id)
    False otherwise
    """
    parts = name.split(".")
    if len(parts) >= 3:
        return True
    else:
        return False

# sort list items by the numbers within their strings (for hostname ordering)
def numSort(x,y):
    def getNum(str): return float(re.findall(r'\d+',str)[0])
    return cmp(getNum(x), getNum(y))

# writes out a capistrano config file
def cap_write_config(cfg):
    # declarin'
    tag_map = {}

    # Gather tag info 
    tags = cfg.dbsess.query(Tag)
    for tag in tags:
      servers = []
      for serv in cfg.dbsess.query(Server).\
      filter(Server.tag==tag.name):
        servers.append(serv.hostname)
      tag_map[tag.name] = servers

    tags = tag_map.keys()
    tags.sort()
    for tag in tags:
      collector = []
      python_strings_suck_so_very_hard = "tag :"+tag
      sorted_servers = tag_map[tag]
      sorted_servers.sort(numSort)
      for servers in sorted_servers:
        if servers:
          collector.append(", '"+servers+"'")
      buf = "".join(collector)
      if buf:
        print python_strings_suck_so_very_hard + buf

