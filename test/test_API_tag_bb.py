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
# instantiate kv
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
        print "[API_tag] BB_test_tag_add_name_good_start_port_bad: PASSED (raised TagError)"
 
    # test name=foo, stop_port=frank, failure 
    def test_tag_add_name_good_stop_port_bad(self):
        query = {'name': 'frank', 'stop_port': 'frank'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_add_name_good_stop_port_bad: PASSED (raised TagError)"
 
    # test name=foo, security_level=frank, failure 
    def test_tag_add_name_good_security_level_bad(self):
        query = {'name': 'frank', 'security_level': 'frank'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_add_name_good_security_level_bad: PASSED (raised TagError)"
 
    # test name=foo, start_port=80, stop_port=frank, failure 
    def test_tag_add_name_and_start_port_good_stop_port_bad(self):
        query = {'name': 'frank', 'start_port': 80, 'stop_port': 'frank'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_add_name_and_start_port_good_stop_port_bad: PASSED (raised TagError)"
 
    # test name=foo, stop_port=80, start_port=frank, failure 
    def test_tag_add_name_and_stop_port_good_start_port_bad(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 'frank'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_add_name_and_stop_port_good_start_port_bad: PASSED (raised TagError)"
 
    # everything good except security_level 
    def test_tag_add_everything_good_except_security_level_failure(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 80, 'security_level': 'fred'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_add_everything_good_except_security_level_failure: PASSED (raised TagError)"
 
    # everything good except start_port 
    def test_tag_add_everything_good_except_start_port_failure(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 'fred', 'security_level': 1}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_add_everything_good_except_start_port_failure: PASSED (raised TagError)"
 
    # everything good except stop_port 
    def test_tag_add_everything_good_except_stop_port_failure(self):
        query = {'name': 'frank', 'stop_port': 'fred', 'start_port': 80, 'security_level': 1}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_add_everything_good_except_stop_port_failure: PASSED (raised TagError)"
 
    # everything good, superfluous query, failure 
    def test_tag_add_everything_good_superfluous_query_failure(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 80, 'security_level': 1, 'durr': 'stuff'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_add_everything_good_superfluous_query_failure: PASSED (raised TagError)"
 
    # everything good, good results 
    def test_tag_add_everything_good(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 80, 'security_level': 1}
        result = tag.add(query)
        # put everything back where we found it
        tag.delete(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_add_everything_good: PASSED"
 
    # just name, stop, start, good results 
    def test_tag_add_name_stop_start_good(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 80}
        result = tag.add(query)
        # put everything back where we found it
        tag.delete(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_add_name_stop_start_good: PASSED"
 
    # just name, stop, security_level, failure
    def test_tag_add_name_stop_security_failure(self):
        query = {'name': 'frank', 'stop_port': 80, 'security_level': 1}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_add_name_stop_security_failure: PASSED (raised TagError)"
 
    # just name, security, start, failure 
    def test_tag_add_name_security_start_failure(self):
        query = {'name': 'frank', 'security_level': 1, 'start_port': 80}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] BB_test_tag_add_name_security_start_failure: PASSED (raised TagError)"
 
    # just name, good results 
    def test_tag_add_name_good(self):
        query = {'name': 'frank'}
        result = tag.add(query)
        # put everything back where we found it
        tag.delete(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_add_name_good: PASSED"
 
    # just name, security, good results 
    def test_tag_add_name_security_good(self):
        query = {'name': 'frank', 'security_level': 1}
        result = tag.add(query)
        # put everything back where we found it
        tag.delete(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_add_name_security_good: PASSED"
 

    ######################################
    # testing delete()                   #
    ######################################

    # just name, good results 
    def test_tag_delete_name_good(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 80, 'security_level': 1}
        tag.add(query)
        query = {'name': 'frank'}
        result = tag.delete(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_delete_name_good: PASSED"
 
    # bad name, null results 
    def test_tag_delete_bad_name_null(self):
        query = {'name': 'FAILURE'}
        result = tag.delete(query)

        self.assertEqual(result, None)
        print "[API_tag] BB_test_tag_delete_bad_name_null: PASSED"
 
    # good name, failure due to existing mapping
    def test_tag_delete_name_mapping_failure(self):
        query = {'name': 'puppet'}

        self.assertRaises(TagError, tag.delete, query)
        print "[API_tag] BB_test_tag_delete_name_mapping_failure: PASSED (raised TagError)"
 

    ######################################
    # testing update()                   #
    ######################################

    # bad name, good security_level, failure 
    def test_tag_update_bad_name_good_security_failure(self):
        query = {'name': 'FAILURE', 'security_level': 1}

        self.assertRaises(TagError, tag.update, query)
        print "[API_tag] BB_test_tag_update_bad_name_good_security_failure: PASSED (raised TagError)"
 
    # name only, failure 
    def test_tag_update_name_only_failure(self):
        query = {'name': 'puppet'}

        self.assertRaises(TagError, tag.update, query)
        print "[API_tag] BB_test_tag_update_name_only_failure: PASSED (raised TagError)"

    # set everything. start_port > stop_port, failure
    def test_tag_update_start_gt_stop_failure(self):
        query = {'name': 'puppet', 'start_port': 90, 'stop_port': 70, 'security_level': 1}

        self.assertRaises(TagError, tag.update, query)
        print "[API_tag] BB_test_tag_update_start_gt_stop_failure: PASSED (raised TagError)"

    # set everything except stop_port. start_port > existing.stop_port (80), failure
    def test_tag_update_start_gt_existing_stop_failure(self):
        query = {'name': 'puppet', 'start_port': 90, 'security_level': 1}

        self.assertRaises(TagError, tag.update, query)
        print "[API_tag] BB_test_tag_update_start_gt_existing_stop_failure: PASSED (raised TagError)"

    # set everything except start_port. existing.start_port (80) > stop_port, failure
    def test_tag_update_existing_start_gt_stop_failure(self):
        query = {'name': 'puppet', 'stop_port': 70, 'security_level': 1}

        self.assertRaises(TagError, tag.update, query)
        print "[API_tag] BB_test_tag_update_existing_start_gt_stop_failure: PASSED (raised TagError)"

    # just name, start_port, good results 
    def test_tag_update_start_port_good(self):
        query = {'name': 'puppet', 'start_port': 70}
        result = tag.update(query)
        # put everything back where we found it
        query['start_port'] = 80
        tag.update(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_update_start_port_good: PASSED"

    # just name, stop_port, good results 
    def test_tag_update_stop_port_good(self):
        query = {'name': 'puppet', 'stop_port': 90}
        result = tag.update(query)
        # put everything back where we found it
        query['stop_port'] = 80
        tag.update(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_update_stop_port_good: PASSED"

    # just name, security_level, good results 
    def test_tag_update_security_level_good(self):
        query = {'name': 'puppet', 'security_level': 7}
        result = tag.update(query)
        # put everything back where we found it
        query['security_level'] = 1
        tag.update(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_update_security_level_good: PASSED"

    # everything, good results 
    def test_tag_update_everything_good(self):
        query = {'name': 'puppet', 'stop_port': 90, 'start_port': 70, 'security_level': 7}
        result = tag.update(query)
        # put everything back where we found it
        query = {'name': 'puppet', 'stop_port': 80, 'start_port': 80, 'security_level': 1}
        tag.update(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_update_everything_good: PASSED"
 

    ######################################
    # testing tag()                      #
    ######################################

    # name, unqdn=server.realm.site, good results
    def test_tag_tag_name_unqdn_is_server_realm_site_good(self):
        query = {'name': 'puppet', 'unqdn': 'cm1.satest.jfk'}
        result = tag.tag(query)
        # put everything back where we found it
        tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_tag_name_unqdn_is_server_realm_site_good: PASSED"
 
    # name, unqdn=realm.site, good results
    def test_tag_tag_name_unqdn_is_realm_site_good(self):
        query = {'name': 'puppet', 'unqdn': 'satest.jfk'}
        result = tag.tag(query)
        # put everything back where we found it
        tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_tag_name_unqdn_is_realm_site_good: PASSED"

    # name, unqdn=site, good results
    def test_tag_tag_name_unqdn_is_site_good(self):
        query = {'name': 'puppet', 'unqdn': 'jfk'}
        result = tag.tag(query)
        # put everything back where we found it
        tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_tag_name_unqdn_is_site_good: PASSED"

    # name, unqdn=GLOBAL, good results
    def test_tag_tag_name_unqdn_is_GLOBAL_good(self):
        query = {'name': 'puppet', 'unqdn': 'GLOBAL'}
        result = tag.tag(query)
        # put everything back where we found it
        tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_tag_name_unqdn_is_GLOBAL_good: PASSED"


    ######################################
    # testing untag()                    #
    ######################################

    # name, unqdn=server.realm.site, good results
    def test_tag_untag_name_unqdn_is_server_realm_site_good(self):
        query = {'name': 'puppet', 'unqdn': 'cm1.satest.jfk'}
        # setup
        tag.tag(query)
        result = tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_untag_name_unqdn_is_server_realm_site_good: PASSED"
 
    # name, unqdn=realm.site, good results
    def test_tag_untag_name_unqdn_is_realm_site_good(self):
        query = {'name': 'puppet', 'unqdn': 'satest.jfk'}
        # setup
        tag.tag(query)
        result = tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_untag_name_unqdn_is_realm_site_good: PASSED"

    # name, unqdn=site, good results
    def test_tag_untag_name_unqdn_is_site_good(self):
        query = {'name': 'puppet', 'unqdn': 'jfk'}
        # setup
        tag.tag(query)
        result = tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_tag_name_unqdn_is_site_good: PASSED"

    # name, unqdn=GLOBAL, good results
    def test_tag_untag_name_unqdn_is_GLOBAL_good(self):
        query = {'name': 'puppet', 'unqdn': 'GLOBAL'}
        # setup
        tag.tag(query)
        result = tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] BB_test_tag_untag_name_unqdn_is_GLOBAL_good: PASSED"

