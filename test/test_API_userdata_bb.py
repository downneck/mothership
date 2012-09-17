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

    # too few arguments, error
    def test48(self):
        query = {}
        self.assertRaises(UserdataError, ud.udisplay, query)
        print "[API_userdata] test47: PASSED"

    # too many arguments, error
    def test49(self):
        query = {'unqun': 'bobsponge.satest.jfk', 'count': 'chocula'}
        self.assertRaises(UserdataError, ud.udisplay, query)
        print "[API_userdata] test48: PASSED"

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

    # non-numeric uid, error raised
    def test62(self):
        query = {'unqun': 'jiffyjeff.satest.jfk', 'uid': 'fred'}
        self.assertRaises(UserdataError, ud.uadd, query)
        print "[API_userdata] test62: PASSED"

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

    # bad type, error raised 
    def test30(self):
        query = {'unqun': 'jiffyjeff.satest.badsite', 'user_type': 'garbage'}
        self.assertRaises(UserdataError, ud.uadd, query)
        print "[API_userdata] test30: PASSED"

    ######################################
    # testing udelete()                  #
    ######################################

    # basic delete, just username, success
    def test17(self):
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        ud.uadd(query)
        # now we need to remove the user from the default groups: web, users
        # otherwise udelete will raise an error
        ugquery = {'unqun': 'jiffyjeff.satest.jfk', 'groupname': 'web'}
        ud.urmg(query)
        ugquery['groupname'] = 'users'
        ud.urmg(query)
        result = ud.udelete(query)
        self.assertEqual(result, 'success')
        print "[API_userdata] test17: PASSED"

    # nonexistent user, error raised 
    def test18(self):
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        self.assertRaises(UserdataError, ud.udelete, query)
        print "[API_userdata] test18: PASSED"

    # bad querykey, error raised 
    def test19(self):
        query = {'unqun': 'bobsponge.satest.jfk', 'MEAT': 'MACHINE'}
        self.assertRaises(UserdataError, ud.udelete, query)
        print "[API_userdata] test19: PASSED"

    # bad realm, error raised 
    def test20(self):
        query = {'unqun': 'bobsponge.badrealm.jfk'}
        self.assertRaises(UserdataError, ud.udelete, query)
        print "[API_userdata] test20: PASSED"

    # bad site_id, error raised 
    def test21(self):
        query = {'unqun': 'bobsponge.satest.badsite'}
        self.assertRaises(UserdataError, ud.udelete, query)
        print "[API_userdata] test21: PASSED"

    # user still belongs to group(s), error
    def test79(self):
        query = {'unqun': 'dkovach.satest.jfk',}
        self.assertRaises(UserdataError, ud.udelete, query)
        print "[API_userdata] test79: PASSED"


    ######################################
    # testing umodify()                  #
    ######################################

    # modify everything, success
    def test22(self):
        query = {'unqun': 'jiffyjeff.satest.jfk', 'uid': 31336}
        ud.uadd(query)
        filedata = [open('test/ssh_pubkey_good')]
        query = {'unqun': 'jiffyjeff.satest.jfk', 'first_name': 'jiffy', 'last_name': 'jeff', 'uid': 31337, 'user_type': 'consultant', 'shell': '/bin/frank', 'email_address': 'jiffy@jeff.com', 'home_dir': '/fudge/jiffyjeff'}
        result = ud.umodify(query, files=filedata)
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        ud.udelete(query)
        self.assertEqual(result, 'success')
        print "[API_userdata] test22: PASSED"

    # nonexistent user, error raised 
    def test23(self):
        query = {'unqun': 'jiffyjeff.satest.jfk', 'uid': 31336}
        self.assertRaises(UserdataError, ud.umodify, query)
        print "[API_userdata] test23: PASSED"

    # bad querykey, error raised 
    def test24(self):
        query = {'unqun': 'bobsponge.satest.jfk', 'uid': 31337, 'MEAT': 'MACHINE'}
        self.assertRaises(UserdataError, ud.umodify, query)
        print "[API_userdata] test24: PASSED"

    # bad realm, error raised 
    def test25(self):
        query = {'unqun': 'bobsponge.badrealm.jfk', 'uid': 31337}
        self.assertRaises(UserdataError, ud.umodify, query)
        print "[API_userdata] test25: PASSED"

    # bad site_id, error raised 
    def test26(self):
        query = {'unqun': 'bobsponge.satest.badsite', 'uid': 31337}
        self.assertRaises(UserdataError, ud.umodify, query)
        print "[API_userdata] test26: PASSED"

    # bad ssh_key, error raised 
    def test27(self):
        query = {'unqun': 'jiffyjeff.satest.jfk', 'ssh_key': 'test/ssh_pubkey_bad'}
        ud.uadd(query)
        filedata = [open('test/ssh_pubkey_bad')]
        self.assertRaises(UserdataError, ud.umodify, query, files=filedata)
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        ud.udelete(query)
        print "[API_userdata] test27: PASSED"

    # uid too high (>65535, configured in mothership_daemon.yaml), error raised 
    def test28(self):
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        ud.uadd(query)
        query = {'unqun': 'jiffyjeff.satest.jfk', 'uid': 65539}
        self.assertRaises(UserdataError, ud.umodify, query)
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        ud.udelete(query)
        print "[API_userdata] test28: PASSED"

    # uid too low (<500, configured in mothership_daemon.yaml), error raised 
    def test29(self):
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        ud.uadd(query)
        query = {'unqun': 'jiffyjeff.satest.jfk', 'uid': 9}
        self.assertRaises(UserdataError, ud.umodify, query)
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        ud.udelete(query)
        print "[API_userdata] test29: PASSED"

    # uid too low (<500, configured in mothership_daemon.yaml), error raised 
    def test31(self):
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        ud.uadd(query)
        query = {'unqun': 'jiffyjeff.satest.jfk', 'uid': 9}
        self.assertRaises(UserdataError, ud.umodify, query)
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        ud.udelete(query)
        print "[API_userdata] test31: PASSED"

    # bad user_type, error raised 
    def test32(self):
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        ud.uadd(query)
        query = {'unqun': 'jiffyjeff.satest.jfk', 'user_type': 'jerk'}
        self.assertRaises(UserdataError, ud.umodify, query)
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        ud.udelete(query)
        print "[API_userdata] test32: PASSED"

    # deactivate user, success
    def test33(self):
        query = {'unqun': 'jiffyjeff.satest.jfk', 'uid': 31336}
        ud.uadd(query)
        query = {'unqun': 'jiffyjeff.satest.jfk', 'active': 'False'}
        result = ud.umodify(query)
        query = {'unqun': 'jiffyjeff.satest.jfk'}
        ud.udelete(query)
        self.assertEqual(result, 'success')
        print "[API_userdata] test33: PASSED"

    ######################################
    # testing uclone()                   #
    ######################################

    # basic clone, success
    def test34(self):
        query = {'unqun': 'bobsponge.satest.jfk', 'newunqn': 'qa.sfo'}
        result = ud.uclone(query)
        query = {'unqun': 'bobsponge.qa.sfo'}
        ud.udelete(query)
        self.assertEqual(result, 'success')
        print "[API_userdata] test34: PASSED"

    # nonexistent user, error raised
    def test35(self):
        query = {'unqun': 'jiffyjeff.satest.jfk', 'newunqn': 'qa.sfo'}
        self.assertRaises(UserdataError, ud.uclone, query)
        print "[API_userdata] test35: PASSED"

    # bad new realm, error raised
    def test36(self):
        query = {'unqun': 'bobsponge.satest.jfk', 'newunqn': 'badrealm.sfo'}
        self.assertRaises(UserdataError, ud.uclone, query)
        print "[API_userdata] test36: PASSED"

    # bad new site_id, error raised
    def test37(self):
        query = {'unqun': 'bobsponge.satest.jfk', 'newunqn': 'qa.badsite'}
        self.assertRaises(UserdataError, ud.uclone, query)
        print "[API_userdata] test37: PASSED"

    # bad querykey, error raised
    def test38(self):
        query = {'unqun': 'bobsponge.satest.jfk', 'MEAT': 'MACHINE'}
        self.assertRaises(UserdataError, ud.uclone, query)
        print "[API_userdata] test38: PASSED"

    # empty newunqn, error raised
    def test39(self):
        query = {'unqun': 'bobsponge.satest.jfk', 'newunqn': ''}
        self.assertRaises(UserdataError, ud.uclone, query)
        print "[API_userdata] test39: PASSED"

    # bad username, little bobby tables, error raised.
    def test40(self):
        query = {'unqun': "Robert'); DROP TABLE Students;.satest.jfk", 'newunqn': 'qa.sfo'}
        self.assertRaises(UserdataError, ud.uclone, query)
        print "[API_userdata] test40: PASSED"

    ######################
    # testing gdisplay() #
    ######################

    # good input, good output
    def test41(self):
        query = {'unqgn': 'test6_satest_jfk.satest.jfk'}
        result = ud.gdisplay(query)
        ret = {
               "realm": "satest",
               "description": "No description given",
               "site_id": "jfk",
               "sudo_cmds": None,
               "groupname": "test6_satest_jfk",
               "gid": 767,
               "id": 547
        }
        self.assertEqual(result, ret)
        print "[API_userdata] test41: PASSED"

    # bad username, error
    def test42(self):
        query = {'unqgn': 'garbage.satest.jfk'}
        self.assertRaises(UserdataError, ud.gdisplay, query)
        print "[API_userdata] test42: THE ANSWER TO LIFE, THE UNIVERSE, AND EVERYTHING (PASSED)."

    # bad realm, error
    def test43(self):
        query = {'unqgn': 'test6_satest_jfk.garbage.jfk'}
        self.assertRaises(UserdataError, ud.gdisplay, query)
        print "[API_userdata] test43: PASSED"

    # bad site_id, error
    def test44(self):
        query = {'unqgn': 'test6_satest_jfk.satest.fred'}
        self.assertRaises(UserdataError, ud.gdisplay, query)
        print "[API_userdata] test44: PASSED"

    # empty unqgn, error
    def test45(self):
        query = {'unqgn': ''}
        self.assertRaises(UserdataError, ud.gdisplay, query)
        print "[API_userdata] test45: PASSED"

    # invalid querykey, error
    def test46(self):
        query = {'sizzle': 'steak'}
        self.assertRaises(UserdataError, ud.gdisplay, query)
        print "[API_userdata] test46: PASSED"

    # too few arguments, error
    def test47(self):
        query = {}
        self.assertRaises(UserdataError, ud.gdisplay, query)
        print "[API_userdata] test47: PASSED"

    # too many arguments, error
    def test48(self):
        query = {'unqgn': 'test6_satest_jfk.satest.jfk', 'count': 'chocula'}
        self.assertRaises(UserdataError, ud.gdisplay, query)
        print "[API_userdata] test48: PASSED"

    ##################
    # testing gadd() #
    ##################

    # basic add, just groupname, success
    def test50(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk'}
        result = ud.gadd(query)
        ud.gdelete(query)
        self.assertEqual(result, 'success')
        print "[API_userdata] test50: PASSED"

    # add everything, success
    def test51(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk', 'gid': '8182', 'sudo_cmds': 'ls, cp', 'description': 'jiffy jeff! jeff! jeff! what? what? what?'}
        result = ud.gadd(query)
        query = {'unqgn': 'jiffyjeff.satest.jfk'}
        ud.gdelete(query)
        self.assertEqual(result, 'success')
        print "[API_userdata] test51: PASSED"

    # add everything with sudo_cmds translation ("All" -> "ALL"), success
    # for this we need to double check the entry using gdisplay
    def test52(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk', 'gid': '8182', 'sudo_cmds': 'All', 'description': 'jeff'}
        result = ud.gadd(query)
        self.assertEqual(result, 'success')
        query = {'unqgn': 'jiffyjeff.satest.jfk'}
        result = ud.gdisplay(query)
        # remove the index id, it's going to change every time this is run
        result['user'].pop("id")
        ret = {
               "user": {
                   "realm": "satest",
                   "description": "jeff",
                   "site_id": "jfk",
                   "sudo_cmds": "ALL",
                   "groupname": "jiffyjeff",
                   "gid": 8182,
               }
               "groups": [
                   {
                        'realm': 'satest',
                        "description": "No description given",
                        "site_id": "jfk",
                        "sudo_cmds": None,
                        "groupname": "users",
                        "gid": 401,
                        "id": 1
                   },
                   { 
                        "realm": "satest",
                        "description": "No description given",
                        "site_id": "jfk",
                        "sudo_cmds": None,
                        "groupname": "web",
                        "gid": 402,
                        "id": 2
                   },
               ]
        }
        ud.gdelete(query)
        self.assertEqual(result, ret)
        print "[API_userdata] test52: PASSED"

    # duplicate gid, error
    def test53(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk', 'gid': '767'}
        self.assertRaises(UserdataError, ud.gadd, query)
        print "[API_userdata] test53: PASSED"

    # non-numeric gid, error
    def test54(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk', 'gid': 'jeff'}
        self.assertRaises(UserdataError, ud.gadd, query)
        print "[API_userdata] test54: PASSED"

    # xlarge gid (>65535, configured in mothership_daemon.yaml), error
    def test55(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk', 'gid': 65539}
        self.assertRaises(UserdataError, ud.gadd, query)
        print "[API_userdata] test55: PASSED"

    # xsmall gid (<500, configured in mothership_daemon.yaml), error
    def test56(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk', 'gid': 1}
        self.assertRaises(UserdataError, ud.gadd, query)
        print "[API_userdata] test56: PASSED"

    # too few arguments, error
    def test57(self):
        query = {}
        self.assertRaises(UserdataError, ud.gadd, query)
        print "[API_userdata] test57: PASSED"

    # too many arguments, error
    def test58(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk', 'gid': '12345', 'description': 'jeff', 'sudo_cmds': 'ALL', 'count': 'chocula'}
        self.assertRaises(UserdataError, ud.gadd, query)
        print "[API_userdata] test58: PASSED"

    # duplicate name, error
    def test59(self):
        query = {'unqgn': 'test6_satest_jfk.satest.jfk',}
        self.assertRaises(UserdataError, ud.gadd, query)
        print "[API_userdata] test59: PASSED"

    # bad realm, error
    def test60(self):
        query = {'unqgn': 'jiffyjeff.fred.jfk',}
        self.assertRaises(UserdataError, ud.gadd, query)
        print "[API_userdata] test60: PASSED"

    # bad site_id, error
    def test61(self):
        query = {'unqgn': 'jiffyjeff.satest.fred',}
        self.assertRaises(UserdataError, ud.gadd, query)
        print "[API_userdata] test61: PASSED"

    # bad name, error
    def test63(self):
        query = {'unqgn': 'jiffy@jeff.satest.jfk',}
        self.assertRaises(UserdataError, ud.gadd, query)
        print "[API_userdata] test63: PASSED"

    #####################
    # testing gmodify() #
    #####################

    # mod everything, success
    def test64(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk'}
        ud.gadd(query)
        query = {'unqgn': 'jiffyjeff.satest.jfk', 'gid': '8182', 'sudo_cmds': 'ls, cp', 'description': 'jiffy jeff! jeff! jeff! what? what? what?'}
        result = ud.gmodify(query)
        query = {'unqgn': 'jiffyjeff.satest.jfk'}
        ud.gdelete(query)
        self.assertEqual(result, 'success')
        print "[API_userdata] test64: PASSED"

    # mod everything with sudo_cmds translation ("All" -> "ALL"), success
    # for this we need to double check the entry using gdisplay
    def test65(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk'}
        ud.gadd(query)
        query = {'unqgn': 'jiffyjeff.satest.jfk', 'gid': '8182', 'sudo_cmds': 'All', 'description': 'jeff'}
        result = ud.gmodify(query)
        self.assertEqual(result, 'success')
        query = {'unqgn': 'jiffyjeff.satest.jfk'}
        result = ud.gdisplay(query)
        # remove the index id, it's going to change every time this is run
        result['group'].pop("id")
        ret = {
               "group": {
                   "realm": "satest",
                   "description": "jeff",
                   "site_id": "jfk",
                   "sudo_cmds": "ALL",
                   "groupname": "jiffyjeff",
                   "gid": 8182,
               },
               'users': []
        }
        ud.gdelete(query)
        self.assertEqual(result, ret)
        print "[API_userdata] test65: PASSED"

    # duplicate gid, error
    def test66(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk'}
        ud.gadd(query)
        query = {'unqgn': 'jiffyjeff.satest.jfk', 'gid': '767'}
        self.assertRaises(UserdataError, ud.gmodify, query)
        query.pop('gid')
        ud.gdelete(query)
        print "[API_userdata] test66: PASSED"

    # non-numeric gid, error
    def test67(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk'}
        ud.gadd(query)
        query = {'unqgn': 'jiffyjeff.satest.jfk', 'gid': 'jeff'}
        self.assertRaises(UserdataError, ud.gmodify, query)
        query.pop('gid')
        ud.gdelete(query)
        print "[API_userdata] test67: PASSED"

    # xlarge gid (>65535, configured in mothership_daemon.yaml), error
    def test68(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk'}
        ud.gadd(query)
        query = {'unqgn': 'jiffyjeff.satest.jfk', 'gid': 65539}
        self.assertRaises(UserdataError, ud.gmodify, query)
        query.pop('gid')
        ud.gdelete(query)
        print "[API_userdata] test68: PASSED"

    # xsmall gid (<500, configured in mothership_daemon.yaml), error
    def test69(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk'}
        ud.gadd(query)
        query = {'unqgn': 'jiffyjeff.satest.jfk', 'gid': 1}
        self.assertRaises(UserdataError, ud.gmodify, query)
        query.pop('gid')
        ud.gdelete(query)
        print "[API_userdata] test69: PASSED"

    # too few arguments, error
    def test70(self):
        query = {}
        self.assertRaises(UserdataError, ud.gmodify, query)
        print "[API_userdata] test70: PASSED"

    # too many arguments, error
    def test71(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk'}
        ud.gadd(query)
        query = {'unqgn': 'jiffyjeff.satest.jfk', 'gid': '12345', 'description': 'jeff', 'sudo_cmds': 'ALL', 'count': 'chocula'}
        self.assertRaises(UserdataError, ud.gmodify, query)
        query = {'unqgn': 'jiffyjeff.satest.jfk'}
        ud.gdelete(query)
        print "[API_userdata] test71: PASSED"

    # bad realm, error
    def test72(self):
        query = {'unqgn': 'jiffyjeff.fred.jfk', 'gid': '6666'}
        self.assertRaises(UserdataError, ud.gmodify, query)
        print "[API_userdata] test72: PASSED"

    # bad site_id, error
    def test73(self):
        query = {'unqgn': 'jiffyjeff.satest.fred',}
        self.assertRaises(UserdataError, ud.gmodify, query)
        print "[API_userdata] test73: PASSED"

    #####################
    # testing gdelete() #
    #####################

    # delete, success
    def testr74(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk'}
        ud.gadd(query)
        result = ud.gdelete(query)
        self.assertEqual(result, 'success')
        print "[API_userdata] test74: PASSED"

    # too few arguments, error
    def test75(self):
        query = {}
        self.assertRaises(UserdataError, ud.gdelete, query)
        print "[API_userdata] test75: PASSED"

    # too many arguments, error
    def test76(self):
        query = {'unqgn': 'test6_satest_jfk.satest.jfk', 'gid': '12345', 'description': 'jeff', 'sudo_cmds': 'ALL', 'count': 'chocula'}
        self.assertRaises(UserdataError, ud.gdelete, query)
        print "[API_userdata] test76: PASSED"

    # bad realm, error
    def test77(self):
        query = {'unqgn': 'jiffyjeff.fred.jfk', 'gid': '6666'}
        self.assertRaises(UserdataError, ud.gdelete, query)
        print "[API_userdata] test77: PASSED"

    # bad site_id, error
    def test77(self):
        query = {'unqgn': 'jiffyjeff.satest.fred',}
        self.assertRaises(UserdataError, ud.gdelete, query)
        print "[API_userdata] test77: PASSED"

    # nonexistent group, error
    def test78(self):
        query = {'unqgn': 'jiffyjeff.satest.jfk',}
        self.assertRaises(UserdataError, ud.gdelete, query)
        print "[API_userdata] test78: PASSED"

    # group still has users, error
    def test80(self):
        query = {'unqgn': 'web.satest.jfk',}
        self.assertRaises(UserdataError, ud.gdelete, query)
        print "[API_userdata] test80: PASSED"

