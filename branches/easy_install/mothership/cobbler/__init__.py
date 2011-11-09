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
cobbler functionality
"""

import os
import re
import types
import mothership.network_mapper
import subprocess
from mothership.transkey import transkey
from xmlrpclib import Fault

class CobblerAPI:
    def __init__(self, cfg):

        # mothership.transkey map for cobbler interface to mothership hardware
        self.map_hardware = {
            'power_address': 'power_switch',
#            'hw_tag'       : 'hw_tag',
            }

        # mothership.transkey map for cobbler interface to mothership servers
        self.map_server = {
            'name'          : 'hostname',
            'profile'       : 'cobbler_profile',
            'virtual'       : 'virtual',
            'virt_cpus'     : 'cores',
            'virt_ram'      : 'ram',
            'virt_file_size': 'disk',
            'virt_path'     : 'storage',
#            'site_id'      : 'site_id',
#            'realm'        : 'realm',
#            'hw_tag'       : 'hw_tag',
            }

        # mothership.transkey map for cobbler interface to mothership network
        self.map_network = {
            'mac_address'  : 'mac',
            'dhcp_tag'     : 'vlan',
            'subnet'       : 'netmask',
            'ip_address'   : 'ip',
            'bonding_opts' : 'bond_options',
            'static_route' : 'static_route',
            'interface'    : 'interface',
            'dns_name'     : 'dns',
#            'server_id'    : 'server_id',
#            'site_id'      : 'site_id',
#            'realm'        : 'realm',
#            'hw_tag'       : 'hw_tag',
            }

        # mothership.transkey map for mothership to cobbler interface
        self.map_interface = {
            'mac'           : 'macaddress',
            'ip'            : 'ipaddress',
            'vlan'          : 'dhcptag',
            'netmask'       : 'subnet',
            'dns_name'      : 'dnsname',
            'bonding'       : 'bonding',
            'bond_master'   : 'bondingmaster',
            'bond_options'  : 'bondingopts',
            'static'        : 'static',
            'static_routes' : 'staticroutes',
            }

        # mothership.transkey map for mothership to cobbler system
        self.map_system =  {
            'hostname'            :'hostname',
            'netboot_enabled'     : False,
            'power_type'          : 'power_type',
            'power_switch'        : 'power_address',
            'power_port'          : 'power_id',
            'name'                : [ 'hostname' ],
            'cobbler_profile'     : 'profile',
            'virtual'             : 'virtual',
            'cores'               : 'virt_cpus',
            'ram'                 : 'virt_ram',
            'disk'                : 'virt_file_size',
            'storage'             : 'virt_path',
            'kernel_options_post' : 'crashkernel=128M@16M',
#            'gateway'             : 'gateway',
#            '' :'comment',
#            '' :'ctime',
#            '' :'depth',
#            '' :'kernel_options',
#            '' :'kernel_options_post',
#            '' :'ks_meta',
#            '' :'mgmt_classes',
#            '' :'mtime',
#            '' :'name_servers',
#            '' :'name_servers_search',
#            '' :'owners',
#            '' :'template_remote_kickstarts',
#            '' :'uid',
            }

        # retrieve os dict
        self.osdict = self.get_os_dict(cfg)

    def add_system(self, cfg, host_dict):
        hostname = host_dict['hostname']
        if not host_dict['cobbler_profile']:
            print '%s has empty profile: system not provisioned for cobbler!' % hostname
            return
        if cfg.coblive:
            if self.find_system_by_hostname(cfg, hostname):
                print 'System already exists: %s' % hostname
                self.delete_system(cfg, hostname)
            print 'Adding system: %s' % hostname
            handle = cfg.remote.new_system(cfg.token)
        else:
            print 'API: remote.find_system({\'name\':hostname})'
            print 'API: if found: remote.remove_system(hostname, token)'
            print 'API: set new handle = remote.new_system(token)'

        sysdict = mothership.transkey(host_dict, self.map_system)
        # Adjust power management values after mothership.transkey
        if sysdict['virtual']:
            sysdict['power_user'] = 'root'
            sysdict['power_pass'] = ''
        else:
            sysdict['power_user'] = cfg.puser
            sysdict['power_pass'] = cfg.ppass

        if cfg.coblive:
            for k in sysdict.keys():
                if '-xen-' not in sysdict['profile'] and 'virt_' in k:
                    continue    # do not set cpu,ram,disk for baremetal
                if sysdict[k] is not None:
                    if k == 'virt_ram':
                        # convert mothership GB to cobbler MB
                        sysdict[k] = int(sysdict[k]) * 1024
                    #print 'Modifying %s system values: %s' % (hostname, k)
                    cfg.remote.modify_system(handle, k, sysdict[k], cfg.token)
        else:
            from pprint import pprint
            print 'API: sysdict = { \'key\':\'value\', }'
            pprint(sysdict, indent=4)
            print 'API: loop through all the cobbler \'system\' values:'
            print 'API:     remote.modify_system(handle, key, sysdict[key], token)'
            print 'API: then loop through all interfaces...'

        ifbond = False
        for k in sorted(host_dict['interfaces'].keys()):
            x = host_dict['interfaces'][k]

            # remove ip if world
            if 'ip' in x and x['ip'] == '0.0.0.0':
                del x['ip']

            # if valid ip, set static to True
            if 'ip' in x:
                x['static'] = 'True'

            # set static_routes
            if x['static_route']:
                x['static_routes'] = [ '0.0.0.0/0:%s' % x['static_route'] ]

            # add appropriate dns_names for each interface
            domain = None
            if x['ip']:
                domain = mothership.network_mapper.remap(cfg, 'dom', nic=x['interface'], siteid=x['site_id'], ip=x['ip'])
            if domain:
                x['dns_name'] = '%s%s' % (hostname, domain)

            # set the bond0 master interface
            if not ifbond and x['bond_options']:
                ifbond = 'bond0'
                ifdict = x.copy()
                ifdict['bonding'] = 'master'
                del ifdict['mac']
                # modify system interface bond0
                if cfg.coblive:
                    #print 'Modifying %s network values: %s' % (hostname, ifbond)
                    cfg.remote.modify_system(handle, 'modify_interface', 
                        self.append_value_to_keyname(cfg, mothership.transkey(ifdict,
                        self.map_interface, True), '-'+ifbond), cfg.token)
                else:
                    print 'API: since bond_options are set:'
                    print 'API:     remote.modify_system(handle, \'modify_interface\', ifbond-dict-map, token)'
                # if xenserver, then add template for bond0
                if 'xenserver' in sysdict['profile']:
                    if cfg.coblive:
                        #print 'Modifying %s templates values' % hostname
                        cfg.remote.modify_system(handle, 'template_files', {
                            '/var/www/cobbler/aux/xenserver/create_bond0.template': '/bond0',
                            '/var/www/cobbler/aux/xenserver/create_eth1.template': '/eth1',
                            '/var/www/cobbler/aux/xenserver/gateway_eth1.template': '/defgw',
                            }, cfg.token)
                    else:
                        print 'API: if \'xenserver\' profile:'
                        print 'API:     remote.modify_system(handle, \'template_files\', {template-path:alias}, token)'

            # set the bond0 slave interfaces
            if x['bond_options']:
                x['bonding'] = 'slave'
                x['bond_master'] = ifbond
                x['ip'] = ifdict['ip']
                del x['bond_options']

            # modify system interface 'k'
            if cfg.coblive and host_dict['interfaces'][k]['mac']:
                try:
                    cfg.remote.modify_system(handle, 'modify_interface', 
                        self.append_value_to_keyname(cfg, mothership.transkey(host_dict['interfaces'][k],
                        self.map_interface, True), '-'+k), cfg.token)
                except Fault, err:
                    print 'Aborting cobbler add, failed to modify %s %s' % (hostname, k)
                    print '    ' + str(err)
                    return False
            else:
                print 'API: remote.modify_system(handle, \'modify_interface\', %s-dict-map, token)' % k

        # save all system changes
        if cfg.coblive:
            cfg.remote.save_system(handle, cfg.token)
        else:
            print 'API: remote.save_system(handle, token)'
        return True

    def append_value_to_keyname(self, cfg, olddict, suffix):
        # loop through all keys and append the suffix to the keyname
        newdict = {}
        for k in olddict.keys():
            if olddict[k]:
                newdict['%s%s' % (k,suffix)] = olddict[k]
        return newdict

    def delete_system(self, cfg, hostname):
        if cfg.coblive:
            if not self.find_system_by_hostname(cfg, hostname):
                print 'Skipping cobbler delete, system does not exist: %s' % hostname
                return
            print 'Deleting cobbler system: %s' % hostname
            cfg.remote.remove_system(hostname, cfg.token)
        else:
            print 'API: remote.remove_system(hostname, token)'

    def extract_system_by_hostname(self, cfg, hostname):
        info = {}
        print 'Extracting cobbler system: %s' % hostname
        system = cfg.remote.get_system(hostname)
        if '-xen-' in system['profile']:
            system['virtual'] = True
        else:
            system['virtual'] = False
        info['server'] = [ mothership.transkey(system, self.map_server) ] 
        info['hardware'] = [ mothership.transkey(system, self.map_hardware) ]
        info['network'] = []
        sysif = system['interfaces']
        for k in sysif.keys():
            if k.startswith('bond'): continue
            sysif[k]['interface'] = k
            if sysif[k]['static_routes']:
                sysif[k]['static_route'] = sysif[k]['static_routes'][0].split(':')[1]
            info['network'].append(mothership.transkey(system['interfaces'][k], self.map_network, True))
        return info

    def append_kickstart_info(self, cfg, info):
        profile = cfg.remote.get_profile(info['server'][0]['cobbler_profile'])
        while profile['parent'] != '':
            profile = cfg.remote.get_profile(profile['parent'])
        distro = cfg.remote.get_distro(profile['distro'])['name']
        cobblerip = cfg.remote.get_settings()['server']
        info['kick'] = {}
        info['kick']['repo'] = 'http://%s/cblr/links/%s/' % (cobblerip, distro)
        info['kick']['ks'] = 'http://%s/cblr/svc/op/ks/system' % cobblerip
        return info

    def find_system_by_hostname(self, cfg, hostname):
        return cfg.remote.find_system({'name':hostname})

    def get_os_dict(self, cfg):
        osdict = { 'profile':{}, 'default':{} }
        for profile in self.list_all_profiles(cfg):
            if profile['comment'] != '':
                osdict['profile'][profile['name']] = profile['comment']
                if profile['dhcp_tag'] != 'default':
                    osdict['default'][profile['dhcp_tag']] = profile['name']
        return osdict

    def list_all_profiles(self, cfg):
        return cfg.remote.get_profiles()

    def list_all_systems(self, cfg):
        return cfg.remote.get_systems()

    def set_system_netboot(self, cfg, hostname, state=False):
        if cfg.coblive:
            if not self.find_system_by_hostname(cfg, hostname):
                print 'Skipping netboot setting, system does not exist: %s' % hostname
                return
            print 'Setting netboot "%s" for %s' % (state, hostname)
            handle = cfg.remote.get_system_handle(hostname, cfg.token)
            cfg.remote.modify_system(handle, 'netboot_enabled', state, cfg.token)
        else:
            print 'API: set handle = remote.get_system_handle(hostname, token)'
            print 'API: remote.modify_system(handle, \'netboot_enabled\', state, token)'

    def set_system_power(self, cfg, hostname, state='reboot'):
        if cfg.coblive:
            if not self.find_system_by_hostname(cfg, hostname):
                print 'Skipping power setting, system does not exist: %s' % hostname
                return
            print 'Setting power "%s" for %s' % (state, hostname)
            handle = cfg.remote.get_system_handle(hostname, cfg.token)
            #self.check_known_hosts(cfg, hostname, '~root')
            try:
                cfg.remote.power_system(handle, state, cfg.token)
            except Fault, err:
                print 'ERROR occurred during cobbler power: %s' \
                    % str(err).replace('\n', ' ')
                return
        else:
            print 'API: set handle = remote.get_system_handle(hostname, token)'
            print 'API: remote.power_system(handle, state, token)'

    def sync_cobbler(self, cfg):
        if cfg.coblive:
            print 'Syncing cobbler configurations'
            try:
                cfg.remote.sync(cfg.token)
            except Fault, err:
                print 'ERROR occurred during cobbler sync: %s' % str(err)
                return
        else:
            print 'API: remote.sync(token)'

    def abort_kick(self, cfg, name, host):
        # abort kick if host.realm.site_id not defined for current system
        try:
            if str(self.extract_system_by_hostname(cfg,
                host.split('.')[0])).find(host) < 0:
                print '!! IP Address for %s not defined' % host
                print 'Please run: %s mod_vlan %s <vlan#>' % (name, host)
                print 'or equivalent command before kickstarting'
                return True
        except:
            return False
        # confirm kick if host.realm.site_id responds to pings
        pingcheck = os.popen("ping -q -c2 -t2 "+host,"r")
        while 1:
            line = pingcheck.readline()
            if not line: break
            match = re.findall(re.compile(r"(\d)( packets)? received"),line)
            if match:
                if int(match[0][0]) == 2:
                    print '%s is an existing host, responsive to pings' % host
                    ans = raw_input('If you still want to continue, type "cobbler_forcekick_%s": ' % host)
                    if ans != 'cobbler_forcekick_%s' % host:
                        print 'cobbler force kick of %s aborted.' % host
                        return True
        return False

    def clear_puppetca(self, host):
        try:
            # clear out the puppet sign CA for host
            os.system('sudo /usr/sbin/puppetca --clean %s' % host)
            print 'Removed puppet ssl for %s' % host
            return True
        except OSError:
            print 'Failed to clear puppet ssl for %s (are you root?)' % host
            return False

    def check_known_hosts(self, cfg, host, user='~'):
        print 'Checking known_hosts for %s' % host
        system = cfg.remote.get_system(host)
        host = system['power_address']
        # check for ssh host key
        hasKey = False
        userknownhosts = os.path.expanduser('%s/.ssh/known_hosts' % user)
        for file in [ '/etc/ssh/ssh_known_hosts', userknownhosts ]:
            if os.path.exists(file):
                for line in open(file):
                    if host in line:
                        hasKey = True
                        break
        if not hasKey:
            print '+=== Adding %s to known_hosts' % host
            key = subprocess.Popen(['ssh-keyscan', host],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE).\
                communicate()[0]
            f = open(userknownhosts, 'a')
            f.write(key)
    
