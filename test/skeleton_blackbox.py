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
# ensure we populate the metadata
cfg.module_metadata['API_list_servers'] = lss

# UnitTesting for API_list_servers module
class TestAPI_list_servers(unittest.TestCase):

    ######################################
    # testing lss()                      #
    ######################################

    # any=True, good output
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
