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
    The Configure class is responsible for loading the yaml file that
    describes connecting to the database and any other configuration specific
    bits that should be abstracted away
"""
import os.path
import sys
import shutil
import yaml

# Extra modules
import xmlrpclib
import sqlalchemy

# our error class
class ConfigureError(Exception):
    pass

# This is the set of paths Configure will look for
# a config_file (mothership.yaml)
load_paths = ['.', '~', '/etc', '/usr/local/etc']

class Configure:
    def __init__(self, config_file):
        """
            Takes a config_file name as a parameter and searches through the following
            dirs to load the configuration file:  /etc, CWD
        """
        # Read settings from configuration yaml
        try:
            yaml_config = open(self.load_path(config_file)).read()
            all_configs = yaml.load(yaml_config)
        except:
            # we discovered this was more annoying than helpful, so we stopped
            #sys.stderr.write('No config file found, copying defaults into your home directory')
            #@srccfgyaml = sys.path[0] + '/mothership.yaml.sample'
            #dstcfgyaml = os.path.expanduser('~') + '/mothership.yaml'
            #shutil.copyfile(srccfgyaml, dstcfgyaml)
            #yaml_config = open(self.load_path(config_file)).read()
            #all_configs = yaml.load(yaml_config)
            raise ConfigureError("Config file mothership.yaml not found in path: %s" % load_paths)

        # Database related settings
        dbconfig = all_configs['db']
        try:
            engine = ''
            # PostgreSQL
            if dbconfig['engine'] == 'postgresql':
                dbtuple = (dbconfig['user'], dbconfig['hostname'], dbconfig['dbname'])
                engine = sqlalchemy.create_engine("postgres://%s@%s/%s" % dbtuple, echo=dbconfig['echo'])
            # MySql
            elif dbconfig['engine'] == 'mysql':
                dbtuple = (dbconfig['user'], dbconfig['pass'], dbconfig['hostname'], dbconfig['dbname'])
                engine = sqlalchemy.create_engine("mysql://%s:%s@%s/%s" % dbtuple, echo=dbconfig['echo'])
            # uhhhh....
            else:
                raise ConfigureError("DB section of /etc/mothership.yaml is misconfigured! Exiting")
            Session = sqlalchemy.orm.sessionmaker(bind=engine)
            dbsession = Session()
            self.dbconfig = dbconfig
            self.dbconn = engine.connect()
            self.dbengine = engine
            self.dbsess = dbsession
            self.dbnull = sqlalchemy.sql.expression.null()
        except:
            print "dbtuple: %s\nengine: %s" % (dbtuple, engine)
            raise ConfigureError('Database configuration error')

        # Cobbler related settings
        self.cobconfig = all_configs['cobbler']
        # Only ping cobbler server if configured to
        self.coblive = False
        if self.cobconfig.has_key('active'):
            self.coblive = self.cobconfig['active']

        # Power related settings
        pwrconfig = all_configs['power']
        if 'user' in pwrconfig and pwrconfig['user']:
            self.puser = pwrconfig['user']
        else:
            self.puser = 'api'
        if 'pass' in pwrconfig and pwrconfig['pass']:
            self.ppass = pwrconfig['pass']
        else:
            self.ppass = 'api'

        # DRAC related settings
        draconfig = all_configs['drac']
        if 'dell' in draconfig and draconfig['dell']:
            self.ddell = draconfig['dell']  # default dell pass
        else:
            self.ddell = 'calvin'
        if 'user' in draconfig and draconfig['user']:
            self.duser = draconfig['user']  # drac root user
        else:
            self.duser = 'root'
        if 'pass' in draconfig and draconfig['pass']:
            self.dpass = draconfig['pass']  # drac root pass
        else:
            self.dpass = 'CHANGE_ME_PLEASE'
        if 'keys' in draconfig and draconfig['keys']:
            self.dkeys = draconfig['keys']  # list of users for pubkeys
        else:
            self.dkeys = [ 'root', 'postgres' ]
        if 'trust' in draconfig and draconfig['trust']:
            self.dgold = draconfig['trust']  # trusted user
        else:
            self.dgold = 'gold'

        # SNMP related settings
        snmpconfig = all_configs['snmp']
        if 'hosts' in snmpconfig and snmpconfig['hosts']:
            self.snmphosts = snmpconfig['hosts']
        else:
            self.snmphosts = [ '10.0.0.1', '10.0.0.3' ]
        if 'community' in snmpconfig and snmpconfig['community']:
            self.snmpread = snmpconfig['community']
        else:
            self.snmpread ='public'
        if 'version' in snmpconfig and snmpconfig['version']:
            self.snmpver = snmpconfig['version']
        else:
            self.snmpver = '2c'
        if 'exclude' in snmpconfig and snmpconfig['exclude']:
            self.snmpskip = snmpconfig['exclude']
        else:
            self.snmpskip = ['No Such']

        # KV settings
        kvconfig = all_configs['kv']
        if 'search_path' in kvconfig and kvconfig['search_path']:
            self.search_path = kvconfig['search_path']
        else:
            self.search_path = [ ['prod', 'iad'], ['iad'], [] ]

        # Zenoss settings
        zenconfig = all_configs['zenoss']
        if 'active' in zenconfig and zenconfig['active']:
            self.zenlive = zenconfig['active']
        else:
            self.zenlive = False

        # General settings
        genconfig = all_configs['general']
        if 'domain' in genconfig and genconfig['domain']:
            self.domain = genconfig['domain']
        else:
            self.domain = 'localhost.localdomain'
        if 'contact' in genconfig and genconfig['contact']:
            self.contact = genconfig['contact']
        else:
            self.contact = 'hostmaster@localhost.localdomain'
        if 'realms' in genconfig and genconfig['realms']:
            self.realms = genconfig['realms']
        else:
            self.realms = ['prod', 'qa']
        if 'site_ids' in genconfig and genconfig['site_ids']:
            self.site_ids = genconfig['site_ids']
        else:
            self.site_ids = ['iad', 'sfo']
        if 'publicip' in genconfig and genconfig['publicip']:
            self.def_public_ip = genconfig['publicip']
        else:
            self.def_public_ip = '123.123.123.123'
        if 'sudo_nopass' in genconfig and genconfig['sudo_nopass']:
            self.sudo_nopass = genconfig['sudo_nopass']
        else:
            self.sudo_nopass = True
        if 'audit_log_file' in genconfig and genconfig['audit_log_file']:
            self.audit_log_file = genconfig['audit_log_file']
        else:
            self.audit_log_file = '/var/log/mothership_audit.log'
        if 'puppet_audit_log_file' in genconfig and genconfig['puppet_audit_log_file']:
            self.puppet_audit_log_file = genconfig['puppet_audit_log_file']
        else:
            self.audit_log_file = '/var/log/mothership_puppet_audit.log'
        if 'max_time' in genconfig and genconfig['max_time']:
            self.max_time = genconfig['max_time']
        else:
            self.max_time = None
        if 'min_time' in genconfig and genconfig['min_time']:
            self.min_time = genconfig['min_time']
        else:
            self.min_time = None

        # Virtual Machine settings
        vmconfig = all_configs['vm']
        if 'min_cpu' in vmconfig and vmconfig['min_cpu'] and \
        'min_ram' in vmconfig and vmconfig['min_ram'] and \
        'min_disk' in vmconfig and vmconfig['min_disk']:
            self.vm_spec = {
                'cores': vmconfig['min_cpu'],
                'ram': vmconfig['min_ram'],
                'disk': vmconfig['min_disk']
            }
        else:
            self.vm_spec = {
                'cores': 1,
                'ram': 1,
                'disk': 25
            }

        # Zabbix settings
        zabconfig = all_configs['zabbix']
        if 'active' in zabconfig and zabconfig['active']:
            self.zab_active = zabconfig['active']
        else:
            self.zab_active = False

        # Network settings
        netconf = all_configs['network']
        self.network_map = netconf['map']
        # Management Vlan settings
        if 'mgmt_facility' in netconf and netconf['mgmt_facility']:
            self.mgmt_vlan_style = netconf['mgmt_facility']
        else:
            self.mgmt_vlan_style = 'snmp'
        if 'mgmt_interface' in netconf and netconf['mgmt_interface']:
            self.mgmt_vlan_interface = netconf['mgmt_interface']
        else:
            self.mgmt_vlan_interface = 'eth0'

        if self.mgmt_vlan_style == 'curl':
            self.mgmt_vlan_enable_url = netconf['mgmt_enable_url']
            self.mgmt_vlan_disable_url = netconf['mgmt_disable_url']
            self.mgmt_vlan_status_url = netconf['mgmt_status_url']
        elif self.mgmt_vlan_style == 'snmp':
            if 'mgmt_community' in netconf and netconf['mgmt_community']:
                self.mgmt_vlan_community = netconf['mgmt_community']
            else:
                self.mgmt_vlan_community = 'public'
        else:
            sys.stderr.write("mgmt_vlan->facility has been set incorrectly in the config.\nplease edit /etc/mothership.yaml and set it to either 'snmp' or 'curl'")

        # Users and Groups settings
        ugconfig = all_configs['users_and_groups']
        # User settings
        if 'hdir' in ugconfig and ugconfig['hdir']:
            self.hdir = ugconfig['hdir']
        else:
            self.hdir = '/home'
        if 'shell' in ugconfig and ugconfig['shell']:
            self.shell = ugconfig['shell']
        else:
            self.shell = '/bin/bash'
        if 'email_domain' in ugconfig and ugconfig['email_domain']:
            self.email_domain = ugconfig['email_domain']
        else:
            self.email_domain = 'company.com'
        if 'uid_start' in ugconfig and ugconfig['uid_start']:
            self.uid_start = int(ugconfig['uid_start'])
        else:
            self.uid_start = 500
        if 'uid_end' in ugconfig and ugconfig['uid_end']:
            self.uid_end = int(ugconfig['uid_end'])
        else:
            self.uid_end = 65535
        if 'user_types' in ugconfig and ugconfig['user_types']:
            self.user_types = ugconfig['user_types']
        else:
            self.user_types = ['employee', 'consultant', 'system']
        if 'def_user_type' in ugconfig and ugconfig['def_user_type']:
            self.def_user_type = ugconfig['def_user_type']
        else:
            self.def_user_type = 'employee'
        # Group settings
        if 'gid_start' in ugconfig and ugconfig['gid_start']:
            self.gid_start = int(ugconfig['gid_start'])
        else:
            self.gid_start = 500
        if 'gid_end' in ugconfig and ugconfig['gid_end']:
            self.gid_end = int(ugconfig['gid_end'])
        else:
            self.gid_end = 65535
        if 'default_groups' in ugconfig and ugconfig['default_groups']:
            self.default_groups = ugconfig['default_groups']
        else:
            self.default_groups = ['users', 'web']


        # LDAP settings
        ldconfig = all_configs['ldap']
        if 'active' in ldconfig and ldconfig['active']:
            self.ldap_active = ldconfig['active']
        else:
            self.ldap_active = False
        if 'users_ou' in ldconfig and ldconfig['users_ou']:
            self.ldap_users_ou = ldconfig['users_ou']
        else:
            self.ldap_users_ou = 'users'
        if 'groups_ou' in ldconfig and ldconfig['groups_ou']:
            self.ldap_groups_ou = ldconfig['groups_ou']
        else:
            self.ldap_groups_ou = 'groups'
        if 'default_gid' in ldconfig and ldconfig['default_gid']:
            self.ldap_default_gid = ldconfig['default_gid']
        else:
            self.ldap_default_gid = '401'


        # DNS settings
        dnsconfig = all_configs['dns']
        if 'active' in dnsconfig and dnsconfig['active']:
            self.dns_active = dnsconfig['active']
        else:
            self.dns_active = False
        if 'zonecfg' in dnsconfig and dnsconfig['zonecfg']:
            self.dns_conf = dnsconfig['zonecfg']
        else:
            self.dns_conf = '/etc/named/zones.conf'
        if 'zonedir' in dnsconfig and dnsconfig['zonedir']:
            self.dns_zone = dnsconfig['zonedir']
        else:
            self.dns_zone = '/var/named/'
        if 'zonettl' in dnsconfig and dnsconfig['zonettl']:
            self.dns_ttl = dnsconfig['zonettl']
        else:
            self.dns_ttl = '86400'
        if 'refresh' in dnsconfig and dnsconfig['refresh']:
            self.dns_refresh = dnsconfig['refresh']
        else:
            self.dns_refresh = '21600'
        if 'retry' in dnsconfig and dnsconfig['retry']:
            self.dns_retry = dnsconfig['retry']
        else:
            self.dns_retry = '3600'
        if 'expire' in dnsconfig and dnsconfig['expire']:
            self.dns_expire = dnsconfig['expire']
        else:
            self.dns_expire = '604800'

    def close_connections(self):
        """
            Close out connections
        """
        self.dbconn.close()
        self.dbsess.close()
        self.dbengine.dispose()

    def load_path(self, config_file):
        """
            Try to guess where the path is or return empty string
        """
        for load_path in load_paths:
            file_path = os.path.join(load_path, config_file)
            if os.path.isfile(file_path):
                return file_path
        return ''
