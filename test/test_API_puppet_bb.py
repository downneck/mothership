import unittest

from mothership.API_puppet import * 
from mothership.API_kv import API_kv
from mothership.configure import *
from mothership.common import *


# globals
###
# load up the config object
cfg = MothershipConfigureDaemon('mothership_daemon.yaml')
cfg.load_config()
# override logging parameters for testing
cfg.log_to_file = False 
cfg.log_to_console = False
# instantiate a logger so the module we're testing doesn't freak out
cfg.log = MothershipLogger(cfg)
# instantiate the main class
p = API_puppet(cfg)
cfg.module_metadata['API_puppet'] = p
# needed to keep the KV from freaking out
cfg.module_metadata['API_kv'] = API_kv(cfg)


# UnitTesting for API_puppet module
class TestAPI_puppet(unittest.TestCase):

    ######################################
    # testing classify()                 #
    ######################################

    # any=True, good output
    def test1(self):
        query = {'unqdn': 'stage2.satest.jfk'}
        result = p.classify(query)
        # pre-define expected output
        ret = {
            "environment": "satest",
            "classes": [
                "tags::stage",
                "baseline",
                "tags::splunklightforwarder"
            ],
            "parameters": {
                "xen_api_pass": "sashimi911",
                "mtag": "stage",
                "site_id": "jfk",
                "mtags": [
                    "stage",
                    "splunklightforwarder"
                ],
                "server_id": 290,
                "realm": "satest",
                "mc_host": "cobbler1",
                "zabbix_server": "zbx1",
                "ldap_master_server": "ldap1.satest.jfk.gilt.local",
                "unqdn": "stage2.satest.jfk",
                "ntp_servers": "xenserver2.satest.jfk",
                "ns": "172.16.20.81,10.190.44.55,10.190.44.93",
                "primary_ip": "10.190.44.52",
                "ssh_authorized_keys_command": "/usr/libexec/openssh/ssh-ldap-helper.sh",
                "ldap_sync_user": "ldapsync",
                "groups": [
                    "stage2_satest_jfk",
                    "satest_jfk",
                    "jfk"
                ],
                "ssh_authorized_keys_command_run_as": "nobody",
                "mc_secret": "359924B5-B1E4-468F-BD94-784FCD366BFA",
                "mc_userpass": "7AFAE79B-BFF1-4673-90DA-47A234CEC55B",
                "mc_user": "middleware",
                "mx": "10 relay1,20 relay2",
                "ldap_sync_pass": "aJLxA33Ng"
            }
        }
        self.assertEqual(result, ret)
        print "[API_puppet] test1: PASSED"

    # test unqdn=garbage, failure results
    def test2(self):
        query = {'unqdn': 'garbage'}
        self.assertRaises(PuppetError, p.classify, query)
        print "[API_puppet] test2: PASSED"

    # test snort=snort, failure results
    def test3(self):
        query = {'snort': 'snort'}
        self.assertRaises(PuppetError, p.classify, query)
        print "[API_puppet] test3: PASSED"
