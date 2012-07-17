import unittest

from mothership.API_tag import * 
from mothership.API_kv import * 
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
tag = API_tag(cfg)
cfg.module_metadata['API_tag'] = tag
# instantiate lss and kv
lss = API_list_servers(cfg)
cfg.module_metadata['API_list_servers'] = lss
kv = API_kv(cfg)
cfg.module_metadata['API_kv'] = kv

# UnitTesting for API_tag module
class TestAPI_tag(unittest.TestCase):

    ######################################
    # testing display()                  #
    ######################################

    # name=apache, good output
    def test_display_good_result(self):
        query = {'name': 'apache'}
        result = tag.display(query)

        # pre-define expected output
        ret = {
               'start_port': 80,
               'name': 'apache',
               'stop_port': 80,
               'table_name': 'tags',
               'security_level': None,
               'id': 89
        }

        self.assertEqual(result, ret)
        print "[API_tag] BB_test_tag_display_good_result: PASSED"

    # name=puppet, bad output
    def test_tag_display_bad_result(self):
        query = {'name': 'puppet'}
        result = tag.display(query)

        # pre-define unexpected output
        ret = {
               'start_port': 80,
               'name': 'apache',
               'stop_port': 80,
               'table_name': 'tags',
               'security_level': None,
               'id': 89
        }

        self.assertNotEqual(result, ret)
        print "[API_tag] BB_test_tag_display_bad_result: PASSED"

    # name=FAILURE, null results 
    def test_tag_display_bad_name_null_result(self):
        query = {'name': 'FAILURE'}
        result = tag.display(query)

        self.assertEqual(result, None)
        print "[API_tag] BB_test_tag_display_bad_name_null_result: PASSED"


    ######################################
    # testing add()                      #
    ######################################
 
    # test name=None, failure 
    def test_tag_add_name_bad(self):
        query = {'name': None}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_add_name_bad: PASSED (raised TagError)"
 
    # test name=foo, start_port=frank, failure 
    def test_tag_add_name_good_start_port_bad(self):
        query = {'name': 'frank', 'start_port': 'frank'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_name_good_start_port_bad: PASSED (raised TagError)"
 
    # test name=foo, stop_port=frank, failure 
    def test_tag_add_name_good_stop_port_bad(self):
        query = {'name': 'frank', 'stop_port': 'frank'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_name_good_stop_port_bad: PASSED (raised TagError)"
 
    # test name=foo, security_level=frank, failure 
    def test_tag_add_name_good_security_level_bad(self):
        query = {'name': 'frank', 'security_level': 'frank'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_name_good_security_level_bad: PASSED (raised TagError)"
 
    # test name=foo, start_port=80, stop_port=frank, failure 
    def test_tag_add_name_and_start_port_good_stop_port_bad(self):
        query = {'name': 'frank', 'start_port': 80, 'stop_port': 'frank'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_name_and_start_port_good_stop_port_bad: PASSED (raised TagError)"
 
    # test name=foo, stop_port=80, start_port=frank, failure 
    def test_tag_add_name_and_stop_port_good_start_port_bad(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 'frank'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_name_and_stop_port_good_start_port_bad: PASSED (raised TagError)"
 
    # everything good except security_level 
    def test_tag_add_everything_good_except_security_level_failure(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 80, 'security_level': 'fred'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_everything_good_except_security_level_failure: PASSED (raised TagError)"
 
    # everything good except start_port 
    def test_tag_add_everything_good_except_start_port_failure(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 'fred', 'security_level': 1}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_everything_good_except_start_port_failure: PASSED (raised TagError)"
 
    # everything good except stop_port 
    def test_tag_add_everything_good_except_stop_port_failure(self):
        query = {'name': 'frank', 'stop_port': 'fred', 'start_port': 80, 'security_level': 1}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_everything_good_except_stop_port_failure: PASSED (raised TagError)"
 
    # everything good, superfluous query, failure 
    def test_tag_add_everything_good_superfluous_query_failure(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 80, 'security_level': 1, 'durr': 'stuff'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_everything_good_superfluous_query_failure: PASSED (raised TagError)"
 
    # add, everything good, good results 
    def test_tag_add_everything_good(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 80, 'security_level': 1}
        result = tag.add(query)
        tag.delete(query) # clean up after ourselves

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_everything_good: PASSED (raised TagError)"
 

    ######################################
    # testing delete()                   #
    ######################################



    ######################################
    # testing update()                   #
    ######################################

    # test unqdn=decorati1.satest.jfk, key=tag, value='randomstringofcrap',
    # new_value=anotherrandomstringofcrap, good results  
#    def test_tag_update_unqdn_tag_value_and_newvalue_good(self):
#        # set up for the test
#        query = {'unqdn': 'decorati1.satest.jfk', 'key': 'tag', 'value': 'randomstringofcrap'}
#        tag.add(query)
#        # the test
#        query['new_value'] = 'anotherrandomstringofcrap'
#        result = tag.update(query)
#        # set up for cleanup
#        query.pop('new_value')
#        query['value'] = 'anotherrandomstringofcrap'
#        # clean up after ourselves
#        tag.delete(query)
#
#        self.assertEqual(result, 'success')
#        print "[API_tag] BB_test_tag_update_unqdn_tag_value_and_newvalue_good: PASSED"
#
#    # test unqdn=decorati1.satest.jfk, key=tag, value='stringofcrap',
#    # new_value=anotherrandomstringofcrap, good results  
#    def test_tag_update_nonexistent_value_bad(self):
#        # set up for the test
#        query = {'unqdn': 'decorati1.satest.jfk', 'key': 'tag', 'value': 'randomstringofcrap'}
#        # the test
#        query['new_value'] = 'anotherrandomstringofcrap'
#
#        self.assertRaises(TagError, tag.update, query)
#        print "[API_tag] BB_test_tag_update_nonexistent_value_bad: PASSED (raised TagError)"
#
