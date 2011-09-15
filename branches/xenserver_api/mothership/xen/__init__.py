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
import time
import socket
import XenAPI
from pprint import pprint

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
            self.session = XenAPI.Session('https://%s.mgmt:443' % host)
            # Try unqdn if connection refused
#            self.session = XenAPI.Session('https://%s:443' % host.split('.')[0])
            self.session.xenapi.login_with_password(user, passwd)
        except Exception, e:
            print str(e)
            raise

    def choose_storage(self):
        srs = self.session.xenapi.SR.get_all_records()
        storage = {}
        for s in srs:
            if 'storage' in srs[s]['name_label'] and \
                'Removable' not in srs[s]['name_label'] \
                and srs[s]['name_label'] not in storage:
                storage[srs[s]['name_label']] = {
                    'size': long(srs[s]['physical_size']),
                    'used': long(srs[s]['physical_utilisation']),
                    'free': long(srs[s]['physical_size']) \
                          - long(srs[s]['physical_utilisation']),
                    }
        if len(storage.keys()) == 1:
            return storage.keys()[0]
        if len(storage.keys()) > 1:
            print 'There are multiple storage resources available:'
            for s in storage.keys():
                print '%d) %-35s (%5d GB free)' % (storage.keys().index(s),
                    s, storage[s]['free']/1024/1024/1024)
            ans = raw_input('Which one do you want to use: ')
            if int(ans) < 0 or int(ans) >= len(storage.keys()):
                print 'Storage selection aborted.'
                return False
            else:
                print 'User selected "%s"' % storage.keys()[int(ans)]
                return storage.keys()[int(ans)]
        else:
            return False

    def check_memory(self, need=None):
        maxfree = 0
        hosts = self.session.xenapi.host.get_all()
        for h in hosts:
            free = long(self.session.xenapi.host.compute_free_memory(h))/1024/1024
            #print '%-20s: %5d MB Memory Free' % (self.session.xenapi.host.get_hostname(h), free)
            if (free > maxfree):
                maxfree = free
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

    def check_license(self, host):
        hosts = self.session.xenapi.host.get_all()
        for h in hosts:
            #print self.session.xenapi.host.get_license_params(h)
            if host in self.session.xenapi.host.get_hostname(h):
                #pprint(self.session.xenapi.host.get_license_params(h))
                expires = self.session.xenapi.host.get_license_params(h)['expiry']
                print '%s license expires in %d days' % (host, (int(time.strftime('%s',
                    time.strptime(expires, '%Y%m%dT%H:%M:%SZ')))-int(time.time()))/86400)

    def triple_check(self, info):
        info['storage'] = self.choose_storage()
        freecores = self.check_vcpus()
        if freecores < info['cores']:
            print '%s does not have enough VCPUs for %d cores (%d available)!' \
                % (info['power_switch'], info['cores'], freecores)
            return False
        freeram = self.check_memory()
        if freeram < (info['ram']*1024):
            print '%s does not have enough memory for %d MB (%d available)!' \
                % (info['power_switch'], info['ram']*1024, freeram)
            return False
        freedisk = self.check_storage(info['storage'])
        if freedisk < info['disk']:
            print '%s does not have enough storage for %d GB (%d available)!' \
                % (info['power_switch'], info['disk'], freedisk)
            return False
        return True

    def byte_unit(self, value, multiplier):
        return int(float(value) * (1024 ** multiplier))

    def resize_vm(self, vmhost, mem=None, cpu=None, hdd=None):
        vmdict = None
        vmobj = None
        vms = self.session.xenapi.VM.get_all_records()
        for v in vms:
            if vmhost == vms[v]['name_label']:
                vmdict = vms[v]
                vmobj = v
                break
        if not vmobj:
            print '%s not found on xen host/pool' % vmhost
            sys.exit(1)
        if hdd:
            disk = self.choose_storage()
            xhdd = self.check_storage(disk)
            vdi = list(set([ self.session.xenapi.VBD.get_VDI(v) for v in vmdict['VBDs']]) & \
                set(self.session.xenapi.SR.get_VDIs(self.session.xenapi.SR.get_by_name_label(disk)[0])))[0]
            vhdd = self.byte_unit(self.session.xenapi.VDI.get_virtual_size(vdi), -3)
            if hdd < vhdd:
                print 'Not allowed to shrink the size of the virtual storage'
                sys.exit(1)
            if (xhdd + vhdd - hdd) < 0:
                print 'Not enough space on "%s" for resize: need %d, %d used, %d free' % (disk, hdd, vhdd, xhdd)
                sys.exit(1)
        if mem:
            mem = self.byte_unit(mem, 1)
            vmem = self.byte_unit(vmdict['memory_static_max'], -2)
            xmem = self.check_memory()
            if (xmem + vmem - mem) < 0:
                print 'Not enough memory for resize: need %d, %d used, %d free' % (mem, vmem, xmem)
                sys.exit(1)
        if cpu:
            vcpu = int(vmdict['VCPUs_max'])
            xcpu = self.check_vcpus()
            if (xcpu + vcpu - cpu) < 0:
                print 'Not enough cpus for resize: need %d, %d used, %d free' % (cpu, vcpu, xcpu)
                sys.exit(1)
        if vmdict['power_state'] != 'Halted':
            self.session.xenapi.VM.clean_shutdown(vmobj)
        if hdd:
            print self.byte_unit(hdd, 3)
            self.session.xenapi.VDI.resize(vdi, str(self.byte_unit(hdd, 3)))
        if mem:
            newmem = str(self.byte_unit(mem, 2))
            self.session.xenapi.VM.set_memory_limits(vmobj,
                newmem, newmem, newmem, newmem)
        if cpu:
            if vcpu < cpu:
                self.session.xenapi.VM.set_VCPUs_max(vmobj, str(cpu))
            self.session.xenapi.VM.set_VCPUs_at_startup(vmobj, str(cpu))
            if vcpu > cpu:
                self.session.xenapi.VM.set_VCPUs_max(vmobj, str(cpu))
        if vmdict['power_state'] != 'Running':
            self.session.xenapi.VM.start(vmobj, False, False)

