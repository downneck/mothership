import unittest

from mothership.API_userdata import * 
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
ud = API_userdata(cfg)
cfg.module_metadata['API_userdata'] = ud

# UnitTesting for API_userdata module
class TestAPI_userdata(unittest.TestCase):

    ######################################
    # testing udisplay()                 #
    ######################################

    # good input, good output
    def test1(self):
        query = {'unqun': 'bobsponge.satest.jfk'}
        result = ud.udisplay(query)
        # pre-define expected output
        ret = {
               'username': 'bobsponge',
               'hdir': '/home/bobsponge',
               'first_name': 'bob',
               'last_name': 'two',
               'realm': 'satest',
               'uid': 639,
               'site_id': 'jfk',
               'id': 175,
               'shell': '/bin/bash',
               'ssh_public_key': None,
               'active': True,
               'type': 'employee',
               'email': 'bobsponge@gilt.com' 
        }
        self.assertEqual(result, ret)
        print "[API_userdata] test1: PASSED"

    # bad username, error raised 
    def test2(self):
        query = {'unqdn': 'garbage.satest.jfk'}

        self.assertRaises(UserdataError, ud.udisplay, query)
        print "[API_userdata] test2: PASSED"

    # bad realm, error raised 
    def test3(self):
        query = {'unqdn': 'bobsponge.garbage.jfk'}
        self.assertRaises(UserdataError, ud.udisplay, query)
        print "[API_userdata] test3: PASSED"

    # bad site_id, error raised 
    def test4(self):
        query = {'unqdn': 'bobsponge.satest.garbage'}
        self.assertRaises(UserdataError, ud.udisplay, query)
        print "[API_userdata] test4: PASSED"

    # empty unqdn, error raised 
    def test5(self):
        query = {'unqdn': ''}
        self.assertRaises(UserdataError, ud.udisplay, query)
        print "[API_userdata] test5: PASSED"

    # invalid querykey, error raised 
    def test6(self):
        query = {'sizzle': 'steak'}
        self.assertRaises(UserdataError, ud.udisplay, query)
        print "[API_userdata] test6: PASSED"


    ######################################
    # testing uadd()                     #
    ######################################

    # basic add, just username, success
    def test7(self):
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        result = ud.uadd(query)
        ud.udelete(query)
        self.assertEqual(result, 'success')
        print "[API_userdata] test7: PASSED"

