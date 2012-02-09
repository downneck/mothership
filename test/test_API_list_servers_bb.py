import unittest

from mothership.API_list_servers import * 
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
lss = API_list_servers(cfg)

bigassret = [
    "ci1.satest.jfk",
    "cm1.satest.jfk",
    "cm2.satest.jfk",
    "cobbler1.satest.jfk",
    "dcmon1.satest.jfk",
    "hudson1.satest.jfk",
    "hudson2.satest.jfk",
    "jira1.satest.jfk",
    "ldap1.satest.jfk",
    "ldap2.satest.jfk",
    "mtest3.satest.jfk",
    "ns1.satest.jfk",
    "ns2.satest.jfk",
    "puppet.satest.jfk",
    "rpmbuilder1.satest.jfk",
    "solr12.satest.jfk",
    "splunk1.satest.jfk",
    "stage2.satest.jfk",
    "stage7.satest.jfk",
    "swaptest1.satest.jfk",
    "swaptest2.satest.jfk",
    "test2.satest.jfk",
    "test5.satest.jfk",
    "test6.satest.jfk",
    "testeasyinstall.satest.jfk",
    "teststore.satest.jfk",
    "xenserver1.satest.jfk",
    "xenserver2.satest.jfk",
    "xenserver3.satest.jfk",
    "zbx1.satest.jfk",
    "zendc1.satest.jfk",
    "zenoss1.satest.jfk"
]


# UnitTesting for API_list_servers module
class TestAPI_list_servers(unittest.TestCase):

    ######################################
    # testing lss()                      #
    ######################################

    # all=True, good output
    def test_lss_all_good(self):
        query = {'all': True}
        result = lss.lss(query)

        # pre-define expected output
        self.assertEqual(result, bigassret)
        print "[API_list_servers] BB_test_lss_all_good: PASSED"

    # test empty query, failure results
    def test_lss_empty_query_bad(self):
        query = {}
      
        self.assertRaises(ListServersError, lss.lss, query)
        print "[API_list_servers] BB_test_kv_select_garbage_input_bad: PASSED (raised ListServersError)"

    # vlan=200, good output
    def test_lss_vlan_good(self):
        query = {'vlan': '200'}
        result = lss.lss(query)

        self.assertEqual(result, bigassret)
        print "[API_list_servers] BB_test_lss_vlan_good: PASSED"

    # site_id=jfk, good output
    def test_lss_site_id_good(self):
        query = {'site_id': 'jfk'}
        result = lss.lss(query)

        self.assertEqual(result, bigassret)
        print "[API_list_servers] BB_test_lss__site_id__good: PASSED"

    # realm=satest, good output
    def test_lss_realm_good(self):
        query = {'realm': 'satest'}
        result = lss.lss(query)

        self.assertEqual(result, bigassret)
        print "[API_list_servers] BB_test_lss_realm_good: PASSED"

    # ram=4, good output
    def test_lss_ram_good(self):
        query = {'ram': 4}
        result = lss.lss(query)

        ret = ['hudson1.satest.jfk', 'hudson2.satest.jfk']

        self.assertEqual(result, ret)
        print "[API_list_servers] BB_test_lss_ram_good: PASSED"

    # ram=3, empty output
    def test_lss_ram_empty(self):
        query = {'ram': 3}
        result = lss.lss(query)

        ret = []

        self.assertEqual(result, ret)
        print "[API_list_servers] BB_test_lss_ram_empty: PASSED"
