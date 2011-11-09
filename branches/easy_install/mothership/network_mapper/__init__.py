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
   The mothership.network_mapper module
"""

import re
import types
import socket
import struct


"""
    define custom ip functions below to avoid any licensing issues
"""
_netmasks = list(((0xffffffffL << x) & 0xffffffffL) for x in range(32,-1,-1))
def get_netmask(cidr):
    # the netmasks list is indexed by cidr
    return '.'.join(map(str, [ _netmasks[int(cidr.split('/')[1])] % (256**i) / (256**(i-1)) for i in range(4,0,-1) ]))

def get_network(cidr):
    # network address is simply long ip bitwise-and against netmask  
    return long2ip(ip2long(cidr.split('/')[0]) & _netmasks[int(cidr.split('/')[1])])

def get_broadcast(cidr):
    # broadcast is network XOR wildcard
    return '.'.join(map(str, [ int(get_network(cidr).split('.')[i]) ^ int(get_wildcard(cidr).split('.')[i]) for i in range(0,4) ]))

def get_wildcard(cidr):
    # each netmask octet XOR 255 will produce wildcard address
    return '.'.join(['%d' % (255^x) for x in map(int, get_netmask(cidr).split('.'))])

def ip2long(ip):
    return struct.unpack("!L", socket.inet_aton(ip))[0]

def long2ip(ip):
    return socket.inet_ntoa(struct.pack("!L", ip))

def within(ip, cidr):
    if ip is None:
        return False
    #print '%s <= %s <= %s' % (ip2long(get_network(cidr)), ip2long(ip), ip2long(get_broadcast(cidr)))
    if ip2long(ip) >= ip2long(get_network(cidr)) and ip2long(ip) <= ip2long(get_broadcast(cidr)):
        return True
    else:
        return False


def remap(cfg, request, **kv):
    """
       Removed dictlist and migrated it to mothership.yaml
    """
    netmap = cfg.network_map
    if request=='gw' or 'gw' in request:
        if 'vlan' not in kv.keys() and 'ip' not in kv.keys():
            print 'Either vlan or ip MUST be specified when requesting gw'
            return False
    for line in netmap:
        match = True
        for key in line:
            skip = False
            for k in kv:
                if k=='siteid' and key=='dom':
                    if kv[k] not in line[key].split('.'):
                        skip = True
                        break
                elif k=='ip' and key=='cidr':
                    if not within(kv[k], line['cidr']):
                        skip = True
                        break
                elif k==key and kv[k]!=line[key]:
                    skip = True
                    break
            if skip:
                match = False
                break
        if match:
            if type(request) is types.ListType:
                answer = []
                for r in request:
                    if r == 'siteid':
                        answer.append(line['dom'].split('.')[-3])
                    elif r == 'mask':
                        answer.append(get_netmask(line['cidr']))
                    elif r == 'ip':   # legacy ip prefix
                        answer.append(re.sub('(\.0)+$', '', line['cidr'].split('/')[0]) + '.')
                    elif r in line:
                        answer.append(line[r])
                    else:
                        answer.append(None)
                return answer
            else:
                if request == 'siteid':
                    return line['dom'].split('.')[-3]
                elif request == 'mask':
                    return get_netmask(line['cidr'])
                elif request == 'ip':   # legacy ip prefix
                    return re.sub('(\.0)+$', '', line['cidr'].split('/')[0]) + '.'
                elif request in line:
                    return line[request]
    return False

def generate_ipaddress_list(first, count=None, last=None):
    """
        Given a starting IP 'first'
            generate a list up to 'count'
            OR
            generate a list up to 'last'
    """
    iplist = []
    list_a = map(int,first.split("."))
    cur_ip = list_a[:]
    if count:
        for i in range(int(count)):
            iplist.append('.'.join(map(str,cur_ip)))
            cur_ip[3] += 1
            for x in range(3,0,-1):
                if cur_ip[x] > 255:
                    cur_ip[x] = 0
                    cur_ip[x-1] += 1
    elif last:
        list_z = map(int,last.split("."))
        for i in range(4):
            while cur_ip[i] < list_z[i]:
                iplist.append('.'.join(map(str,cur_ip)))
                cur_ip[3] += 1
                for x in range(3,0,-1):
                    if cur_ip[x] > 255:
                        cur_ip[x] = 0
                        cur_ip[x-1] += 1
        iplist.append('.'.join(map(str,cur_ip)))
    else:
        print 'You must specify --count or --last in order to generated ip addresses'
    return iplist

def ip_to_mac(ip,pre='14:6E'):
    """
        Generates a mac address from a prefix and and ipv4 address
        According to http://standards.ieee.org/regauth/oui/oui.txt, 14-6E-0A (hex) PRIVATE
    """
    if not pre.endswith(':'): pre += ':'
    return pre+':'.join([ '%02X' % int(i) for i in ip.split('.') ])

def mac_to_ip(mac):
    """
        Converts a MAC address to IP address using the final 4 octets of the MAC
        to map back to an IP address
    """
    num = mac.split(':')
    print 'pre: ' + ':'.join(num[0:2])
    print ' ip: ' + str('.'.join([ '%02d' % int(i,16) for i in num[2:6] ]))

def mac_to_oid(mac):
    """
        Converts a MAC address to an OID string
    """
    return '.'.join([ str(int(x,16)) for x in mac.split(':') ])

def next_ip(ipaddress):
    """
        Simple method that tries to the next IPv4 address given
        an IPv4 address in dotted decimal (ex. 192.168.1.2)
    """
    octet = map(int,ipaddress.split('.'))
    octet[3] += 1
    for x in range(3,0,-1):
        if octet[x] > 255:
            octet[x] = 0
            octet[x-1] += 1
    return '.'.join(map(str,octet))

