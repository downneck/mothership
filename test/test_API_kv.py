import unittest

from mothership.API_kv import API_kv
from mothership.configure import *
import mothership.validate
from mothership.common import *

from sqlalchemy import or_, desc, MetaData

# UnitTesting for API_kv module
class TestAPI_kv(unittest.TestCase):

    # good output
    def test_kv_select_any_good(self):
        cfg = MothershipConfigureDaemon('mothership_daemon.yaml')
        cfg.load_config()
        cfg.log = MothershipLogger(cfg) 
        kv = API_kv(cfg)
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

    # bad output
    def test_kv_select_any_bad(self):
        cfg = MothershipConfigureDaemon('mothership_daemon.yaml')
        cfg.load_config()
        cfg.log = MothershipLogger(cfg) 
        kv = API_kv(cfg)
        query = {'any': True}
        result = kv.select(query)

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

    # test 'any' override ('any' option overrides all others)
    def test_kv_select_any_override(self):
        cfg = MothershipConfigureDaemon('mothership_daemon.yaml')
        cfg.load_config()
        cfg.log = MothershipLogger(cfg) 
        kv = API_kv(cfg)
        query = {'any': True, 'unqdn': 'stage2.satest.jfk', 'key': 'tag'}
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
