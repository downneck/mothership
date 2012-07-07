import unittest

from mothership.API_serverinfo import API_serverinfo
from mothership.API_kv import API_kv
from mothership.configure import *
import mothership.validate
from mothership.mothership_models import *
from mothership.common import *

from sqlalchemy import or_, desc, MetaData

# globals
# load up the config object
cfg = MothershipConfigureDaemon('mothership_daemon.yaml')
cfg.load_config()
# override logging parameters for testing
cfg.log_to_file = False
cfg.log_to_console = False
# instantiate a logger so the module we're testing doesn't freak out
cfg.log = MothershipLogger(cfg)
# instantiate the main class
si = API_serverinfo(cfg)
cfg.module_metadata['API_serverinfo'] = si
# needed to keep the KV from freaking out
cfg.module_metadata['API_kv'] = API_kv(cfg)

class TestAPI_serverinfo(unittest.TestCase):
    def test_get_host_from_hwtag(self):
        result = si._get_host_from_hwtag('4VK27L1')

        s = si.cfg.dbsess.query(Server).\
            filter(Server.hw_tag=='4VK27L1').\
            filter(Server.virtual==False).first()
        if s.hostname:
            ret = si._get_serverinfo(s.hostname, s.realm, s.site_id)

        self.assertEqual(result, ret)
        print "[API_serverinfo] WB_test_serverinfo_get_host_from_hwtag: PASSED"

    def test_get_host_from_ip(self):
        result = si._get_host_from_ip('10.190.44.52')

        try:
            s, n = si.cfg.dbsess.query(Server, Network).\
                   filter(Server.id==Network.server_id).\
                   filter(Network.ip=='10.190.44.52').first()
            if s.hostname:
                ret = si._get_serverinfo(s.hostname, s.realm, s.site_id)
        except TypeError:
            pass
        # try the public ip
        try:
            s, n = si.cfg.dbsess.query(Server, Network).\
                   filter(Server.id==Network.server_id).\
                   filter(Network.public_ip=='10.190.44.52').first()
            if s.hostname:
                ret = si._get_serverinfo(s.hostname, s.realm, s.site_id)
        except TypeError:
            pass
        
        self.assertEqual(ret, result)
        print "[API_serverinfo] WB_test_serverinfo_get_host_from_ip: PASSED"
        
    def test_got_host_from_mac(self):
        result = si._get_host_from_mac('00:21:9b:98:49:24')

        h, s = cfg.dbsess.query(Network, Server).\
               filter(Network.hw_tag==Server.hw_tag).\
               filter(Network.mac=='00:21:9b:98:49:24').\
               filter(Server.virtual==False).first()
        if s.hostname:
            ret = si._get_serverinfo(s.hostname, s.realm, s.site_id)

        self.assertEqual(result, ret)
        print "[API_serverinfo] WB_test_serverinfo_get_host_from_mac: PASSED"

    def test_got_host_from_hostname(self):
        result = si._get_host_from_hostname('cm1')

        s = mothership.validate.v_get_host_obj(cfg, 'cm1')
        ret = si._get_serverinfo(s.hostname, s.realm, s.site_id)

        self.assertEqual(result, ret)
        print "[API_serverinfo] WB_test_serverinfo_get_host_from_hostname: PASSED"
        
    def test_get_serverinfo(self):
        pass
