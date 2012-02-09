################################################
# ACHTUNG! ACHTUNG! ACHTUNG! ACHTUNG! ACHTUNG! #
#                                              #
# this is an example file for how to set up a  #
# black box unit test. example module is the   #
# API_list_servers module                      #
################################################
# do not actually run this thing               #
# rename it to "test_something_or_other.py"    #
# before converting it to use for your module  #
################################################

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


# UnitTesting for API_list_servers module
class TestAPI_list_servers(unittest.TestCase):

    ######################################
    # testing select()                   #
    ######################################

    # any=True, good output
    def test_kv_select_any_good(self):
        query = {'any': True}
        result = kv.select(query)

        # pre-define expected output
        ret = [{
               'realm': None,
               'hostname': None,
               'site_id': None,
               'value': '359924B5-B1E4-468F-BD94-784FCD366BFA',
               'table_name': 'kv',
               'key': 'mc_secret',
               'id': 1
        },]

        self.assertEqual(result, ret)
        print "****** test_kv_select_any_good: PASSED"

    # test unqdn=garbage, failure results
    def test_kv_select_unqdn_garbage_input_bad(self):
        query = {'unqdn': 'garbage'}

        self.assertRaises(KVError, kv.select, query)
        print "****** test_kv_select_garbage_input_bad: PASSED (raised KVError)"

