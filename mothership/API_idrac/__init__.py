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
The idrac6 module contains all the functionality that mothership will need
to interact with the Dell DRACs using pexpect and some IPMI commands

most of this code is Kent Lee's original drac code, just spruced up to work
with the new REST daemon and API framework
"""

import os
import sys
import re
import pexpect
import subprocess

from mothership.mothership_models import *
from mothership.common import *
from mothership.validate import *
from mothership.network_mapper import remap

class IdracError(Exception):
    pass

class API_idrac:

    def __init__(self, cfg):
        self.cfg = cfg
        self.common = MothershipCommon(cfg)
        self.version = 1
        self.namespace = 'API_idrac'
        self.metadata = {
            'config': {
                'shortname': 'drac',
                'description': 'allows interaction with Integrated Dell Remote Access Console',
                'module_dependencies': {},
            },
            'methods': {
                'prep': {
                    'description': 'prep the iDrac for import',
                    'short': 'p',
                    'rest_type': 'POST',
                    'admin_only': True,
                    'required_args': {
                        'args': {
                            'ip': {
                                'vartype': 'str',
                                'desc': 'ip address of the iDrac',
                                'ol': 'i',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'ingest': {
                    'description': 'import iDrac info into mothership\'s hardware database',
                    'short': 'i',
                    'rest_type': 'POST',
                    'admin_only': True,
                    'required_args': {
                        'args': {
                            'ip': {
                                'vartype': 'str',
                                'desc': 'ip address of the iDrac',
                                'ol': 'i',
                            },
                            'unqn': {
                                'vartype': 'str',
                                'desc': 'unqualified name (realm.site_id) to import into',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'string': 'success',
                    },
                },
            },
        }


    def ingest(self, query):
        """
        [description]
        display stored/configured forward DNS data 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        returns a list of zones' information if successful, raises an error if not
        """
        # setting our valid query keys
        common = MothershipCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'import')
        try:
            # check for min/max number of optional arguments
            self.common.check_num_opt_args(query, self.namespace, 'import')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_idrac/import: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise IdracError("API_idrac/import: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # doin stuff
            if ip in query.keys() and query['ip'] and unqn in query.keys() and query['unqn']:
                drac_info = self.__parse_sysinfo(self.__get_sysinfo(self.cfg, query['ip']))
                special_vlan, realm, site_id = v_split_unqn(query['unqn'])
                drac_info.update({'power_switch': query['ip'], 'site_id': site_id, 'realm': realm})
                for k in drac_info.keys():
                    info = drac_info.copy()
                    if not k.startswith('eth') and k != 'drac': continue
                    net = remap(cfg, ['vlan','mask','ip'], nic=k, siteid=site_id)
                    dracip = remap(cfg, 'ip', nic='drac', siteid=site_id)
                    if net:
                        if k!= self.cfg.primary_interface: # due to multiple vlans
                            if ip.startswith(dracip):
                                info.update({'ip':ip.replace(dracip,net[2])})
                            netdrac_sysinfo.update({'vlan':net[0], 'netmask':net[1]})
                        info.update({'interface':k, 'mac':info[k]})
                    self.cfg.dbsess.add(Network(info['ip'], info['interface'], info['netmask'], info['mac']))
                    self.cfg.dbsess.commit()
            else:
                self.cfg.log.debug("API_idrac/import: missing either ip or unqn.")
                raise IdracError("API_idrac/import: missing either ip or unqn.")
        except Exception, e:
            self.cfg.log.debug("API_idrac/import: error: %s" % e)
            raise IdracError("API_idrac/import: error: %s" % e)


    def prep(self, query):
        # set some defaults
        basics = True
        ipmi = False
        serial = False
        telnet = None
        gold = False
        # setting our valid query keys
        common = MothershipCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'prep')
        try:
            # check for min/max number of optional arguments
            self.common.check_num_opt_args(query, self.namespace, 'prep')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_idrac/prep: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise IdracError("API_idrac/prep: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # doin stuff
            if ip in query.keys() and query['ip']:
                self.__check_known_hosts(query['ip'])
                try:
                    self.__check_known_hosts(host, '~root')
                except IOError, e:
                    self.cfg.log.debug("API_idrac/prep: ship_daemon must be run as root!")
                    raise IdracError("API_idrac/prep: ship_daemon must be run as root!")
            else:
                self.cfg.log.debug("API_idrac/prep: idrac ip must be specified!")
                raise IdracError("API_idrac/prep: idrac ip must be specified!")
            configured = False
            pubkeys = []
            for p in self.cfg.dkeys:
                if os.path.exists("%s/.ssh/id_rsa.pub" % os.path.expanduser('~%s' % p)):
                    f = open('%s/.ssh/id_rsa.pub' % os.path.expanduser('~%s' % p))
                elif os.path.exists("%s/.ssh/id_dsa.pub" % os.path.expanduser('~%s' % p)):
                    f = open('%s/.ssh/id_dsa.pub' % os.path.expanduser('~%s' % p))
                else:
                    self.cfg.log.debug("API_idrac/prep: no ssh keys found for user: %s" % p)
                    raise IdracError("API_idrac/prep: no ssh keys found for user: %s" % p)
                pubkeys.append(f.read().rstrip())
                f.close()
        
            adm_pre = 'racadm config -g cfgUserAdmin -i'
            adm_obj = [
                '-o cfgUserAdminUserName %s' % self.cfg.puser,
                '-o cfgUserAdminPassword %s' % self.cfg.ppass,
                '-o cfgUserAdminPrivilege 0x000001ff',
                '-o cfgUserAdminIpmiLanPrivilege 4',
                '-o cfgUserAdminIpmiSerialPrivilege 4',
                '-o cfgUserAdminSolEnable 1',
                '-o cfgUserAdminEnable 1' ]
        
            # login as default root
            child = pexpect.spawn('ssh %s@%s' % (self.cfg.duser, query['ip']))
            child.expect('assword:')
            child.sendline(self.cfg.ddell)
            ans = child.expect([ 'Permission denied', '/admin1->', pexpect.TIMEOUT ])
            if ans == 0:
                # login as power user
                child = pexpect.spawn('ssh %s@%s' % (self.cfg.puser, query['ip']))
                child.expect('assword:')
                child.sendline(cfg.ppass)
                newans = child.expect([ 'Permission denied', '/admin1->'])
                if newans == 0:
                    self.cfg.log.debug("API_idrac/prep: unable to log into drac as root or alternate user: %s" % self.cfg.puser)
                    raise IdracError("API_idrac/prep: unable to log into drac as root or alternate user: %s" % self.cfg.puser)
                userdata = 'default root disabled'
                configured = True
            elif ans == 1:
                # configure new admin user
                for c in adm_obj:
                    child.sendline('%s 3 %s' % (adm_pre,c))
                    child.expect('/admin1->')
                child.sendline('racadm getconfig -u %s' % self.cfg.puser)
                child.expect('/admin1->')
                userdata = '\n'.join(child.before.split('\n')[1:])
            elif ans == 2:
                # timeout
                self.cfg.log.debug("API_idrac/prep: idrac default root login timed out")
                raise IdracError("API_idrac/prep: idrac default root login timed out")
        
            if basics or ipmi:    # enable IPMI
                child.sendline('racadm config -g cfgIpmiLan -o cfgIpmiLanEnable 1')
                child.expect('/admin1->')
                child.sendline('racadm getconfig -g cfgIpmiLan')
                child.expect('/admin1->')
            
            if basics or serial:    # enable SerialConsole
                child.sendline('racadm config -g cfgSerial -o cfgSerialConsoleEnable 1')
                child.expect('/admin1->')
                child.sendline('racadm getconfig -g cfgSerial')
                child.expect('/admin1->')
            
            if telnet is not None:    # enable Telnet
                child.sendline('racadm config -g cfgSerial -o cfgSerialTelnetEnable %d' % telnet)
                child.expect('/admin1->')
                child.sendline('racadm getconfig -g cfgSerial')
                child.expect('/admin1->')
        
            if basics or gold:    # gold = trusted user
                adm_obj[0] = '-o cfgUserAdminUserName %s' % self.cfg.dgold
                adm_obj[1] = '-o cfgUserAdminPassword %s' % self.cfg.dpass
                for c in adm_obj:
                    child.sendline('%s 4 %s' % (adm_pre,c))
                    child.expect('/admin1->')
                child.sendline('racadm getconfig -u %s' % self.cfg.dgold)
                child.expect('/admin1->')
                # add keys to trusted user
                for k in pubkeys:
                    child.sendline('racadm sshpkauth -i 4 -k %d -t "%s"' % (pubkeys.index(k)+1, k))
                    child.expect('/admin1->')
                child.sendline('racadm sshpkauth -v -i 4 -k all')
                child.expect('/admin1->')
        
            # alter password for root user
            if self.cfg.puser in userdata:
                child.sendline('%s 2 -o cfgUserAdminPassword %s' % (adm_pre,self.cfg.dpass))
                child.expect('/admin1->')
        
            # leaving drac
            child.sendline('exit')
            child.expect('CLP Session terminated')
        
            if basics or ipmi:    # enable IPMI, continued
                # setting new admin user privileges with IPMI (apparently racadm was not enough)
                os.system('/usr/bin/ipmitool -H %s -U root -P %s user priv 3 4' % (host, self.cfg.dpass))
                os.system('/usr/bin/ipmitool -H %s -U root -P %s user priv 4 4' % (host, self.cfg.dpass))
        except Exception, e:
            self.cfg.log.debug("API_idrac/prep: error: %s" % e)
            raise IdracError("API_idrac/prep: error: %s" % e)


    #
    # internal methods below
    # 


    # check for ssh host key
    def __check_known_hosts(self, host, user='~'):
        """
            check known hosts to make sure the drac has a known hosts key 
        """
        try:
            hasKey = False
            userknownhosts = os.path.expanduser('%s/.ssh/known_hosts' % user)
            for file in [ '/etc/ssh/ssh_known_hosts', userknownhosts ]:
                for line in open(file):
                    if host in line:
                        hasKey = True
                        break
            if not hasKey:
                key = subprocess.Popen(['ssh-keyscan', host],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).\
                    communicate()[0]
                f = open(userknownhosts, 'a')
                f.write(key)
        except Exception, e:
            self.cfg.log.debug("API_idrac/__check_known_hosts: error: %s" % e)
            raise IdracError("API_idrac/__check_known_hosts: error: %s" % e)
    

    # get all sys info from the idrac
    def __get_sysinfo(self, host):
        """
            get all sys info from the idrac 
        """
        try:
            self.__check_known_hosts(host)
            child = pexpect.spawn('ssh %s@%s' % (self.cfg.puser, host))
            child.expect('assword:')
            child.sendline(self.cfg.ppass)
            child.expect('/admin1->')
            child.sendline('racadm getsysinfo')
            child.expect('/admin1->')
            data = child.before
            child.sendline('exit')
            child.expect('CLP Session terminated')
            return data
        except Exception, e:
            self.cfg.log.debug("API_idrac/__get_sysinfo: error: %s" % e)
            raise IdracError("API_idrac/__get_sysinfo: error: %s" % e)


    # Parses information returned from drac getsysinfo command and returns it as a dictionary    
    def __parse_sysinfo(self, info):
        """
            Parses information returned from drac getsysinfo command
            and returns it as a dictionary
        """
        try:
            out={}
            parsers = [
            r'(Firmware Version\s+=\s(?P<firmware>[.\d]+))',
            r'(System BIOS Version\s+=\s(?P<bios>[.\d]+))',
                r'(System Model\s+=\s(?P<model>[ \w]+))',
                r'(Service Tag\s+=\s(?P<hw_tag>\w+))',
                r'(MAC Address\s+=\s(?P<drac>[a-f:0-9]+))',
                r'(?P<hwname>NIC\d+)\sEthernet\s+=\s(?P<hwaddr>[a-f:0-9]+)',
                ]
        
            for line in info.split('\n'):
                for pattern in parsers:
                    match = re.search(pattern, line)
                    if match:
                        if 'hwname' in match.groupdict().keys():
                            num = match.group('hwname').replace('NIC','')
                            out['eth%d' % (int(num)-1)] = match.group('hwaddr')
                        else:
                            for key in match.groupdict().keys():
                                out[key] = match.group(key)
                                if key == 'model' and re.match('PowerEdge', match.group(key)):
                                    out['manufacturer'] = 'Dell'
            return out
        except Exception, e:
            self.cfg.log.debug("API_idrac/__parse_sysinfo: error: %s" % e)
            raise IdracError("API_idrac/__parse_sysinfo: error: %s" % e)
 
####################### unconverted below here



