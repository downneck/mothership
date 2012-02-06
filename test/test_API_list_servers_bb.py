import unittest

from mothership.API_list_servers import * 
from mothership.configure import *
import mothership.validate
from mothership.common import *

from sqlalchemy import or_, desc, MetaData


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
        ret = [
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
        self.assertEqual(result, ret)
        print "****** test_lss_all_good: PASSED"

    # test empty query, failure results
    def test_lss_empty_query_bad(self):
        query = {}
      
        self.assertRaises(ListServersError, lss.lss, query)
        print "****** test_kv_select_garbage_input_bad: PASSED (raised ListServersError)"

    # all=True, good output
    def test_lss_all_good(self):
        query = {'all': True}
        result = lss.lss(query)

        # pre-define expected output
        ret = [
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
        self.assertEqual(result, ret)
        print "****** test_lss_all_good: PASSED"
