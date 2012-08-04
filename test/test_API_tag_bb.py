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
    def test1(self):
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
        print "[API_tag] test1: PASSED"

    # name=puppet, bad output
    def test2(self):
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
        print "[API_tag] test2: PASSED"

    # name=FAILURE, null results 
    def test3(self):
        query = {'name': 'FAILURE'}

        self.assertRaises(TagError, tag.display, query)
        print "[API_tag] test3: PASSED"


    ######################################
    # testing add()                      #
    ######################################
 
    # test name=None, failure 
    def test4(self):
        query = {'name': None}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] test4: PASSED"
 
    # test name=foo, start_port=frank, failure 
    def test5(self):
        query = {'name': 'frank', 'start_port': 'frank'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] test5: PASSED"
 
    # test name=foo, stop_port=frank, failure 
    def test6(self):
        query = {'name': 'frank', 'stop_port': 'frank'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] test6: PASSED"
 
    # test name=foo, security_level=frank, failure 
    def test7(self):
        query = {'name': 'frank', 'security_level': 'frank'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] test7: PASSED"
 
    # test name=foo, start_port=80, stop_port=frank, failure 
    def test8(self):
        query = {'name': 'frank', 'start_port': 80, 'stop_port': 'frank'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] test8: PASSED"
 
    # test name=foo, stop_port=80, start_port=frank, failure 
    def test9(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 'frank'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] test9: PASSED"
 
    # everything good except security_level 
    def test10(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 80, 'security_level': 'fred'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] test10: PASSED"
 
    # everything good except start_port 
    def test11(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 'fred', 'security_level': 1}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] test11: PASSED"
 
    # everything good except stop_port 
    def test12(self):
        query = {'name': 'frank', 'stop_port': 'fred', 'start_port': 80, 'security_level': 1}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] test12: PASSED"
 
    # everything good, superfluous query, failure 
    def test13(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 80, 'security_level': 1, 'durr': 'stuff'}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] test13: PASSED"
 
    # everything good, good results 
    def test14(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 80, 'security_level': 1}
        result = tag.add(query)
        # put everything back where we found it
        tag.delete(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test14: PASSED"
 
    # just name, stop, start, good results 
    def test15(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 80}
        result = tag.add(query)
        # put everything back where we found it
        tag.delete(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test15: PASSED"
 
    # just name, stop, security_level, failure
    def test16(self):
        query = {'name': 'frank', 'stop_port': 80, 'security_level': 1}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] test16: PASSED"
 
    # just name, security, start, failure 
    def test17(self):
        query = {'name': 'frank', 'security_level': 1, 'start_port': 80}

        self.assertRaises(TagError, tag.add, query)
        print "[API_tag] test17: PASSED"
 
    # just name, good results 
    def test18(self):
        query = {'name': 'frank'}
        result = tag.add(query)
        # put everything back where we found it
        tag.delete(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test18: PASSED"
 
    # just name, security, good results 
    def test19(self):
        query = {'name': 'frank', 'security_level': 1}
        result = tag.add(query)
        # put everything back where we found it
        tag.delete(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test19: PASSED"
 

    ######################################
    # testing delete()                   #
    ######################################

    # just name, good results 
    def test20(self):
        query = {'name': 'frank', 'stop_port': 80, 'start_port': 80, 'security_level': 1}
        tag.add(query)
        query = {'name': 'frank'}
        result = tag.delete(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test20: PASSED"
 
    # bad name, null results 
    def test21(self):
        query = {'name': 'FAILURE'}

        self.assertRaises(TagError, tag.delete, query)
        print "[API_tag] test21: PASSED"
 
    # good name, failure due to existing mapping
    def test22(self):
        query = {'name': 'puppet'}

        self.assertRaises(TagError, tag.delete, query)
        print "[API_tag] test22: PASSED"
 

    ######################################
    # testing update()                   #
    ######################################

    # bad name, good security_level, failure 
    def test23(self):
        query = {'name': 'FAILURE', 'security_level': 1}

        self.assertRaises(TagError, tag.update, query)
        print "[API_tag] test23: PASSED"
 
    # name only, failure 
    def test24(self):
        query = {'name': 'puppet'}

        self.assertRaises(TagError, tag.update, query)
        print "[API_tag] test24: PASSED"

    # set everything. start_port > stop_port, failure
    def test25(self):
        query = {'name': 'puppet', 'start_port': 90, 'stop_port': 70, 'security_level': 1}

        self.assertRaises(TagError, tag.update, query)
        print "[API_tag] test25: PASSED"

    # set everything except stop_port. start_port > existing.stop_port (80), failure
    def test26(self):
        query = {'name': 'puppet', 'start_port': 90, 'security_level': 1}

        self.assertRaises(TagError, tag.update, query)
        print "[API_tag] test26: PASSED"

    # set everything except start_port. existing.start_port (80) > stop_port, failure
    def test27(self):
        query = {'name': 'puppet', 'stop_port': 70, 'security_level': 1}

        self.assertRaises(TagError, tag.update, query)
        print "[API_tag] test27: PASSED"

    # just name, start_port, good results 
    def test28(self):
        query = {'name': 'puppet', 'start_port': 70}
        result = tag.update(query)
        # put everything back where we found it
        query['start_port'] = 80
        tag.update(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test28: PASSED"

    # just name, stop_port, good results 
    def test29(self):
        query = {'name': 'puppet', 'stop_port': 90}
        result = tag.update(query)
        # put everything back where we found it
        query['stop_port'] = 80
        tag.update(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test29: PASSED"

    # just name, security_level, good results 
    def test30(self):
        query = {'name': 'puppet', 'security_level': 7}
        result = tag.update(query)
        # put everything back where we found it
        query['security_level'] = 1
        tag.update(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test30: PASSED"

    # everything, good results 
    def test31(self):
        query = {'name': 'puppet', 'stop_port': 90, 'start_port': 70, 'security_level': 7}
        result = tag.update(query)
        # put everything back where we found it
        query = {'name': 'puppet', 'stop_port': 80, 'start_port': 80, 'security_level': 1}
        tag.update(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test31: PASSED"
 

    ######################################
    # testing tag()                      #
    ######################################

    # name, unqdn=server.realm.site, good results
    def test32(self):
        query = {'name': 'puppet', 'unqdn': 'cm1.satest.jfk'}
        result = tag.tag(query)
        # put everything back where we found it
        tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test32: PASSED"
 
    # name, unqdn=realm.site, good results
    def test33(self):
        query = {'name': 'puppet', 'unqdn': 'satest.jfk'}
        result = tag.tag(query)
        # put everything back where we found it
        tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test33: PASSED"

    # name, unqdn=site, good results
    def test34(self):
        query = {'name': 'puppet', 'unqdn': 'jfk'}
        result = tag.tag(query)
        # put everything back where we found it
        tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test34: PASSED"

    # name, unqdn=GLOBAL, good results
    def test35(self):
        query = {'name': 'puppet', 'unqdn': 'GLOBAL'}
        result = tag.tag(query)
        # put everything back where we found it
        tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test35: PASSED"

    # name, hostname invalid, failure 
    def test36(self):
        query = {'name': 'puppet', 'unqdn': 'blarg1.satest.jfk'} 

        self.assertRaises(TagError, tag.tag, query)
        print "[API_tag] test36: PASSED"

    # name invalid, unqdn, failure 
    def test37(self):
        query = {'name': 'shreveport', 'unqdn': 'jira1.satest.jfk'} 

        self.assertRaises(TagError, tag.tag, query)
        print "[API_tag] test37: PASSED"

    # name, realm invalid, failure 
    def test38(self):
        query = {'name': 'puppet', 'unqdn': 'jira1.fubar.jfk'} 

        self.assertRaises(TagError, tag.tag, query)
        print "[API_tag] test38: PASSED"

    # name, site_id invalid, failure 
    def test39(self):
        query = {'name': 'puppet', 'unqdn': 'jira1.satest.foo'} 

        self.assertRaises(TagError, tag.tag, query)
        print "[API_tag] test39: PASSED"


    ######################################
    # testing untag()                    #
    ######################################

    # name, unqdn=server.realm.site, good results
    def test40(self):
        query = {'name': 'puppet', 'unqdn': 'cm1.satest.jfk'}
        # setup
        tag.tag(query)
        result = tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test40: PASSED"
 
    # name, unqdn=realm.site, good results
    def test41(self):
        query = {'name': 'puppet', 'unqdn': 'satest.jfk'}
        # setup
        tag.tag(query)
        result = tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test41: PASSED"

    # name, unqdn=site, good results
    def test42(self):
        query = {'name': 'puppet', 'unqdn': 'jfk'}
        # setup
        tag.tag(query)
        result = tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test42: THE ANSWER TO LIFE, THE UNIVERSE, AND EVERYTHING (PASSED)"

    # name, unqdn=GLOBAL, good results
    def test43(self):
        query = {'name': 'puppet', 'unqdn': 'GLOBAL'}
        # setup
        tag.tag(query)
        result = tag.untag(query)

        self.assertEqual(result, 'success')
        print "[API_tag] test43: PASSED"

    # name, hostname invalid, failure 
    def test44(self):
        query = {'name': 'puppet', 'unqdn': 'blarg1.satest.jfk'} 

        self.assertRaises(TagError, tag.untag, query)
        print "[API_tag] test44: PASSED"

    # name invalid, unqdn, failure 
    def test45(self):
        query = {'name': 'shreveport', 'unqdn': 'jira1.satest.jfk'} 

        self.assertRaises(TagError, tag.untag, query)
        print "[API_tag] test45: PASSED"

    # name, realm invalid, failure 
    def test46(self):
        query = {'name': 'puppet', 'unqdn': 'jira1.fubar.jfk'} 

        self.assertRaises(TagError, tag.untag, query)
        print "[API_tag] test47: PASSED"

    # name, site_id invalid, failure 
    def test47(self):
        query = {'name': 'puppet', 'unqdn': 'jira1.satest.foo'} 

        self.assertRaises(TagError, tag.untag, query)
        print "[API_tag] test47: PASSED"
