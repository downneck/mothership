import unittest

from mothership.API_list_servers import * 
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
lss = API_list_servers(cfg)
# needed to keep the KV from freaking out
cfg.module_metadata['API_kv'] = API_kv(cfg)


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
    def test1(self):
        query = {'all': True}
        result = lss.lss(query)

        # pre-define expected output
        self.assertEqual(result, bigassret)
        print "[API_list_servers] test1: PASSED"

    # test empty query, failure results
    def test2(self):
        query = {}
      
        self.assertRaises(ListServersError, lss.lss, query)
        print "[API_list_servers] test2: PASSED"

    # vlan=200, good output
    def test3(self):
        query = {'vlan': 200}
        result = lss.lss(query)

        self.assertEqual(result, bigassret)
        print "[API_list_servers] test3: PASSED"

    # vlan=3400, empty output
    def test4(self):
        query = {'vlan': 3400}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] test4: PASSED"

    # test vlan=garbage, failure output 
    def test5(self):
        query = {'vlan': 'garbage'}
      
        self.assertRaises(ListServersError, lss.lss, query)
        print "[API_list_servers] test5: PASSED"

    # site_id=jfk, good output
    def test6(self):
        query = {'site_id': 'jfk'}
        result = lss.lss(query)

        self.assertEqual(result, bigassret)
        print "[API_list_servers] test6: PASSED"

    # realm=satest, good output
    def test7(self):
        query = {'realm': 'satest'}
        result = lss.lss(query)

        self.assertEqual(result, bigassret)
        print "[API_list_servers] test7: PASSED"

    # ram=4, good output
    def test8(self):
        query = {'ram': 4}
        result = lss.lss(query)

        ret = ['hudson1.satest.jfk', 'hudson2.satest.jfk']

        self.assertEqual(result, ret)
        print "[API_list_servers] test8: PASSED"

    # ram=3, empty output
    def test9(self):
        query = {'ram': 3}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] test9: PASSED"

    # test ram=garbage, failure output 
    def test10(self):
        query = {'ram': 'garbage'}
      
        self.assertRaises(ListServersError, lss.lss, query)
        print "[API_list_servers] test10: PASSED"

    # tag=splunklightforwarder, good output
    def test11(self):
        query = {'tag': 'splunklightforwarder'}
        result = lss.lss(query)

        ret = [
            "stage2.satest.jfk",
            "cobbler1.satest.jfk",
            "ns1.satest.jfk",
            "ns2.satest.jfk"
        ]

        self.assertEqual(result, ret)
        print "[API_list_servers] test11: PASSED"

    # tag=garbage, empty output
    def test12(self):
        query = {'tag': 'garbage'}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] test12: PASSED"

    # disk=200, good output
    def test13(self):
        query = {'disk': 200}
        result = lss.lss(query)

	ret = ['hudson1.satest.jfk', 'hudson2.satest.jfk']

        self.assertEqual(result, ret)
        print "[API_list_servers] test13: PASSED"

    # disk=1, empty output
    def test14(self):
        query = {'disk': 1}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] test14: PASSED"

    # test disk=garbage, failure output 
    def test15(self):
        query = {'disk': 'garbage'}
      
        self.assertRaises(ListServersError, lss.lss, query)
        print "[API_list_servers] test15: PASSED"

    # manufacturer=IBM, good output
    def test16(self):
        query = {'manufacturer': 'IBM'}
        result = lss.lss(query)

        ret = ['zendc1.satest.jfk',]

        # pre-define expected output
        self.assertEqual(result, ret)
        print "[API_list_servers] test16: PASSED"

    # manufacturer=garbage, empty output
    def test17(self):
        query = {'manufacturer': 'garbage'}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] test17: PASSED"

    # virtual=true, good output
    def test18(self):
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
        print "[API_list_servers] test18: PASSED"

    # physical=true, good output
    def test19(self):
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
        print "[API_list_servers] test19: PASSED"

    # test incompatible query parameters, failure results
    def test20(self):
        query = {'physical': True, 'virtual': True}
      
        self.assertRaises(ListServersError, lss.lss, query)
        print "[API_list_servers] test20: PASSED"

    # hw_tag=4VK27L1, good output
    def test21(self):
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
        print "[API_list_servers] test21: PASSED"

    # hw_tag=garbage, empty output
    def test22(self):
        query = {'hw_tag': 'garbage'}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] test22: PASSED"

    # hostname=stage2.satest.jfk, good output
    def test23(self):
        query = {'hostname': 'stage2'}
        result = lss.lss(query)

        # pre-define expected output
        ret = ["stage2.satest.jfk",] 

        self.assertEqual(result, ret)
        print "[API_list_servers] test23: PASSED"

    # hostname=stage2.satest.jfk, good output
    def test24(self):
        query = {'hostname': 'stage2.satest.jfk'}
        result = lss.lss(query)

        # pre-define expected output
        ret = ["stage2.satest.jfk",] 

        self.assertEqual(result, ret)
        print "[API_list_servers] test24: PASSED"

    # hostname=garbage, empty output
    def test25(self):
        query = {'hostname': 'garbage'}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] test25: PASSED"

    # cores=2, good output
    def test26(self):
        query = {'cores': 2}
        result = lss.lss(query)

        # pre-define expected output
        ret = ['hudson1.satest.jfk', 'hudson2.satest.jfk'] 

        self.assertEqual(result, ret)
        print "[API_list_servers] test26: PASSED"

    # cores=132, empty output
    def test27(self):
        query = {'cores': 132}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] test27: PASSED"

    # test cores=garbage, failure output 
    def test28(self):
        query = {'cores': 'garbage'}
      
        self.assertRaises(ListServersError, lss.lss, query)
        print "[API_list_servers] test28: PASSED"

    # test model='System x3650', good results
    def test29(self):
        query = {'model': 'Server x3650'}
        result = lss.lss(query)

        # pre-define expected output
        ret = ['zendc1.satest.jfk']

        self.assertEqual(result, ret)
        print "[API_list_servers] test29: PASSED"

    # test model=garbage, empty results
    def test30(self):
        query = {'model': 'garbage'}
        result = lss.lss(query)

        self.assertEqual(result, [])
        print "[API_list_servers] test30: PASSED"
