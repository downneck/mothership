import unittest

from mothership.API_serverinfo import * 
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
si = API_serverinfo(cfg)
cfg.module_metadata['API_serverinfo'] = si
# needed to keep the KV from freaking out
cfg.module_metadata['API_kv'] = API_kv(cfg)


# giant return constant for xenserver2.satest.jfk
bigassret = {
    "hardware": {
      "manufacturer": "Dell",
      "cost": None,
      "table_name": "hardware",
      "kvm_port": None,
      "ram": None,
      "site_id": "jfk",
      "kvm_switch": None,
      "power_switch": "",
      "rma": False,
      "hw_tag": "4VK27L1",
      "power_port": None,
      "cpu_speed": None,
      "cores": None,
      "model": "PowerEdge R610",
      "disk": "2 x 73GB SAS, 4 x 146GB SAS",
      "rack_id": None,
      "id": 116,
      "cpu_sockets": None,
      "purchase_date": "2010-09-23"
    },
    "server": {
      "comment": None,
      "ram": None,
      "realm": "satest",
      "table_name": "servers",
      "hostname": "xenserver2",
      "site_id": "jfk",
      "virtual": False,
      "tag_index": None,
      "provision_date": "None",
      "tag": "xen",
      "hw_tag": "4VK27L1",
      "security_level": None,
      "active": None,
      "cores": None,
      "cobbler_profile": "xenserver560-gilt",
      "disk": None,
      "os": None,
      "id": 277,
      "cost": None
    },
    "network": [
      {
        "bond_options": None,
        "server_id": 277,
        "mac": "00:21:9b:98:49:24",
        "realm": "mgmt",
        "switch_port": None,
        "ip": "172.16.20.9",
        "vlan": 200,
        "site_id": "jfk",
        "switch": None,
        "public_ip": None,
        "table_name": "network",
        "netmask": "255.255.255.0",
        "hw_tag": "4VK27L1",
        "interface": "eth0",
        "static_route": None,
        "id": 963
      },
      {
        "bond_options": "mode=active-backup miimon=10",
        "server_id": 277,
        "mac": "00:21:9b:98:49:26",
        "realm": "satest",
        "switch_port": None,
        "ip": "10.190.44.9",
        "vlan": 201,
        "site_id": "jfk",
        "switch": None,
        "public_ip": None,
        "table_name": "network",
        "netmask": "255.255.255.0",
        "hw_tag": "4VK27L1",
        "interface": "eth1",
        "static_route": None,
        "id": 964
      },
      {
        "bond_options": "mode=active-backup miimon=10",
        "server_id": 277,
        "mac": "00:21:9b:98:49:28",
        "realm": "satest",
        "switch_port": None,
        "ip": None,
        "vlan": None,
        "site_id": "jfk",
        "switch": None,
        "public_ip": None,
        "table_name": "network",
        "netmask": "255.255.255.0",
        "hw_tag": "4VK27L1",
        "interface": "eth2",
        "static_route": None,
        "id": 965
      }
    ],
    "kv": []
  }


# UnitTesting for API_serverinfo module
class TestAPI_serverinfo(unittest.TestCase):

    ######################################
    # testing si()                       #
    ######################################

    # unqdn=xenserver2.satest.jfk, good output
    def test_si_unqdn_good(self):
        query = {'unqdn': 'xenserver2.satest.jfk'}
        result = si.si(query)

        self.assertEqual(result, bigassret)
        print "[API_serverinfo] BB_test_si_unqdn_good: PASSED"

    # unqdn=garbage, bad output
    def test_si_unqdn_bad(self):
        query = {'unqdn': 'garbage'}

        self.assertRaises(ServerInfoError, si.si, query)
        print "[API_serverinfo] BB_test_si_unqdn_bad: PASSED (raised ServerInfoError)"

    # hw_tag=4VK27L1, good output
    def test_si_hwtag_good(self):
        query = {'hw_tag': '4VK27L1'}
        result = si.si(query)

        self.assertEqual(result, bigassret)
        print "[API_serverinfo] BB_test_si__hw_tag__good: PASSED"

    # hw_tag=garbage, bad output
    def test_si_hw_tag_bad(self):
        query = {'hw_tag': 'garbage'}

        self.assertRaises(ServerInfoError, si.si, query)
        print "[API_serverinfo] BB_test_si__hw_tag__bad: PASSED (raised ServerInfoError)"

    # mac=00:21:9b:98:49:24, good output
    def test_si_mac_good(self):
        query = {'mac': '00:21:9b:98:49:24'}
        result = si.si(query)

        self.assertEqual(result, bigassret)
        print "[API_serverinfo] BB_test_si_mac_good: PASSED"

    # mac=00:00:00:00:00:00, bad output
    def test_si_mac_bad(self):
        query = {'mac': '00:00:00:00:00:00'}

        self.assertRaises(ServerInfoError, si.si, query)
        print "[API_serverinfo] BB_test_si_mac_bad: PASSED (raised ServerInfoError)"

    # ip=123.123.123.123, good output
    def test_si_ip_good(self):
        query = {'ip': '10.190.44.9'}
        result = si.si(query)

        self.assertEqual(result, bigassret)
        print "[API_serverinfo] BB_test_si_ip_good: PASSED"

    # ip=garbage, bad output
    def test_si_ip_bad(self):
        query = {'ip': '1.1.1.1'}

        self.assertRaises(ServerInfoError, si.si, query)
        print "[API_serverinfo] BB_test_si_ip_bad: PASSED (raised ServerInfoError)"

    # test unqdn=garbage, failure results
    def test_si_unknown_query_key_bad(self):
        query = {'blargle': 'garbage'}

        self.assertRaises(ServerInfoError, si.si, query)
        print "[API_serverinfo] BB_test_si_unqknown_query_key_bad: PASSED (raised ServerInfoError)"
