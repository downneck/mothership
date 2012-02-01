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
# a config_file
load_paths = ['.', '~', '/etc', '/usr/local/etc']


# configuration options common to CLI and Daemon versions. These options
# should appear in BOTH .yaml files
class MothershipConfigure(object):
    def __init__(self, config_file):
        """
            Takes a config_file name as a parameter and searches through the following
            dirs to load the configuration file:  /etc, CWD
        """
        # Read settings from configuration yaml
        try:
            yaml_config = open(self.load_path(config_file)).read()
            self.all_configs = yaml.load(yaml_config)
        except Exception, e:
            raise ConfigureError("Error loading config file: %s\nConfig search paths: %s\nError: %s" % (config_file, load_paths, e))

        # Logging settings
        all_configs = self.all_configs
        logconfig = all_configs['logconfig']
        # log directory, default is /var/log/mothership
        if 'logdir' in logconfig and logconfig['logdir']:
            self.logdir = logconfig['logdir']
        else:
            self.logdir = '/var/log/mothership/'
        # do we log to a file?
        # default is False
        if 'log_to_file' in logconfig and logconfig['log_to_file']:
            self.log_to_file = logconfig['log_to_file']
        else:
            self.log_to_file = False
        # do we log to console? 
        # default is False
        if 'log_to_console' in logconfig and logconfig['log_to_console']:
            self.log_to_console = logconfig['log_to_console']
        else:
            self.log_to_console = False
        # logfile to write our main log to. no default
        if 'logfile' in logconfig and logconfig['logfile']:
            self.logfile = logconfig['logfile']
        else:
            self.logfile = 'mothership.log'
        # log level, corresponds to unix syslog priority levels
        # DEBUG, ERROR, WARNING, INFO
        if 'log_level' in logconfig and logconfig['log_level']:
            self.log_level = logconfig['log_level']
        else:
            self.log_level = 'DEBUG'
        # audit log filename, default is mothership_audit.log
        # logs all command line calls
        if 'audit_log_file' in logconfig and logconfig['audit_log_file']:
            self.audit_log_file = logconfig['audit_log_file']
        else:
            self.audit_log_file = 'mothership_audit.log'


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



# configuration options for the CLI. these options should appear ONLY in
# mothership_cli.yaml
class MothershipConfigureCli(MothershipConfigure):
    def load_config(self):

        all_configs = self.all_configs

        genconfig = all_configs['general']
        # api server hostname, used to tell the command line where to
        # send REST requests. default is "localhost"
        if 'api_server' in genconfig and genconfig['api_server']:
            self.api_server = genconfig['api_server']
        else:
            self.api_server = 'localhost'
        # api port, used to tell the command line where to send REST
        # requests. default is "8081"
        if 'api_port' in genconfig and genconfig['api_port']:
            self.api_port = genconfig['api_port']
        else:
            self.api_port = '8081'



# configuration options for the Daemon. these options should appear ONLY
# in mothership_daemon.yaml
class MothershipConfigureDaemon(MothershipConfigure):
    def load_config(self):
        """
            Takes a config_file name as a parameter and searches through the following
            dirs to load the configuration file:  /etc, CWD
        """
        # module metadata for API module loader
        self.module_metadata = {}
        all_configs = self.all_configs

        # Database related settings
        dbconfig = all_configs['db']
        # try to create a DB engine with sqlalchemy
        try:
            engine = ''
            # PostgreSQL
            if dbconfig['engine'] == 'postgresql':
                dbtuple = (dbconfig['user'], dbconfig['hostname'], dbconfig['dbname'])
                engine = sqlalchemy.create_engine("postgresql://%s@%s/%s" % dbtuple, echo=dbconfig['echo'])
            elif dbconfig['engine'] == 'postgres':
                dbtuple = (dbconfig['user'], dbconfig['hostname'], dbconfig['dbname'])
                engine = sqlalchemy.create_engine("postgres://%s@%s/%s" % dbtuple, echo=dbconfig['echo'])
            # MySql
            elif dbconfig['engine'] == 'mysql':
                dbtuple = (dbconfig['user'], dbconfig['pass'], dbconfig['hostname'], dbconfig['dbname'])
                engine = sqlalchemy.create_engine("mysql://%s:%s@%s/%s" % dbtuple, echo=dbconfig['echo'])
            # uhhhh....
            else:
                raise ConfigureError("DB section of /etc/mothership_daemon.yaml is misconfigured! Exiting")
            # now that we have an engine, bind it to a session
            Session = sqlalchemy.orm.sessionmaker(bind=engine)
            dbsession = Session()
            self.dbconfig = dbconfig
            self.dbconn = engine.connect()
            self.dbengine = engine
            self.dbsess = dbsession
            self.dbnull = sqlalchemy.sql.expression.null()
        except Exception, e:
            raise ConfigureError("Database configuration error. dbtuple: %s, engine: %s. Error: %s" % (dbtuple, engine, e))

        # Cobbler related settings
        cobconfig = all_configs['cobbler']
        # Only ping cobbler server if configured to
        self.coblive = False
        if cobconfig.has_key('active'):
            self.coblive = cobconfig['active']
        if self.coblive:
            try:
                self.remote = xmlrpclib.Server('http://%s/cobbler_api' % cobconfig['host'])
                self.token = self.remote.login(cobconfig['user'], cobconfig['pass'])
            except Exception, e:
                sys.stderr.write("Cobbler configuration error.  Check cobbler API server. Error: %s" % e)
        else:
            self.cobremote = 'API: set remote = xmlrpclib.Server(\'http://server/cobbler_api\')'
            self.cobtoken = 'API: set token = remote.login(user, pass)'

        # Power related settings
        pwrconfig = all_configs['power']
        # username for power calls
        if 'user' in pwrconfig and pwrconfig['user']:
            self.puser = pwrconfig['user']
        else:
            self.puser = 'api'
        # password for power calls
        if 'pass' in pwrconfig and pwrconfig['pass']:
            self.ppass = pwrconfig['pass']
        else:
            self.ppass = 'api'

        # DRAC related settings
        draconfig = all_configs['drac']
        # default dell pass
        if 'dell' in draconfig and draconfig['dell']:
            self.ddell = draconfig['dell']
        else:
            self.ddell = 'calvin'
        # drac root user, default is "root"
        if 'user' in draconfig and draconfig['user']:
            self.duser = draconfig['user']
        else:
            self.duser = 'root'
        # drac root pass, default is "CHANGE_ME_PLEASE"
        if 'pass' in draconfig and draconfig['pass']:
            self.dpass = draconfig['pass']
        else:
            self.dpass = 'CHANGE_ME_PLEASE'
        # list of users for public keys, default is "root, postgres"
        if 'keys' in draconfig and draconfig['keys']:
            self.dkeys = draconfig['keys']
        else:
            self.dkeys = [ 'root', 'postgres' ]
        # trusted drac user, default is "gold"
        if 'trust' in draconfig and draconfig['trust']:
            self.dgold = draconfig['trust']
        else:
            self.dgold = 'gold'

        # SNMP related settings
        snmpconfig = all_configs['snmp']
        # snmp hosts. anyone know what this is for?
        if 'hosts' in snmpconfig and snmpconfig['hosts']:
            self.snmphosts = snmpconfig['hosts']
        else:
            self.snmphosts = [ '10.0.0.1', '10.0.0.3' ]
        # snmp RO community string, default is "public"
        if 'community' in snmpconfig and snmpconfig['community']:
            self.snmpread = snmpconfig['community']
        else:
            self.snmpread ='public'
        # snmp version, default is "2c"
        if 'version' in snmpconfig and snmpconfig['version']:
            self.snmpver = snmpconfig['version']
        else:
            self.snmpver = '2c'

        # KV settings
        kvconfig = all_configs['kv']
        # kv search path, this should probably be deprecated
        if 'search_path' in kvconfig and kvconfig['search_path']:
            self.search_path = kvconfig['search_path']
        else:
            self.search_path = [ ['prod', 'iad'], ['iad'], [] ]

        # Zenoss settings
        zenconfig = all_configs['zenoss']
        # whether to activate the zenoss module. default is False
        if 'active' in zenconfig and zenconfig['active']:
            self.zenlive = zenconfig['active']
        else:
            self.zenlive = False

        # General settings
        genconfig = all_configs['general']
        # our domain, default is "localhost.localdomain"
        if 'domain' in genconfig and genconfig['domain']:
            self.domain = genconfig['domain']
        else:
            self.domain = 'localhost.localdomain'
        # main contact, for alerts and such. default is
        # "hostmaster@localhost.localdomain"
        if 'contact' in genconfig and genconfig['contact']:
            self.contact = genconfig['contact']
        else:
            self.contact = 'hostmaster@localhost.localdomain'
        # allowed realms, default is "prod, qa"
        if 'realms' in genconfig and genconfig['realms']:
            self.realms = genconfig['realms']
        else:
            self.realms = ['prod', 'qa']
        # allowed site_ids, default is "iad, sfo"
        if 'site_ids' in genconfig and genconfig['site_ids']:
            self.site_ids = genconfig['site_ids']
        else:
            self.site_ids = ['iad', 'sfo']
        # default public ip (for non static NATs), default is nonsense
        if 'publicip' in genconfig and genconfig['publicip']:
            self.def_public_ip = genconfig['publicip']
        else:
            self.def_public_ip = '123.123.123.123'
        # allow sudo without passwords, default is True
        if 'sudo_nopass' in genconfig and genconfig['sudo_nopass']:
            self.sudo_nopass = genconfig['sudo_nopass']
        else:
            self.sudo_nopass = True

        # Virtual Machine settings
        vmconfig = all_configs['vm']
        # default minimum specs for new Virtual Machine creation
        # for use with xen, vmware, etc.
        # default is: 1 core, 1GB ram, 25GB hard disk
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
        # whether to activate the zabbix module, default is False
        if 'active' in zabconfig and zabconfig['active']:
            self.zab_active = zabconfig['active']
        else:
            self.zab_active = False

        # Network settings
        netconf = all_configs['network']
        # suck in the network map construct from the yaml.
        # THERE IS NO DEFAULT FOR THIS. YOU MUST SPECIFY IT IN THE YAML.
        self.network_map = netconf['map']
        # Management Vlan settings
        # This can be set to either 'snmp' or 'curl' depending on what
        # style of management you want to use. default is "snmp"
        if 'mgmt_facility' in netconf and netconf['mgmt_facility']:
            self.mgmt_vlan_style = netconf['mgmt_facility']
        else:
            self.mgmt_vlan_style = 'snmp'
        # the interface your management vlan uses. default is eth0
        if 'mgmt_interface' in netconf and netconf['mgmt_interface']:
            self.mgmt_vlan_interface = netconf['mgmt_interface']
        else:
            self.mgmt_vlan_interface = 'eth0'
        # some operations to set the management vlan up
        # if we're using curl, we don't need the snmp settings
        if self.mgmt_vlan_style == 'curl':
            self.mgmt_vlan_enable_url = netconf['mgmt_enable_url']
            self.mgmt_vlan_disable_url = netconf['mgmt_disable_url']
            self.mgmt_vlan_status_url = netconf['mgmt_status_url']
        # if we're using snmp, we need a RW community string. default is
        # "public" which is a terrible default
        elif self.mgmt_vlan_style == 'snmp':
            if 'mgmt_community' in netconf and netconf['mgmt_community']:
                self.mgmt_vlan_community = netconf['mgmt_community']
            else:
                self.mgmt_vlan_community = 'public'
        else:
            sys.stderr.write("mgmt_vlan->facility has been set incorrectly in the config.\nplease edit /etc/mothership_daemon.yaml and set it to either 'snmp' or 'curl'")

        # Users and Groups settings
        ugconfig = all_configs['users_and_groups']
        # User settings
        # default home parent dir for your users. default is /home
        if 'hdir' in ugconfig and ugconfig['hdir']:
            self.hdir = ugconfig['hdir']
        else:
            self.hdir = '/home'
        # default shell for users, default is /bin/bash
        if 'shell' in ugconfig and ugconfig['shell']:
            self.shell = ugconfig['shell']
        else:
            self.shell = '/bin/bash'
        ##### TODO ##### review this. may need to be deprecated
        # email domain. do we even use this any more?
        if 'email_domain' in ugconfig and ugconfig['email_domain']:
            self.email_domain = ugconfig['email_domain']
        else:
            self.email_domain = 'company.com'
        ##### /TODO #####
        # lowest UID to start provisioning from. default is 500
        # MOTHERSHIP WILL NOT ALLOW PROVISIONING BELOW THIS
        if 'uid_start' in ugconfig and ugconfig['uid_start']:
            self.uid_start = int(ugconfig['uid_start'])
        else:
            self.uid_start = 500
        # highest UID to provision to. default is 65535
        # MOTHERSHIP WILL NOT ALLOW PROVISIONING BEYOND THIS
        if 'uid_end' in ugconfig and ugconfig['uid_end']:
            self.uid_end = int(ugconfig['uid_end'])
        else:
            self.uid_end = 65535
        # allowed user types. default is "employee, consultant, system"
        if 'user_types' in ugconfig and ugconfig['user_types']:
            self.user_types = ugconfig['user_types']
        else:
            self.user_types = ['employee', 'consultant', 'system']
        # default user type if none is specified on the command line
        # default is "employee"...obviously this should be one of the
        # allowed user types above.
        if 'def_user_type' in ugconfig and ugconfig['def_user_type']:
            self.def_user_type = ugconfig['def_user_type']
        else:
            self.def_user_type = 'employee'
        # Group settings
        # lowest GID to start provisioning from. default is 500
        # MOTHERSHIP WILL NOT ALLOW PROVISIONING BELOW THIS
        if 'gid_start' in ugconfig and ugconfig['gid_start']:
            self.gid_start = int(ugconfig['gid_start'])
        else:
            self.gid_start = 500
        # highest GID to provision to. default is 65535
        # MOTHERSHIP WILL NOT ALLOW PROVISIONING BEYOND THIS
        if 'gid_end' in ugconfig and ugconfig['gid_end']:
            self.gid_end = int(ugconfig['gid_end'])
        else:
            self.gid_end = 65535
        # all users are put into the default groups when the user is
        # created. default is "users"
        if 'default_groups' in ugconfig and ugconfig['default_groups']:
            self.default_groups = ugconfig['default_groups']
        else:
            self.default_groups = ['users',]

        # LDAP settings
        ldconfig = all_configs['ldap']
        # whether to activate the LDAP module. default is False
        if 'active' in ldconfig and ldconfig['active']:
            self.ldap_active = ldconfig['active']
        else:
            self.ldap_active = False
        # ldap OU (organizational unit) for users. default is "users"
        if 'users_ou' in ldconfig and ldconfig['users_ou']:
            self.ldap_users_ou = ldconfig['users_ou']
        else:
            self.ldap_users_ou = 'users'
        # ldap OU (organizational unit) for groups. default is "groups"
        if 'groups_ou' in ldconfig and ldconfig['groups_ou']:
            self.ldap_groups_ou = ldconfig['groups_ou']
        else:
            self.ldap_groups_ou = 'groups'
        # LDAP connection success code.
        # DO NOT CHANGE THIS unless you know what you're doing
        # default is 97
        if 'ldap_success' in ldconfig and ldconfig['ldap_success']:
            self.ldap_success = ldconfig['ldap_success']
        else:
            self.ldap_success = 97
        # Default gidNumber for posixGroup , should match value
        # associated to the first entry of default_groups array
        # default is "500"
        if 'default_gid' in ldconfig and ldconfig['default_gid']:
            self.ldap_default_gid = ldconfig['default_gid']
        else:
            self.ldap_default_gid = '500'


