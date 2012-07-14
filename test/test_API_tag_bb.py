import unittest

from mothership.API_tag import * 
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
 
    # test unqdn=decorati1.satest.jfk, failure results  
    def test_kv_add_unqdn_bad(self):
        query = {'unqdn': 'decorati1.satest.jfk'}

        self.assertRaises(KVError, kv.add, query)
        print "[API_tag] BB_test_kv_add_unqdn_bad: PASSED (raised KVError)"
 
    # test unqdn=decorati1.satest.jfk, key=tag, failure results  
    def test_kv_add_unqdn_and_tag_bad(self):
        query = {'unqdn': 'decorati1.satest.jfk', 'key': 'tag'}

        self.assertRaises(KVError, kv.add, query)
        print "[API_tag] BB_test_kv_add_unqdn_and_tag_bad: PASSED (raised KVError)"
 
    # test unqdn=decorati1.satest.jfk, key=tag, value='randomstringofcrap', good results  
    def test_kv_add_unqdn_tag_and_value_good(self):
        query = {'unqdn': 'decorati1.satest.jfk', 'key': 'tag', 'value': 'randomstringofcrap'}
        result = kv.add(query)
        kv.delete(query) # clean up after ourselves

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_kv_add_unqdn_tag_and_value_good: PASSED"

    # test unqdn=decorati1.satest.jfk, key=tag, value='apache', failure results  
    def test_kv_add_duplicate_unqdn_tag_and_value_bad(self):
        query = {'unqdn': 'decorati1.satest.jfk', 'key': 'tag', 'value': 'apache'}

        self.assertRaises(KVError, kv.add, query)
        print "[API_tag] BB_test_kv_add_duplicate_unqdn_tag_and_value_bad: PASSED (raised KVError)"


    ######################################
    # testing delete()                   #
    ######################################

    # test unqdn=decorati1.satest.jfk, key=tag, value='randomstringofcrap', good results  
    def test_kv_delete_unqdn_tag_and_value_good(self):
        query = {'unqdn': 'decorati1.satest.jfk', 'key': 'tag', 'value': 'randomstringofcrap'}
        kv.add(query) # setup for the test
        result = kv.delete(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_kv_delete_unqdn_tag_and_value_good: PASSED"

    # test unqdn=decorati1.satest.jfk, key=tag, value='randomstringofcrap', failure results  
    def test_kv_delete_nonexistent_unqdn_tag_and_value_bad(self):
        query = {'unqdn': 'decorati1.satest.jfk', 'key': 'tag', 'value': 'randomstringofcrap'}

        self.assertRaises(KVError, kv.delete, query)
        print "[API_tag] BB_test_kv_delete_nonexistent_unqdn_tag_and_value_bad: PASSED (raised KVError)"

    # test unqdn=decorati1.satest.jfk, failure results 
    def test_kv_delete_unqdn_only_bad(self):
        query = {'unqdn': 'decorati1.satest.jfk'}

        self.assertRaises(KVError, kv.delete, query)
        print "[API_tag] BB_test_kv_delete_unqdn_only_bad: PASSED (raised KVError)"


    ######################################
    # testing update()                   #
    ######################################

    # test unqdn=decorati1.satest.jfk, key=tag, value='randomstringofcrap',
    # new_value=anotherrandomstringofcrap, good results  
    def test_kv_update_unqdn_tag_value_and_newvalue_good(self):
        # set up for the test
        query = {'unqdn': 'decorati1.satest.jfk', 'key': 'tag', 'value': 'randomstringofcrap'}
        kv.add(query)
        # the test
        query['new_value'] = 'anotherrandomstringofcrap'
        result = kv.update(query)
        # set up for cleanup
        query.pop('new_value')
        query['value'] = 'anotherrandomstringofcrap'
        # clean up after ourselves
        kv.delete(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_kv_update_unqdn_tag_value_and_newvalue_good: PASSED"

    # test unqdn=decorati1.satest.jfk, key=tag, value='stringofcrap',
    # new_value=anotherrandomstringofcrap, good results  
    def test_kv_update_nonexistent_value_bad(self):
        # set up for the test
        query = {'unqdn': 'decorati1.satest.jfk', 'key': 'tag', 'value': 'randomstringofcrap'}
        # the test
        query['new_value'] = 'anotherrandomstringofcrap'

        self.assertRaises(KVError, kv.update, query)
        print "[API_tag] BB_test_kv_update_nonexistent_value_bad: PASSED (raised KVError)"

