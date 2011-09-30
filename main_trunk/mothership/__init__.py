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
import network_mapper
import os
import re
import subprocess
import sys
import types

import mothership.kv
import mothership.list_values
import mothership.users
import mothership.validate

from mothership_models import *
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

    ans = raw_input("to delete tag \"%s\" please type \"delete_%s\": " % (name, name))
    if ans != "delete_%s" % name:
        raise MothershipError("aborted by user")
    else:
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
        ip,site_id = network_mapper.remap(cfg, ['1st_dyn_ip','siteid'], vlan=int(vlan))
        return ip, 'prod', site_id

def calculate_next_baremetal_vlan_ipaddress(cfg, vlan):
    data = cfg.dbsess.query(Network).\
        filter(Network.vlan==vlan).\
        filter(Network.ip!=cfg.dbnull).\
        filter(Network.hw_tag!=cfg.dbnull)
    try:
        first = data.order_by(Network.ip).first().ip
        last = data.order_by(Network.ip.desc()).first().ip
    except:
        first = network_mapper.remap(cfg, '1st_static_ip', vlan=int(vlan))
        last = first

    # compare the sequential list to the shiplist
    shiplist = []
    for i in data.order_by(Network.ip).all():
        shiplist.append(i.ip)

    # determine the next free ip and return it
    nextip = None
    for i in network_mapper.generate_ipaddress_list(first, last=last):
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
        nextip = network_mapper.next_ip(last)
    return nextip

def clear_empty_keys_from_dict(dict):
    clean = dict.copy()
    for k in dict.keys():
        if dict[k] == '':
            del clean[k]
    return clean

def clear_serverinfo_from_network(cfg, server_id):
    # remove the public_ip first
    #cfg.dbconn.execute(Network.__table__.update().\
    #    where(Network.server_id==server_id).\
    #    values(public_ip=cfg.dbnull))
    # set the server_id to null
    #cfg.dbconn.execute(Network.__table__.update().\
    #    where(Network.server_id==server_id).\
    #    values(server_id=cfg.dbnull))
    # remove specific columns, then remove the server_id
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

def console_hostname(cfg, hostname):
    if cfg.dbsess.query(Server).filter(Server.hostname==hostname).one().virtual:
        for xen in cfg.dbsess.query(Server,Network).\
            filter(Server.id==Network.server_id).\
            filter(Server.cobbler_profile.like('xenserver%')).\
            filter(Network.interface=='eth0').\
            all():
            ### TODO: need to get the correct domid and run:
            #ssh root@$xen /usr/lib/xen/bin/xenconsole $domid
            #result = o.system('/usr/bin/ssh root@%s xe vm-list name-label=%s params=dom-id' % (xen.Network.ip, hostname))
            #if result: break
            if xen or True:
                print 'This feature not currently active'
    else:    # baremetal machine
        dracip = cfg.dbsess.query(Server,Network).\
            filter(Server.id==Network.server_id).\
            filter(Server.hostname==hostname).\
            filter(Network.interface=='drac').\
            one().Network.ip
        os.system('echo /usr/bin/ipmitool -U %s -P %s -H %s -Ilanplus sol activate' %
            (cfg.puser, cfg.ppass, dracip))

def convert_drac_dict_to_network(cfg, drac_sysinfo, ip):
    siteid = drac_sysinfo['site_id']
    for k in drac_sysinfo.keys():
        netdrac_sysinfo = drac_sysinfo.copy()
        if not k.startswith('eth') and k != 'drac': continue
        net = network_mapper.remap(cfg, ['vlan','mask','ip'], nic=k, siteid=siteid)
        dracip = network_mapper.remap(cfg, 'ip', nic='drac', siteid=siteid)
        if net:
            if k!='eth1': # due to multiple vlans
                if ip.startswith(dracip):
                    netdrac_sysinfo.update({'ip':ip.replace(dracip,net[2])})
                netdrac_sysinfo.update({'vlan':net[0], 'netmask':net[1]})
        netdrac_sysinfo.update({'interface':k, 'mac':netdrac_sysinfo[k]})
        update_table_network(cfg, netdrac_sysinfo)

def convert_table_objects_to_dict(tables):
    d = {}
    for table in tables.keys():
        for k in getattr(tables, table).__dict__.keys():
            if k.startswith('_') or k=='id':
                continue
            d[k] = getattr(tables,table).__dict__[k]
    return d

def count_nonempty_args(obj, boolean=False):
    count = 0
    if type(obj) is types.ListType or type(obj) is types.TupleType:
        for arg in obj:
            if boolean:
                if type(arg) is types.BooleanType and arg:
                    count += 1
            else:
                if arg != None:
                    count += 1
    elif type(obj) is types.DictType:
        for key in obj:
            if boolean:
                if type(obj[key]) is types.BooleanType and obj[key]:
                    count += 1
            else:
                if obj[key] != None:
                    count += 1
    return count

def count_graveyard_server_by_date(cfg, hostname, when):
    try:
        return cfg.dbsess.query(ServerGraveyard).\
            filter(ServerGraveyard.deprovision_date==when).\
            filter(ServerGraveyard.hostname==hostname).count()
    except:
        return 0

def delete_server(cfg, hostname, relatives=None):
    sid = cfg.dbsess.query(Server).filter(Server.hostname==hostname).one().id
    # mapper/delete-cascade does not seem to override foreign constraint, so
    # delete constrained foreign keys first, replace if better method found
    for r in relatives:
        print 'Deleting %s records that are related to server_id %d' % (r, sid)
        cfg.dbconn.execute(r.delete().where(Column('server_id')==sid))
    # Then remove the servers record
    print 'Deleting %s (id=%d) from servers' % (hostname, sid)
    return cfg.dbconn.execute(Server.__table__.delete().\
        where(Server.hostname==hostname))

def expire_server(cfg, hostname, when, delete_entry=True):
    cols = retrieve_server_dict(cfg, hostname)
    if not cols['id']:
        print 'There is no server named %s to delete' % hostname
        return
    cols['delid'] = cols['id']
    del cols['id']
    cols['deprovision_date'] = when
    # retrieve all server_id related info and display
    print '\nThe following info is related to %s (id=%d)' % (hostname, cols['delid'])
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
        print 'Inserting %s into server_graveyard' % hostname
        insert_server_into_graveyard(cfg, cols) # Insert into server graveyard
        # Check hostname exists in server_graveyard and continue only if found
        if count_graveyard_server_by_date(cfg, hostname, when) > 0:
            # clear server info from network table
            clear_serverinfo_from_network(cfg, cols['delid'])
            # Remove server from servers table and related tables
            delete_server(cfg, hostname, relatives)
            # remove the server's group
            try:
                server_groupname = hostname+"_"+cols['realm']+"_"+cols['site_id'] \
                    +"."+cols['realm']+"."+cols['site_id']
                mothership.users.gremove(cfg, server_groupname)
            except Exception, e:
                print e
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
    for ip in network_mapper.generate_ipaddress_list(first, count=count, last=last):
        vlan,mask,nic = network_mapper.remap(cfg, ['vlan','mask','nic'], ip=ip, siteid=site_id)
        update_table_network(cfg, { 'ip':ip, 'realm':realm, 'site_id':site_id,
            'mac':network_mapper.ip_to_mac(ip),
            'vlan':vlan, 'netmask':mask, 'interface':nic })

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
    return cfg.dbconn.execute(ServerGraveyard.__table__.insert(), [ values ])

def merge_dictlists(master, slave, key):
    for m in master:
        for s in slave:
            if key not in m or key not in s:
                continue
            if m[key] == s[key]:
                m.update(s)
    return master

def modify_network_vlan(cfg, hostname, vlan, interface='eth1', force=False):
    ip = calculate_next_baremetal_vlan_ipaddress(cfg, vlan)
    try:
        data = cfg.dbsess.query(Server,Network).\
            filter(Server.hostname==hostname).\
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
    mask = network_mapper.remap(cfg, 'mask', ip=ip, nic=interface, siteid=data.site_id)
    gw = network_mapper.remap(cfg, 'gw', ip=ip, nic=interface, siteid=data.site_id)
    if not mask: mask = cfg.dbnull
    if not gw: gw = cfg.dbnull
    print 'Updating %s: setting %s to ip=%s on vlan=%s' \
            % (hostname, interface, ip, vlan)
    update_table_network(cfg, { 'ip':ip, 'server_id':data.server_id,
        'interface':interface, 'vlan':vlan, 'static_route':gw, 'netmask':mask })

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

def modify_server_column(cfg, hostname, col, value):
    data = retrieve_server_dict(cfg, hostname)
    # Since public+ip is not in the servers table, retrieve it from network
    data['public_ip'] = retrieve_network_dict_by_ifname(cfg,
            'eth1', 'server_id', data['id'])['public_ip']
    if not data['id']:
        print 'The server "%s" does not exist' % hostname
        return
    if col not in data:
        print 'The column "%s" does not exist' % col
        print 'This is the current layout of %s:\n' % hostname
        for k in data.keys():
            print '%15s: %-20s' % (k, data[k])
        return
    if data[col] == value:
        print 'No change needed.  For %s, %s is already %s' \
            % (hostname, col, data[col])
        return
    print 'Please confirm the following change:\n'
    for k in data.keys():
        if k == col:
            print '%15s: %-20s --> %15s: %-20s' % (k, data[k], k, value)
        else:
            print '%15s: %-20s     %15s: %-20s' % (k, data[k], k, data[k])
    ans = raw_input('\nTo confirm this change, type "modify_%s": ' % col)
    if ans != 'modify_%s' % col:
        print 'Modification of "%s" column in server %s aborted.' % (col, hostname)
        return
    data[col] = value
    if col == 'public_ip':
        update_table_network(cfg, { 'server_id':data['id'], 'interface':'eth1', col:value })
    else:
        update_table_server(cfg, data)
    print 'Modification of "%s" column in server %s complete.' % (col, hostname)

def provision_server(cfg, fqdn, vlan, when, osdict, public_ip='', tag=None,
    hwtag=None, dracip=None, mgmtip=None, osname=None, specs=None):
    if specs is None:
        specs = {'cpu':None, 'ram':None, 'disk':None}
    if not is_unqdn(cfg, fqdn):
        print 'fqdn MUST contain hostname.realm.site_id'
        return
    hostname,realm,site_id = split_fqdn(fqdn)
    try:    # check to see if server hostname exists
        retrieve_server_row(cfg, hostname)
        print '%s already provisioned, skipping' % hostname
        return
    except:
        # new = True
        pass

    # set the primary tag to be the hostname without the trailing integers
    if not tag:
        tag = re.sub('\d+$', '', hostname)
    # check to make sure that the tag is valid before proceeding
    try:
        cfg.dbsess.query(Tag).filter(Tag.name==tag).one()
    except:
        print '%s is not a valid tag, provisioning of %s aborted' % (tag, hostname)
        return

    virtual = False

    if not hwtag:
        # see which identifier was passed to us
        if dracip:
            try:
                hwtag = cfg.dbsess.query(Network).\
                    filter(Network.interface=='drac').\
                    filter(Network.ip==dracip).one().hw_tag
            except:
                print 'No hardware found with drac ip = %s' % dracip
        elif mgmtip:
            try:
                hwtag = cfg.dbsess.query(Network).\
                    filter(Network.interface=='eth0').\
                    filter(Network.ip==mgmtip).one().hw_tag
            except:
                print 'No hardware found with management ip = %s' % mgmtip
        elif vlan:
            try:
                hwtag = cfg.dbsess.query(Server,Network).\
                    filter(Network.vlan==vlan).\
                    filter(Server.id==Network.server_id).\
                    filter(Server.cobbler_profile.like('xenserver%')).\
                    first().Server.hw_tag
            except:
                print 'No xenserver on vlan %s to add virtual host' % vlan
                return
            virtual = True
            profile = osdict['default']['virtual']

    if not virtual:
        try:    # check to see if hwtag already belongs to a server
            check = retrieve_network_row_by_ifname(cfg, 'eth0', hwtag=hwtag)
            if check.server_id:
                print '%s already provisioned as server id %s' % (hwtag, check.id)
                return
        except:
            print 'Hardware tag %s does NOT exist in mothership' % hwtag
            return
        if hostname.startswith('xen'):    # xen server
            profile = osdict['default']['xenserver']
        else:                             # default
            profile = osdict['default']['baremetal']

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

    if virtual:
        # make sure the vlan specified is primary eth1
        if network_mapper.remap(cfg, 'nic', vlan=int(vlan), siteid=site_id) != 'eth1':
            print 'Please specify the primary vlan for eth1 for virtual hosts'
            return
        # if specs are not provided, get the minimum values from configuration
        for key in cfg.vm_spec.keys():
            if specs[key] is None:
                specs[key] = cfg.vm_spec[key]
        # check eth1 and eth0 for valid ips before continuing
        ip = []
        vlist = [ network_mapper.remap(cfg, 'vlan', nic='eth0', siteid=site_id), vlan ]
        for v in vlist:
            ip.append(retrieve_next_virtual_ip(cfg, v, autogen=True))
        sid,hwtag = update_table_server(cfg, { 'hostname':hostname, 'hw_tag':hwtag, 'realm':realm,
            'site_id':site_id, 'cobbler_profile':profile, 'os':osprofile, 'virtual':virtual,
            'tag':tag, 'cores':specs['cpu'], 'ram':specs['ram'], 'disk':specs['disk'] }, when)
        update_table_network(cfg, { 'server_id':sid,
            'static_route':network_mapper.remap(cfg, 'gw', nic='eth1', ip=ip[1], siteid=site_id),
            'netmask':network_mapper.remap(cfg, 'mask', nic='eth1', ip=ip[1], siteid=site_id),
            'interface':'eth1', 'ip':ip[1] })
        update_table_network(cfg, {'server_id':sid, 'interface':'eth0', 'ip':ip[0]})
        print 'Added virtual host %s to mothership' % hostname
    else:
        # check to make sure that hardware is not marked for RMA
        data = retrieve_hardware_row(cfg, hwtag)
        if data.rma:
            print '%s is marked for RMA so cannot be provisioned' % hwtag
            return
        # update server table and retrieve the server_id
        sid,hwtag = update_table_server(cfg, { 'hostname':hostname, 'tag':tag,
            'hw_tag':hwtag, 'realm':realm, 'site_id':site_id, 'os':osprofile,
            'cobbler_profile':profile, 'virtual':virtual }, when)
        # update the server_id in the network table rows and return the id
        for net in retrieve_network_rows(cfg, hwtag=hwtag):
            ip = None
            if net.interface == 'eth1':
                ip = calculate_next_baremetal_vlan_ipaddress(cfg, vlan)
            # never retrieve the gw without ip=, especially when eth1
            gw = network_mapper.remap(cfg, 'gw', ip=ip, nic=net.interface, siteid=site_id)
            mask = network_mapper.remap(cfg, 'mask', ip=ip, nic=net.interface, siteid=site_id)
            if not mask: mask = cfg.dbnull
            if not gw: gw = cfg.dbnull
            if not ip: ip = cfg.dbnull
            update_table_network(cfg, { 'interface':net.interface, 'ip': ip,
                'hw_tag':hwtag, 'server_id':sid, 'static_route':gw, 'netmask':mask })
            if re.match('eth[12]', net.interface):
                update_table_network(cfg, { 'interface':net.interface,
                    'hw_tag':hwtag, 'bond_options':'mode=active-backup miimon=10' })
        print 'Added baremetal host %s to mothership' % hostname

    # insert vlan public_ip into network table
    if not public_ip or network_mapper.remap(cfg, 'ip', ip=public_ip):
        print 'Invalid public_ip %s, using default %s' % (public_ip, cfg.def_public_ip)
        public_ip = cfg.def_public_ip
    update_table_network(cfg, { 'server_id':sid, 'vlan': vlan,
        'interface':'eth1', 'public_ip':public_ip })

    # create a group for the new machine
    newgroupname = hostname+"_"+realm+"_"+site_id
    g = cfg.dbsess.query(Groups).\
    filter(Groups.groupname==newgroupname).\
    filter(Groups.realm==realm).\
    filter(Groups.site_id==site_id).first()
    if g:
        print "group exists, skipping: %s" % newgroupname
    else:
        mothership.users.gadd(cfg, newgroupname+"."+realm+"."+site_id)
    return sid

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


def remove_method_keys(dict, empty=False):
    for k in dict.keys():
        if empty: dict[k] = None
        if k.startswith('_'): del dict[k]
    return dict

def retrieve_cobbler_network_rows(cfg, hostname):
    return cfg.dbsess.query(Server,Network).\
            filter(Server.hostname==hostname).\
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
        sysdict['power_type'] = 'xenserver'
        power = cfg.dbsess.query(Server,Network).\
            filter(Network.vlan==netdict['eth1']['vlan']).\
            filter(Server.id==Network.server_id).\
            filter(Server.cobbler_profile.like('xenserver%'))
        if xen:
            power = power.filter(Server.hostname==xen)
        try:
            sysdict['power_switch'] = power.first().Server.hostname + '.mgmt'
        except:
            print "Server %s not found or not part of vlan %s" % (xen,netdict['eth1']['vlan'])
            sys.exit(1)
    else:
        sysdict['power_type'] = 'ipmitool'
    return sysdict

def retrieve_cobbler_system_row(cfg, hostname):
    try:
        return cfg.dbsess.query(Server,Hardware).\
            filter(Server.hostname==hostname).\
            filter(Server.hw_tag==Hardware.hw_tag).one()
    except:
        print "Server %s not found in cobbler database" % hostname
        sys.exit(1)

def retrieve_fqdn(cfg, hostname, interface='eth1'):
    q = retrieve_server_dict(cfg, hostname)
    append = network_mapper.remap(cfg, 'dom', nic=interface, siteid=q['site_id'])
    return hostname + append

def retrieve_hardware_dict(cfg, hwtag):
    empty = False
    try:
        values = retrieve_hardware_row(cfg, hwtag).__dict__.copy()
    except:
        values = Hardware.__dict__.copy()
        empty = True
    return remove_method_keys(values, empty)

def retrieve_hardware_row(cfg, hwtag):
    try:
        return cfg.dbsess.query(Hardware).filter(Hardware.hw_tag==hwtag).one()
    except:
        print "hwtag %s not found in database" % hwtag
        sys.exit(1)

def retrieve_network_dict_by_hwtag(cfg, hwtag, ifname):
    empty = False
    try:
        values = retrieve_network_row_by_ifname(cfg, ifname, hwtag=hwtag).\
            __dict__.copy()
    except:
        values = Network.__dict__.copy()
        empty = True
    return remove_method_keys(values, empty)

def retrieve_network_dict_by_ipaddress(cfg, ip, ifname):
    empty = False
    try:
        values = retrieve_network_row_by_ifname(cfg, ifname, ip=ip).\
            __dict__.copy()
    except:
        values = Network.__dict__.copy()
        empty = True
    return remove_method_keys(values, empty)

def retrieve_network_dict_by_serverid(cfg, serverid, ifname):
    empty = False
    try:
        values = retrieve_network_row_by_ifname(cfg, ifname, serverid=serverid).\
            __dict__.copy()
    except:
        values = Network.__dict__.copy()
        empty = True
    for k in values.keys():
        if empty: values[k] = None
        if k.startswith('_'): del values[k]
    return values

def retrieve_network_dict_by_ifname(cfg, ifname, key, value):
    empty = False
    try:
        if key == 'mac':
            values = retrieve_network_row_by_ifname(cfg, ifname,
                mac=value).__dict__.copy()
        elif key == 'ip':
            values = retrieve_network_row_by_ifname(cfg, ifname,
                ip=value).__dict__.copy()
        elif key == 'hw_tag':
            values = retrieve_network_row_by_ifname(cfg, ifname,
                hwtag=value).__dict__.copy()
        elif key == 'server_id':
            values = retrieve_network_row_by_ifname(cfg, ifname,
                serverid=value).__dict__.copy()
    except:
        values = Network.__dict__.copy()
        empty = True
    for k in values.keys():
        if empty: values[k] = None
        if k.startswith('_'): del values[k]
    return values

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
            network_rows = retrieve_network_row_by_ifname(cfg, interface, serverid = server_id)
        else:
            network_rows = retrieve_network_rows(cfg, serverid = server_id)
        return network_rows
    else:
        return []

def retrieve_network_rows_by_servername(cfg, hostname):
    """
        Retrieve all network rows associated with a particular hostname
    """
    server = retrieve_server_row(cfg, hostname)
    if server:
        server_id = server.id
        network_rows = retrieve_network_rows(cfg, serverid = server_id)
        return network_rows
    else:
        return []

def retrieve_network_row_by_ifname(cfg, ifname, hwtag=None, ip=None, mac=None, serverid=None):
    data = cfg.dbsess.query(Network).filter(Network.interface==ifname)
    if hwtag:       data = data.filter(Network.hw_tag==hwtag)
    if ip:          data = data.filter(Network.ip==ip)
    if mac:         data = data.filter(Network.mac==mac)
    if serverid:    data = data.filter(Network.server_id==serverid)
    return data.one()

def retrieve_network_rows(cfg, hwtag=None, serverid=None):
    data = cfg.dbsess.query(Network)
    if hwtag:       data = data.filter(Network.hw_tag==hwtag)
    if serverid:    data = data.filter(Network.server_id==serverid)
    return data.all()

def retrieve_next_virtual_ip(cfg, vlan, autogen=False):
    # retrieve the next available ip, assuming that it will be unused
    #next = cfg.dbsess.query(Network).\
    #    filter(Network.server_id==cfg.dbnull).\
    #    filter(Network.hw_tag==cfg.dbnull).\
    #    filter(Network.vlan==vlan)
    #if next.first():
    #    return next.order_by(Network.ip).first().ip
    # loop thru available ip and check ping before returning
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
    empty = False
    try:
        values = retrieve_server_row(cfg, hostname).__dict__.copy()
    except:
        values = Server.__dict__.copy()
        empty = True
    for k in values.keys():
        if empty: values[k] = None
        if k.startswith('_'): del values[k]
    return values

def retrieve_server_row(cfg, hostname):
    try: 
        return cfg.dbsess.query(Server).filter(Server.hostname==hostname).one()
    except:
        print "Server %s not found in database" % hostname
        sys.exit(1)

def retrieve_server_rows(cfg, hostname):
    try: 
        return cfg.dbsess.query(Server).filter(Server.hostname==hostname).all()
    except:
        print "Server %s not found in database" % hostname
        sys.exit(1)

def retrieve_server_row_by_unqdn(cfg, unqdn):
    hostname,realm,site_id  = mothership.get_unqdn(cfg, unqdn)
    row = cfg.dbsess.query(Server).\
        filter(Server.hostname==hostname).\
        filter(Server.realm==realm).\
        filter(Server.site_id==site_id)
    return row.one()

def retrieve_ssh_data(results, cmd, virtual=False):
    parsers = [
#        r'(^core\sid\s+:\s(?P<coreid>\d+))',
#        r'(^siblings\s+:\s+(?P<threads>\d+))',
        r'(^processor\s+:\s+(?P<cpus>\d+))',
        r'(^physical\sid\s+:\s(?P<chips>\d+))',
        r'(^cpu\scores\s+:\s(?P<cores>\d+))',
        r'(^cpu_count\s+:\s(?P<cpus>\d+))',
        r'(^MemTotal:\s+(?P<ram>\d+)\skB)',
        r'(\s+memory-total.+:\s(?P<xeram>\d+))',
        r'(^Disk.+,\s(?P<disk>\d+))',
#        r'(^Disk\s\/dev\/\w+:.+,\s(?P<disk>\d+)\sbytes)',
#        r'(^\sgeometry.+sectors\s=\s(?P<disk>\d+))',
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
    # First make both server aware of their old and new hw_tag
    for i in range(0,len(swaplist)):
        swaplist[i]['oldtag'] = swaplist[i]['hw_tag']
        swaplist[i]['newtag'] = swaplist[i^1]['hw_tag']
    # Second, copy them to the server_graveyard
    for i in range(0,len(swaplist)):
        del swaplist[i]['id']
        swaplist[i]['deprovision_date'] = when
        insert_server_into_graveyard(cfg, swaplist[i]) # Insert into server graveyard
    print 'Swapping hardware for ' + ' and '.join(hosts)
    # Finally, update servers table with newtag and network with newid
    for i in range(0,len(swaplist)):
        swaplist[i]['hw_tag'] = swaplist[i]['newtag']
        sid,hwtag = update_table_server(cfg, swaplist[i], when)
        for net in retrieve_network_rows(cfg, hwtag=hwtag):
            update_table_network(cfg, { 'interface':net.interface,
                'hw_tag':hwtag, 'server_id':sid })

def update_table_hardware(cfg, info, when):
    data = retrieve_hardware_dict(cfg, info['hw_tag'])
    if not data['purchase_date']: info['purchase_date'] = when
    if not data['rma']: info['rma'] = False
    if not data['id']:
        # insert if it does not exist
        print 'Inserting into hardware table'
        cfg.dbconn.execute(Hardware.__table__.insert(), [ info ])
    else:
        print 'Updating hardware table'
        cfg.dbconn.execute(Hardware.__table__.update().\
            where(Hardware.id==data['id']), [ info ])

def update_table_network(cfg, info, noinsert=False):
    data = { 'id':None }
    info = clear_empty_keys_from_dict(info)
    for key in ['mac', 'ip', 'hw_tag', 'server_id']:
        if not data['id'] and key in info:
            data = retrieve_network_dict_by_ifname(cfg,
                info['interface'], key, info[key])
    if not data['id']:
        if noinsert:
            return
        # insert if it does not exist and noinsert=False
        print 'Inserting into network table'
        cfg.dbconn.execute(Network.__table__.insert(), [ info ])
    else:
        print 'Updating network table'
        cfg.dbconn.execute(Network.__table__.update().\
            where(Network.id==data['id']), [ info ])

def update_table_server(cfg, info, when=None, rename=None):
    data = retrieve_server_dict(cfg, info['hostname'])
    if rename: info['hostname'] = rename
    if not data['provision_date']: info['provision_date'] = when
    if not data['id']:
        # insert if it does not exist
        print 'Inserting into server table'
        cfg.dbconn.execute(Server.__table__.insert(), [ info ])
    else:
        print 'Updating server table'
        cfg.dbconn.execute(Server.__table__.update().\
            where(Server.id==data['id']), [ info ])
    ans = retrieve_server_row(cfg, info['hostname'])
    return ans.id, ans.hw_tag

def walk_snmp_dict_oid_match(cfg, snmp_dict, oid, inkey, outkey, debug=False):
    info = walk_snmp_with_oid(cfg, '%s.%s' % (oid, snmp_dict[inkey]),
        vlan=snmp_dict['vlan'], switch=snmp_dict['switch'], debug=debug)[0]
    match = re.search('(INTEGER|STRING):\s(?P<match>.+)$', info['snmp'])
    snmp_dict[outkey] = match.group('match')
    if not snmp_dict['switch']: snmp_dict['switch'] = info['switch']
    return snmp_dict

def walk_snmp_for_ifname(cfg, hostname, ifname=None, debug=False):
    print '\n  hostname: %s' % hostname
    data = []
    if ifname:
        i = retrieve_network_row_by_ifname(cfg, ifname,
            serverid=retrieve_server_row(cfg, hostname).id)
        snmp_dict = walk_snmp_for_mac_port_name(cfg, i.vlan, i.mac, debug=debug)
        snmp_dict['nic'] = ifname
        data.append(snmp_dict)
        # pinging the interface first, helps with the mac snmpwalk
        subprocess.Popen(['ping', '-qc1', i.ip],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        for i in retrieve_network_rows(cfg,
            serverid=retrieve_server_row(cfg, hostname).id):
            snmp_dict = walk_snmp_for_mac_port_name(cfg, i.vlan, i.mac, debug=debug)
            snmp_dict['nic'] = i.interface
            data.append(snmp_dict)
            subprocess.Popen(['ping', '-qc1', i.ip],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return data

def walk_snmp_for_mac_port_list(cfg, vlist, snmplist=[]):
    oid_list = [
        # keys will be alpha-sorted so name merge key[0] appropriately
        { 'oid':'.1.3.6.1.2.1.17.4.3.1.2', # OID: dot1dTpFdbPort
          're':r'\.(?P<mac_oid>[\d\.]+)\s.*:\s(?P<nbridge>\d+)' },
        { 'oid':'.1.3.6.1.2.1.17.1.4.1.2', # OID: dot1dBasePortIfIndex
          're':r'\.(?P<nbridge>\d+)\s.*:\s(?P<nindex>\d+)' },
        { 'oid':'.1.3.6.1.2.1.31.1.1.1.1', # OID: ifName.13617
          're': r'\.(?P<nindex>\d+)\s.*:\s(?P<switch_port>[\w\/]+)' },
        ]
    for o in oid_list:
        key = None
        tmplist = []
        for v in vlist:
            for line in walk_snmp_with_oid(cfg, o['oid'], vlan=v['vlan'], switch=v['switch']):
                match = re.search(o['oid']+o['re'], line['snmp'])
                if match:
                    if not key: key = sorted(match.groupdict().keys())[0]
                    tmplist.append(match.groupdict())
        if key:
            snmplist = merge_dictlists(snmplist, tmplist, key)
    return snmplist

def walk_snmp_for_mac_port_name(cfg, vlan, mac, debug=False):
    data = { 'mac':mac, 'mac_oid':network_mapper.mac_to_oid(mac),
        'vlan':vlan, 'switch':False }
    try:
        oid = '.1.3.6.1.2.1.17.4.3.1.2' # OID: dot1dTpFdbPort
        data = walk_snmp_dict_oid_match(cfg, data, oid,
            'mac_oid', 'bridge', debug=debug)
        oid = '.1.3.6.1.2.1.17.1.4.1.2' # OID: dot1dBasePortIfIndex
        data = walk_snmp_dict_oid_match(cfg, data, oid,
            'bridge', 'index', debug=debug)
        oid = '.1.3.6.1.2.1.31.1.1.1.1' # OID: ifName.13617
        data = walk_snmp_dict_oid_match(cfg, data, oid,
            'index', 'switch_port', debug=debug)
    except:
        if not data['switch']: data['switch'] = 'unknown'
    if 'switch_port' not in data: data['switch_port'] = 'disconnected'
    return data

def walk_snmp_for_vlan_ip_mac_list(cfg):
    # map all valid vlan/ip/mac to their switch
    snmplist = []
    oid = '.1.3.6.1.2.1.3.1.1.2' # OID: atPhysAddress
    for line in walk_snmp_with_oid(cfg, oid):
        match = re.search(oid+'\.(?P<vlan>\d+)\.1\.(?P<ip>\d+(\.\d+){3}).*:\s(?P<mac>.+)\s', line['snmp'])
        vlan = int(match.group('vlan'))
        if vlan in mothership.list_values.list_network_vlans(cfg):
            mac = match.group('mac').replace(' ',':').lower()
            snmplist.append({
                'mac':mac, 'vlan':vlan,
                'switch':line['switch'],
                'ip':match.group('ip'), 'mac':mac,
                'mac_oid':network_mapper.mac_to_oid(mac),
                'interface':network_mapper.remap(cfg, 'nic', vlan=vlan)
            })
    return snmplist

def walk_snmp_for_vlan_switch_list(cfg):
    # map all valid vlans to their switch
    vlan_switch_list = []
    oid = '.1.3.6.1.4.1.9.9.46.1.3.1.1.2.1' # OID: vtpVlanState
    for line in walk_snmp_with_oid(cfg, oid):
        match = re.search(oid+'.(?P<vlan>\d+)', line['snmp'])
        if int(match.group('vlan')) in mothership.list_values.list_network_vlans(cfg):
            vlan_switch_list.append({'switch':line['switch'],
                'vlan':int(match.group('vlan'))})
    return vlan_switch_list

def walk_snmp_with_oid(cfg, oid, vlan=None, switch=None, debug=False):
    walk = '/usr/bin/snmpwalk'
    opts = '-Ofn'
    vers = '-v%s' % cfg.snmpver
    cstr = '-c%s' % cfg.snmpread
    data = []
    for host in cfg.snmphosts:
        if switch and switch != host:
            continue
        if vlan is not None:
            cstr = '-c%s@%s' % (cfg.snmpread, vlan)
        for p in subprocess.Popen([walk, opts, vers, cstr, host, oid],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE).\
            communicate()[0].split('\n'):
            if debug:
                print 'DEBUG: %s %s %s %s %s %s' \
                % (walk, opts, vers, cstr, host, oid)
            if p: data.append({'snmp':p, 'switch':host})
    return data

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
    q = cfg.dbsess.query(Server).filter(Server.hostname==host).one().__dict__

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

