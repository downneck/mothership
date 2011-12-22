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
    mothership.snmp

    Package for interacting with the snmp in mothership
"""

# imports
import mothership.network_mapper
import mothership
import subprocess
import sys


def walk_snmp_dict_oid_match(cfg, snmp_dict, oid, inkey, outkey, debug=False):
    info = walk_snmp_with_oid(cfg, '%s.%s' % (oid, snmp_dict[inkey]),
        vlan=snmp_dict['vlan'], switch=snmp_dict['switch'], debug=debug)[0]
    match = re.search('(INTEGER|STRING):\s(?P<match>.+)$', info['snmp'])
    snmp_dict[outkey] = match.group('match')
    if not snmp_dict['switch']: snmp_dict['switch'] = info['switch']
    return snmp_dict

def walk_snmp_for_network(cfg, ifobj, debug=False):
    if not ifobj.vlan:
        sys.stderr.write(' interface: %s (empty vlan)\n' % ifobj.interface)
        return False
    # pinging the interface first, helps with the mac snmpwalk
    if ifobj.ip:
        subprocess.Popen(['ping', '-qc1', ifobj.ip],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    snmp_dict = walk_snmp_for_mac_port_name(cfg,
        ifobj.vlan, ifobj.mac, debug=debug)
    snmp_dict['nic'] = ifobj.interface
    return snmp_dict

def walk_snmp_for_ifname(cfg, hostname, ifname=None, debug=False):
    unqdn = '.'.join(mothership.get_unqdn(cfg, hostname))
    print '\n  hostname: %s' % unqdn
    data = []
    if ifname:
        snmp_dict = walk_snmp_for_network(cfg,
            mothership.retrieve_network_row_by_ifname(cfg, ifname, filter={
                'server_id':mothership.retrieve_server_row_by_unqdn(cfg,
                unqdn).id}), debug)
        if snmp_dict:
            data.append(snmp_dict)
    else:
        for i in mothership.retrieve_network_rows(cfg,
            serverid=mothership.retrieve_server_row_by_unqdn(cfg, unqdn).id):
            snmp_dict = walk_snmp_for_network(cfg, i,  debug=debug)
            if snmp_dict:
                data.append(snmp_dict)
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
            for line in walk_snmp_with_oid(cfg, o['oid'],
                vlan=v['vlan'], switch=v['switch']):
                match = re.search(o['oid']+o['re'], line['snmp'])
                if match:
                    if not key: key = sorted(match.groupdict().keys())[0]
                    tmplist.append(match.groupdict())
        if key:
            snmplist = merge_dictlists(snmplist, tmplist, key)
    return snmplist

def walk_snmp_for_mac_port_name(cfg, vlan, mac, debug=False):
    data = { 'mac':mac, 'mac_oid':mothership.network_mapper.mac_to_oid(mac),
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
                'mac_oid':mothership.network_mapper.mac_to_oid(mac),
                'interface':mothership.network_mapper.remap(cfg, 'nic', vlan=vlan)
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
            if p:
                valid = True
                for x in cfg.snmpskip:
                    if str(x) in p:
                        valid = False
                if valid: data.append({'snmp':p, 'switch':host})
    return data

