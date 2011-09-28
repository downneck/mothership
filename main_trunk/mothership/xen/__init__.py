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
mothership.xen
for interacting with the Citrix XenAPI

requires the XenServer Python module:
http://community.citrix.com/cdn/xs/sdks/
"""

import sys
import socket
import XenAPI

class XenServerAPI:
    def __init__(self, host, user, passwd):
        self.session = XenAPI.Session('https://%s:443' % host)
        try:
            self.session.xenapi.login_with_password(user, passwd)
        except XenAPI.Failure, e:
            # If slave host from pool chosed, contact master
            exec 'err=%s' % str(e)
            self.session = XenAPI.Session('https://%s:443' % err[1])
            self.session.xenapi.login_with_password(user, passwd)
        except socket.error, e:
            # Try unqdn if connection refused
            self.session = XenAPI.Session('https://%s:443' % host.split('.')[0])
            self.session.xenapi.login_with_password(user, passwd)
        except Exception, e:
            print str(e)
            raise

    def choose_storage(self):
        srs = self.session.xenapi.SR.get_all_records()
        storage = {}
        for s in srs:
            key = srs[s]['name_label']
            if 'Local' in srs[s]['name_label']:
                block = self.session.xenapi.SR.get_PBDs(s)
                if block:
                    key += ':%s' % self.session.xenapi.host.get_name_label(
                        self.session.xenapi.PBD.get_host(block[0]))
                else:
                    continue
            if 'Removable' not in srs[s]['name_label'] and \
                'torage' in key and key not in storage:
                storage[key] = {
                    'size': long(srs[s]['physical_size']),
                    'used': long(srs[s]['physical_utilisation']),
                    'free': long(srs[s]['physical_size']) \
                          - long(srs[s]['physical_utilisation']),
                    }
        if len(storage.keys()) == 1:
            return storage.keys()[0].split(':')
        if len(storage.keys()) > 1:
            print 'There are multiple storage resources available:'
            skeys = sorted(storage.keys())
            svals = map(storage.get, skeys)
            storage = zip(skeys, svals)
            for s in storage:
                print '%d) %-35s (%5d GB free)' % (storage.index(s),
                    s[0], s[1]['free']/1024/1024/1024)
            ans = raw_input('Which one do you want to use: ')
            if int(ans) < 0 or int(ans) >= len(storage):
                print 'Storage selection aborted.'
                return False
            else:
                print 'User selected "%s"' % storage[int(ans)][0]
                if len(storage[int(ans)][0].split(':')) > 1:
                    return tuple(storage[int(ans)][0].split(':'))
                else:
                    return tuple([storage[int(ans)][0], None])
        else:
            return False

    def check_memory(self, need=None, xenhost=None):
        maxfree = 0
        hosts = self.session.xenapi.host.get_all()
        for h in hosts:
            free = long(self.session.xenapi.host.compute_free_memory(h))/1024/1024
            #print '%-20s: %5d MB Memory Free' % (self.session.xenapi.host.get_hostname(h), free)
            if (free > maxfree):
                maxfree = free
            if xenhost and xenhost == self.session.xenapi.host.get_hostname(h):
                return free
        if need:
            return maxfree>=need
        else:
            return maxfree

    def check_vcpus(self, need=None):
        hcpus = 0
        vcpus = 0
        vms = self.session.xenapi.VM.get_all_records()
        for v in vms:
            if vms[v]['power_state'] == 'Running':
                if 'Control domain' in vms[v]['name_label']:
                    hcpus += int(vms[v]['VCPUs_max'])
                else:
                    vcpus += int(vms[v]['VCPUs_max'])
        #print 'Pool/Host is currently using %d out of %d CPUs' % (int(vcpus), int(hcpus))
        if need:
            return int(hcpus)-int(vcpus)>=need
        else:
            return int(hcpus)-int(vcpus)

    def check_storage(self, disk=None, need=None):
        if not disk:
            return False
        maxfree = 0
        srs = self.session.xenapi.SR.get_all()
        for s in srs:
            name = self.session.xenapi.SR.get_name_label(s)
            if name == disk:
                free = (long(self.session.xenapi.SR.get_physical_size(s)) \
                    - long(self.session.xenapi.SR.get_physical_utilisation(s))  \
                    ) / 1024 / 1024 / 1024
                #print '%-20s: %5d GB Storage Free' % (name, free)
                if (free > maxfree):
                    maxfree = free
        if need:
            return maxfree>=need
        else:
            return maxfree

    def triple_check(self, info):
        info['storage'], xenhost = self.choose_storage()
        if xenhost:
            info['power_switch'] = xenhost
        freecores = self.check_vcpus()
        if freecores < info['cores']:
            print '%s does not have enough VCPUs for %d cores (%d available)!' \
                % (info['power_switch'], info['cores'], freecores)
            return False
        freeram = self.check_memory(xenhost=xenhost)
        if freeram < (info['ram']*1024):
            print '%s does not have enough memory for %d MB (%d available)!' \
                % (info['power_switch'], info['ram']*1024, freeram)
            return False
        freedisk = self.check_storage(info['storage'])
        if freedisk < info['disk']:
            print '%s does not have enough storage for %d GB (%d available)!' \
                % (info['power_switch'], info['disk'], freedisk)
            return False
        return info['power_switch']
