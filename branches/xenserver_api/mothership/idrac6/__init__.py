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
"""

import os
import sys
import re
import pexpect
import subprocess


def check_known_hosts(host, user='~'):
    # check for ssh host key
    hasKey = False
    userknownhosts = os.path.expanduser('%s/.ssh/known_hosts' % user)
    for file in [ '/etc/ssh/ssh_known_hosts', userknownhosts ]:
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


def query_idrac(cfg, host):
    check_known_hosts(host)
    child = pexpect.spawn('ssh %s@%s' % (cfg.puser, host))
    child.expect('assword:')
    child.sendline(cfg.ppass)
    child.expect('/admin1->')
    child.sendline('racadm getsysinfo')
    child.expect('/admin1->')
    data = child.before
    child.sendline('exit')
    child.expect('CLP Session terminated')
    return data

def sysinfo(info):
    """
        Parses information returned from drac getsysinfo command
        and returns it as a dictionary
    """
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

def prep_idrac(cfg, host, debug=False, basics=True, ipmi=False, serial=False, telnet=None, gold=False):
    check_known_hosts(host)
    try:
        check_known_hosts(host, '~root')
    except IOError, e:
        print '%s\nDRAC prep must be run as root/sudo' % e
        sys.exit(1)
    configured = False
    pubkeys = []
    for p in cfg.dkeys:
        f = open('%s/.ssh/id_dsa.pub' % os.path.expanduser('~%s' % p))
        pubkeys.append(f.read().rstrip())
        f.close()

    adm_pre = 'racadm config -g cfgUserAdmin -i'
    adm_obj = [
        '-o cfgUserAdminUserName %s' % cfg.puser,
        '-o cfgUserAdminPassword %s' % cfg.ppass,
        '-o cfgUserAdminPrivilege 0x000001ff',
        '-o cfgUserAdminIpmiLanPrivilege 4',
        '-o cfgUserAdminIpmiSerialPrivilege 4',
        '-o cfgUserAdminSolEnable 1',
        '-o cfgUserAdminEnable 1' ]

    # login as default root
    print '+=== Prepping DRAC for %s' % host
    child = pexpect.spawn('ssh %s@%s' % (cfg.duser,host))
    child.expect('assword:')
    child.sendline(cfg.ddell)
    ans = child.expect([ 'Permission denied', '/admin1->', pexpect.TIMEOUT ])
    if ans == 0:
        # login as power user
        print '+- Default root denied, attempting %s alternate' % cfg.puser
        child = pexpect.spawn('ssh %s@%s' % (cfg.puser,host))
        child.expect('assword:')
        child.sendline(cfg.ppass)
        newans = child.expect([ 'Permission denied', '/admin1->'])
        if newans == 0:
            print '+- Alternate %s failed, exiting' % cfg.puser
            sys.exit(2)
        userdata = 'default root disabled'
        configured = True
    elif ans == 1:
        # configure new admin user
        print '+- Adding DRAC user: %s' % cfg.puser
        for c in adm_obj:
            child.sendline('%s 3 %s' % (adm_pre,c))
            child.expect('/admin1->')
        child.sendline('racadm getconfig -u %s' % cfg.puser)
        child.expect('/admin1->')
        userdata = '\n'.join(child.before.split('\n')[1:])
        if debug: print userdata
    elif ans == 2:
        # timeout
        print '+- Default root login timed out, unknown error'
        sys.exit(2)

    if basics or ipmi:    # enable IPMI
        print '+- Enabling IPMI'
        child.sendline('racadm config -g cfgIpmiLan -o cfgIpmiLanEnable 1')
        child.expect('/admin1->')
        child.sendline('racadm getconfig -g cfgIpmiLan')
        child.expect('/admin1->')
        if debug: print '\n'.join(child.before.split('\n')[1:])
    
    if basics or serial:    # enable SerialConsole
        print '+- Enabling SerialConsole'
        child.sendline('racadm config -g cfgSerial -o cfgSerialConsoleEnable 1')
        child.expect('/admin1->')
        child.sendline('racadm getconfig -g cfgSerial')
        child.expect('/admin1->')
        if debug: print '\n'.join(child.before.split('\n')[1:])
    
    if telnet is not None:    # enable Telnet
        print '+- Enabling/Disabling Telnet'
        child.sendline('racadm config -g cfgSerial -o cfgSerialTelnetEnable %d' % telnet)
        child.expect('/admin1->')
        child.sendline('racadm getconfig -g cfgSerial')
        child.expect('/admin1->')
        if debug: print '\n'.join(child.before.split('\n')[1:])

    if basics or gold:    # gold = trusted user
        # configure new trusted user
        adm_obj[0] = '-o cfgUserAdminUserName %s' % cfg.dgold
        adm_obj[1] = '-o cfgUserAdminPassword %s' % cfg.dpass
        print '+- Adding trusted DRAC user: %s' % cfg.dgold
        for c in adm_obj:
            child.sendline('%s 4 %s' % (adm_pre,c))
            child.expect('/admin1->')
        child.sendline('racadm getconfig -u %s' % cfg.dgold)
        child.expect('/admin1->')
        if debug: print '\n'.join(child.before.split('\n')[1:])
        # add keys to trusted user
        print '+- Adding keys for trusted user'
        for k in pubkeys:
            child.sendline('racadm sshpkauth -i 4 -k %d -t "%s"' % (pubkeys.index(k)+1, k))
            child.expect('/admin1->')
        child.sendline('racadm sshpkauth -v -i 4 -k all')
        child.expect('/admin1->')
        if debug: print '\n'.join(child.before.split('\n')[1:])

    # alter password for root user
    if cfg.puser in userdata:
        print '+- Changing password for: %s' % cfg.duser
        child.sendline('%s 2 -o cfgUserAdminPassword %s' % (adm_pre,cfg.dpass))
        child.expect('/admin1->')
        if debug: print '\n'.join(child.before.split('\n')[1:])
    else:
        print '+- Skipping password change for: %s' % cfg.duser
        if not configured: print '   because %s was not successfully created' % cfg.puser

    # leaving drac
    print '+- Exiting DRAC'
    child.sendline('exit')
    child.expect('CLP Session terminated')

    if basics or ipmi:    # enable IPMI, continued
        # settings new admin user privileges with IPMI (apparently racadm was not enough)
        print '+- Updating IPMI privileges for non-root users'
        os.system('/usr/bin/ipmitool -H %s -U root -P %s user priv 3 4' % (host, cfg.dpass))
        os.system('/usr/bin/ipmitool -H %s -U root -P %s user priv 4 4' % (host, cfg.dpass))
        if debug: os.system('/usr/bin/ipmitool -H %s -U root -P %s user list' % (host, cfg.dpass))


