import unittest

from mothership.API_serverinfo import API_serverinfo
from mothership.configure import Configure

import mothership.kv
import mothership.validate
from mothership.mothership_models import *

from sqlalchemy import or_, desc, MetaData

class TestServerInfo(unittest.TestCase):
    def test_get_host_from_hwtag(self):
        cfg = Configure('mothership.yaml')
        si = API_serverinfo(cfg)
        result = si._get_host_from_hwtag('3Y29JQ1')

        s = si.cfg.dbsess.query(Server).\
            filter(Server.hw_tag=='3Y29JQ1').\
            filter(Server.virtual==False).first()
        if s.hostname:
            ret = si._get_serverinfo(s.hostname, s.realm, s.site_id)

        self.assertDictEqual(result, ret)

    def test_get_host_from_ip(self):
        cfg = Configure('mothership.yaml')
        si = API_serverinfo(cfg)
        result = si._get_host_from_ip('10.60.0.20')

        try:
            s, n = si.cfg.dbsess.query(Server, Network).\
                   filter(Server.id==Network.server_id).\
                   filter(Network.ip=='10.60.0.20').first()
            if s.hostname:
                ret = si._get_serverinfo(s.hostname, s.realm, s.site_id)
        except TypeError:
            pass
        # try the public ip
        try:
            s, n = si.cfg.dbsess.query(Server, Network).\
                   filter(Server.id==Network.server_id).\
                   filter(Network.public_ip=='10.60.0.20').first()
            if s.hostname:
                ret = si._get_serverinfo(s.hostname, s.realm, s.site_id)
        except TypeError:
            pass
        
        self.assertDictEqual(ret, result)
        
    def test_got_host_from_mac(self):
        cfg = Configure('mothership.yaml')
        si = API_serverinfo(cfg)
        result = si._get_host_from_mac('14:fe:b5:db:0a:58')

        h, s = cfg.dbsess.query(Network, Server).\
               filter(Network.hw_tag==Server.hw_tag).\
               filter(Network.mac=='14:fe:b5:db:0a:58').\
               filter(Server.virtual==False).first()
        if s.hostname:
            ret = si._get_serverinfo(s.hostname, s.realm, s.site_id)

        self.assertDictEqual(result, ret)

    def test_got_host_from_hostname(self):
        cfg = Configure('mothership.yaml')
        si = API_serverinfo(cfg)
        result = si._get_host_from_hostname('cm1')

        s = mothership.validate.v_get_host_obj(cfg, 'cm1')
        ret = si._get_serverinfo(s.hostname, s.realm, s.site_id)

        self.assertDictEqual(result, ret)
        
    def test_get_serverinfo(self):
        pass
