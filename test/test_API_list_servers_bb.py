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
        print "[API_list_servers] BB_test_lss_empty_query_bad: PASSED (raised ListServersError)"

    # vlan=200, good output
    def test_lss_vlan_good(self):
        query = {'vlan': 200}
        result = lss.lss(query)

        self.assertEqual(result, bigassret)
        print "[API_list_servers] BB_test_lss_vlan_good: PASSED"

    # vlan=3400, empty output
    def test_lss_vlan_empty(self):
        query = {'vlan': 3400}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] BB_test_lss_vlan_empty: PASSED"

    # test vlan=garbage, failure output 
    def test_lss_vlan_bad(self):
        query = {'vlan': 'garbage'}
      
        self.assertRaises(ListServersError, lss.lss, query)
        print "[API_list_servers] BB_test_lss_vlan_bad: PASSED (raised ListServersError)"

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

        self.assertEqual(result, [])
        print "[API_list_servers] BB_test_lss_ram_empty: PASSED"

    # test ram=garbage, failure output 
    def test_lss_ram_bad(self):
        query = {'ram': 'garbage'}
      
        self.assertRaises(ListServersError, lss.lss, query)
        print "[API_list_servers] BB_test_lss_ram_bad: PASSED (raised ListServersError)"

    # tag=splunklightforwarder, good output
    def test_lss_tag_good(self):
        query = {'tag': 'splunklightforwarder'}
        result = lss.lss(query)

        ret = [
            "stage2.satest.jfk",
            "cobbler1.satest.jfk",
            "ns1.satest.jfk",
            "ns2.satest.jfk"
        ]

        self.assertEqual(result, ret)
        print "[API_list_servers] BB_test_lss_tag_good: PASSED"

    # tag=garbage, empty output
    def test_lss_tag_empty(self):
        query = {'tag': 'garbage'}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] BB_test_lss_tag_empty: PASSED"

    # disk=200, good output
    def test_lss_disk_good(self):
        query = {'disk': 200}
        result = lss.lss(query)

	ret = ['hudson1.satest.jfk', 'hudson2.satest.jfk']

        self.assertEqual(result, ret)
        print "[API_list_servers] BB_test_lss_disk_good: PASSED"

    # disk=1, empty output
    def test_lss_disk_empty(self):
        query = {'disk': 1}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] BB_test_lss_tag_empty: PASSED"

    # test disk=garbage, failure output 
    def test_lss_disk_bad(self):
        query = {'disk': 'garbage'}
      
        self.assertRaises(ListServersError, lss.lss, query)
        print "[API_list_servers] BB_test_lss_disk_bad: PASSED (raised ListServersError)"

    # manufacturer=IBM, good output
    def test_lss_manufacturer_good(self):
        query = {'manufacturer': 'IBM'}
        result = lss.lss(query)

        ret = ['zendc1.satest.jfk',]

        # pre-define expected output
        self.assertEqual(result, ret)
        print "[API_list_servers] BB_test_lss_manufacturer_good: PASSED"

    # manufacturer=garbage, empty output
    def test_lss_manufacturer_empty(self):
        query = {'manufacturer': 'garbage'}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] BB_test_lss_manufacturer_empty: PASSED"

    # virtual=true, good output
    def test_lss_virutal_good(self):
        query = {'virtual': True}
        result = lss.lss(query)

        # pre-define expected output
        ret = [
            "cm1.satest.jfk",
            "cm2.satest.jfk",
            "cobbler1.satest.jfk",
            "dcmon1.satest.jfk",
            "hudson1.satest.jfk",
            "hudson2.satest.jfk",
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
            "test2.satest.jfk",
            "test5.satest.jfk",
            "test6.satest.jfk",
            "testeasyinstall.satest.jfk",
            "teststore.satest.jfk",
            "zbx1.satest.jfk",
            "zenoss1.satest.jfk"
        ]

        self.assertEqual(result, ret)
        print "[API_list_servers] BB_test_lss_virtual_good: PASSED"

    # physical=true, good output
    def test_lss_physical_good(self):
        query = {'physical': True}
        result = lss.lss(query)

        # pre-define expected output
        ret = [
            "ci1.satest.jfk",
            "jira1.satest.jfk",
            "swaptest1.satest.jfk",
            "swaptest2.satest.jfk",
            "xenserver1.satest.jfk",
            "xenserver2.satest.jfk",
            "xenserver3.satest.jfk",
            "zendc1.satest.jfk"
        ] 

        self.assertEqual(result, ret)
        print "[API_list_servers] BB_test_lss_physical_good: PASSED"

    # test incompatible query parameters, failure results
    def test_lss_physical_virtual_bad(self):
        query = {'physical': True, 'virtual': True}
      
        self.assertRaises(ListServersError, lss.lss, query)
        print "[API_list_servers] BB_test_lss_physical_virtual_bad: PASSED (raised ListServersError)"

    # hw_tag=4VK27L1, good output
    def test_lss_hw_tag_good(self):
        query = {'hw_tag': '4VK27L1'}
        result = lss.lss(query)

        # pre-define expected output
        ret = [
            "stage2.satest.jfk",
            "stage7.satest.jfk",
            "rpmbuilder1.satest.jfk",
            "xenserver2.satest.jfk",
            "ldap2.satest.jfk",
            "ns2.satest.jfk",
            "puppet.satest.jfk"
        ] 

        self.assertEqual(result, ret)
        print "[API_list_servers] BB_test_lss__hw_tag__good: PASSED"

    # hw_tag=garbage, empty output
    def test_lss_hw_tag_empty(self):
        query = {'hw_tag': 'garbage'}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] BB_test_lss__hw_tag__empty: PASSED"

    # hostname=stage2.satest.jfk, good output
    def test_lss_hostname_only_good(self):
        query = {'hostname': 'stage2'}
        result = lss.lss(query)

        # pre-define expected output
        ret = ["stage2.satest.jfk",] 

        self.assertEqual(result, ret)
        print "[API_list_servers] BB_test_lss_hostname_only_good: PASSED"

    # hostname=stage2.satest.jfk, good output
    def test_lss_hostname_full_unqdn_good(self):
        query = {'hostname': 'stage2.satest.jfk'}
        result = lss.lss(query)

        # pre-define expected output
        ret = ["stage2.satest.jfk",] 

        self.assertEqual(result, ret)
        print "[API_list_servers] BB_test_lss_hostname_full_unqdn_good: PASSED"

    # hostname=garbage, empty output
    def test_lss_hostname_garbage_empty(self):
        query = {'hostname': 'garbage'}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] BB_test_lss_hostname_garbage_empty: PASSED"

    # cores=2, good output
    def test_lss_cores_good(self):
        query = {'cores': 2}
        result = lss.lss(query)

        # pre-define expected output
        ret = ['hudson1.satest.jfk', 'hudson2.satest.jfk'] 

        self.assertEqual(result, ret)
        print "[API_list_servers] BB_test_lss_cores_good: PASSED"

    # cores=132, empty output
    def test_lss_cores_empty(self):
        query = {'cores': 132}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] BB_test_lss_cores_empty: PASSED"

    # test cores=garbage, failure output 
    def test_lss_cores_bad(self):
        query = {'cores': 'garbage'}
      
        self.assertRaises(ListServersError, lss.lss, query)
        print "[API_list_servers] BB_test_lss_cores_bad: PASSED (raised ListServersError)"

    # test model='System x3650', good results
    def test_lss_model_good(self):
        query = {'model': 'Server x3650'}
        result = lss.lss(query)

        # pre-define expected output
        ret = ['zendc1.satest.jfk']

        self.assertEqual(result, ret)
        print "[API_list_servers] BB_test_lss_model_good: PASSED"

    # test model=garbage, empty results
    def test_lss_model_empty(self):
        query = {'model': 'garbage'}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] BB_test_lss_model_empty: PASSED"
