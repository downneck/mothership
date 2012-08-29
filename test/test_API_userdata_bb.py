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

    # add everything except ssh key, success
    def test8(self):
        query = {'unqun': 'jiffyjeff.satest.jfk', 'first_name': 'jiffy', 'last_name': 'jeff', 'uid': 1337, 'user_type': 'employee', 'shell': '/bin/frank', 'email_address': 'jiffy@jeff.com', 'home_dir': '/fudge/jiffyjeff'}
        result = ud.uadd(query)
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        ud.udelete(query)
        self.assertEqual(result, 'success')
        print "[API_userdata] test8: PASSED"

    # add everything, success
    def test9(self):
        filedata = [open('test/ssh_pubkey_good')]
        query = {'unqun': 'jiffyjeff.satest.jfk', 'first_name': 'jiffy', 'last_name': 'jeff', 'uid': 1337, 'user_type': 'employee', 'shell': '/bin/frank', 'email_address': 'jiffy@jeff.com', 'home_dir': '/fudge/jiffyjeff'}
        result = ud.uadd(query, files=filedata)
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        ud.udelete(query)
        self.assertEqual(result, 'success')
        print "[API_userdata] test9: PASSED"

    # add everything, bad ssh_key, error raised
    def test10(self):
        filedata = [open('test/ssh_pubkey_bad')]
        query = {'unqun': 'jiffyjeff.satest.jfk', 'first_name': 'jiffy', 'last_name': 'jeff', 'uid': 1337, 'user_type': 'employee', 'shell': '/bin/frank', 'email_address': 'jiffy@jeff.com', 'home_dir': '/fudge/jiffyjeff'}
        self.assertRaises(UserdataError, ud.uadd, query, files=filedata)
        print "[API_userdata] test10: PASSED"

    # bad querykey, error raised
    def test11(self):
        query = {'unqun': 'jiffyjeff.satest.jfk', 'MEAT': 'MACHINE'}
        self.assertRaises(UserdataError, ud.uadd, query)
        print "[API_userdata] test11: PASSED"

    # uid too high (>65535, configured in mothership_daemon.yaml), error raised
    def test12(self):
        query = {'unqun': 'jiffyjeff.satest.jfk', 'uid': 65539}
        self.assertRaises(UserdataError, ud.uadd, query)
        print "[API_userdata] test12: PASSED"

    # uid too low (<500, configured in mothership_daemon.yaml), error raised
    def test13(self):
        query = {'unqun': 'jiffyjeff.satest.jfk', 'uid': 1}
        self.assertRaises(UserdataError, ud.uadd, query)
        print "[API_userdata] test13: PASSED"

    # bad username, little bobby tables, error raised.
    def test14(self):
        query = {'unqun': "Robert'); DROP TABLE Students;.satest.jfk"}
        self.assertRaises(UserdataError, ud.uadd, query)
        print "[API_userdata] test14: PASSED"

    # bad realm, error raised 
    def test15(self):
        query = {'unqun': 'jiffyjeff.badrealm.jfk'}
        self.assertRaises(UserdataError, ud.uadd, query)
        print "[API_userdata] test15: PASSED"

    # bad site_id, error raised 
    def test16(self):
        query = {'unqun': 'jiffyjeff.satest.badsite'}
        self.assertRaises(UserdataError, ud.uadd, query)
        print "[API_userdata] test16: PASSED"

    ######################################
    # testing udelete()                  #
    ######################################

    # basic delete, just username, success
    def test17(self):
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        ud.uadd(query)
        result = ud.udelete(query)
        self.assertEqual(result, 'success')
        print "[API_userdata] test17: PASSED"

    # nonexistent user, error raised 
    def test18(self):
        query = {'unqun': 'jiffyjeff.satest.badsite'}
        self.assertRaises(UserdataError, ud.udelete, query)
        print "[API_userdata] test18: PASSED"

