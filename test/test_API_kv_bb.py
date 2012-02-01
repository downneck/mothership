import unittest

from mothership.API_kv import API_kv
from mothership.configure import *
import mothership.validate
from mothership.common import *

from sqlalchemy import or_, desc, MetaData

# UnitTesting for API_kv module
class TestAPI_kv(unittest.TestCase):

    # set up the test class to pass around
    def setUp(self):
        # the daemon config
        self.cfg = MothershipConfigureDaemon('mothership_daemon.yaml')
        self.cfg.load_config()
        # override logging settings for testing
        self.cfg.logfile = "mothership_bb_tests.log"
        self.cfg.log_to_file = True
        # fire up the logger
        self.cfg.log = MothershipLogger(self.cfg)
        # fire up the kv module and instantiate the class
        self.kv = API_kv(self.cfg)


    # good output
    def test_kv_select_any_good(self):
        query = {'any': True}
        result = self.kv.select(query)

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
        self.cfg.log.debug("****** test_kv_select_any_good: PASSED")

    # bad output
    def test_kv_select_any_bad(self):
        query = {'any': True}
        result = self.kv.select(query)

        # pre-define unexpected output
        ret = [{
               'realm': None,
               'hostname': None,
               'site_id': None,
               'value': 'FAILURE',
               'table_name': 'kv',
               'key': 'mc_secret',
               'id': 1
        },]

        self.assertNotEqual(result, ret)
        self.cfg.log.debug("****** test_kv_select_any_bad: PASSED")

    # test 'any' override ('any' option overrides all others)
    def test_kv_select_any_override(self):
        query = {'any': True, 'unqdn': 'stage2.satest.jfk', 'key': 'tag'}
        result = self.kv.select(query)

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
        self.cfg.log.debug("****** test_kv_select_any_override: PASSED")

    # test key=tag, good results
    def test_kv_select_key_tag_good(self):
        query = {'key': 'tag'}
        result = self.kv.select(query)

        # pre-define expected output
        ret = [{
               'realm': 'satest',
               'hostname': 'stage2',
               'site_id': 'jfk',
               'value': 'splunklightforwarder',
               'table_name': 'kv',
               'key': 'tag',
               'id': 38
        },]

        self.assertEqual(result, ret)
        self.cfg.log.debug("****** test_kv_select_key_tag_good: PASSED")

    # test key=tag, failure results
    def test_kv_select_key_tag_bad(self):
        query = {'key': 'tag'}
        result = self.kv.select(query)

        # pre-define expected output
        ret = [{
               'realm': 'satest',
               'hostname': 'stage2',
               'site_id': 'jfk',
               'value': 'FAILURE',
               'table_name': 'kv',
               'key': 'tag',
               'id': 38
        },]

        self.assertNotEqual(result, ret)
        self.cfg.log.debug("****** test_kv_select_key_tag_bad: PASSED")

    # test key=tag unqdn=decorati1.satest.jfk, good results
    def test_kv_select_key_tag_and_unqdn_good(self):
        query = {'key': 'tag', 'unqdn': 'decorati1.satest.jfk'}
        result = self.kv.select(query)

        # pre-define expected output
        ret = [{
               'realm': 'satest',
               'hostname': 'decorati1',
               'site_id': 'jfk',
               'value': 'apache',
               'table_name': 'kv',
               'key': 'tag',
               'id': 49
        },]

        self.assertEqual(result, ret)
        self.cfg.log.debug("****** test_kv_select_key_tag_and_unqdn_good: PASSED")

    # test key=tag unqdn=decorati1.satest.jfk, failure results
    def test_kv_select_key_tag_and_unqdn_bad(self):
        query = {'key': 'tag', 'unqdn': 'decorati1.satest.jfk'}
        result = self.kv.select(query)

        # pre-define expected output
        ret = [{
               'realm': 'satest',
               'hostname': 'decorati1',
               'site_id': 'jfk',
               'value': 'FAILURE',
               'table_name': 'kv',
               'key': 'tag',
               'id': 49
        },]

        self.assertNotEqual(result, ret)
        self.cfg.log.debug("****** test_kv_select_key_tag_and_unqdn_bad: PASSED")

    # test value=apache unqdn=decorati1.satest.jfk, good results
    def test_kv_select_unqdn_and_value_good(self):
        query = {'value': 'apache', 'unqdn': 'decorati1.satest.jfk'}
        result = self.kv.select(query)

        # pre-define expected output
        ret = [{
               'realm': 'satest',
               'hostname': 'decorati1',
               'site_id': 'jfk',
               'value': 'apache',
               'table_name': 'kv',
               'key': 'tag',
               'id': 49
        },]

        self.assertEqual(result, ret)
        self.cfg.log.debug("****** test_kv_select_unqdn_and_value_good: PASSED")

    # test value=apache unqdn=decorati1.satest.jfk, failure results
    def test_kv_select_unqdn_and_value_bad(self):
        query = {'value': 'apache', 'unqdn': 'decorati1.satest.jfk'}
        result = self.kv.select(query)

        # pre-define expected output
        ret = [{
               'realm': 'satest',
               'hostname': 'decorati1',
               'site_id': 'jfk',
               'value': 'FAILURE',
               'table_name': 'kv',
               'key': 'tag',
               'id': 49
        },]

        self.assertNotEqual(result, ret)
        self.cfg.log.debug("****** test_kv_select_unqdn_and_value_bad: PASSED")

    # test unqdn=decorati1.satest.jfk, good results
    def test_kv_select_unqdn_good(self):
        query = {'unqdn': 'decorati1.satest.jfk'}
        result = self.kv.select(query)

        # pre-define expected output
        ret = [{
               'realm': 'satest',
               'hostname': 'decorati1',
               'site_id': 'jfk',
               'value': 'apache',
               'table_name': 'kv',
               'key': 'tag',
               'id': 49
        },]

        self.assertEqual(result, ret)
        self.cfg.log.debug("****** test_kv_select_unqdn_good: PASSED")

    # test unqdn=decorati1.satest.jfk, failure results
    def test_kv_select_unqdn_bad(self):
        query = {'unqdn': 'decorati1.satest.jfk'}
        result = self.kv.select(query)

        # pre-define expected output
        ret = [{
               'realm': 'satest',
               'hostname': 'decorati1',
               'site_id': 'jfk',
               'value': 'FAILURE',
               'table_name': 'kv',
               'key': 'tag',
               'id': 49
        },]

        self.assertNotEqual(result, ret)
        self.cfg.log.debug("****** test_kv_select_unqdn_bad: PASSED")
