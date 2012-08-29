import unittest

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
kv = API_kv(cfg)
cfg.module_metadata['API_kv'] = kv
# this thing is HUEG and i don't want this file to be 6 million lines so it's a global
longassret = [{"realm": None, "hostname": None, "site_id": None, "value": "359924B5-B1E4-468F-BD94-784FCD366BFA", "table_name": "kv", "key": "mc_secret", "id": 1}, {"realm": None, "hostname": None, "site_id": None, "value": "middleware", "table_name": "kv", "key": "mc_user", "id": 2}, {"realm": None, "hostname": None, "site_id": None, "value": "7AFAE79B-BFF1-4673-90DA-47A234CEC55B", "table_name": "kv", "key": "mc_userpass", "id": 3}, {"realm": None, "hostname": None, "site_id": None, "value": "satest", "table_name": "kv", "key": "environment", "id": 5}, {"realm": None, "hostname": None, "site_id": None, "value": "cobbler1", "table_name": "kv", "key": "mc_host", "id": 6}, {"realm": "test", "hostname": "cobbler1", "site_id": "jfk", "value": "meddleware", "table_name": "kv", "key": "mc_admin", "id": 8}, {"realm": "test", "hostname": "cobbler1", "site_id": "jfk", "value": "wheel", "table_name": "kv", "key": "groups", "id": 10}, {"realm": None, "hostname": None, "site_id": None, "value": "baseline", "table_name": "kv", "key": "class", "id": 11}, {"realm": None, "hostname": None, "site_id": None, "value": "zbx1", "table_name": "kv", "key": "zabbix_server", "id": 12}, {"realm": "satest", "hostname": "cobbler1", "site_id": "jfk", "value": "990DCAC9-65CC-4518-AA70-81CD153D1858", "table_name": "kv", "key": "mc_adminpass", "id": 14}, {"realm": "satest", "hostname": "cobbler1", "site_id": "jfk", "value": "meddleware", "table_name": "kv", "key": "mc_admin", "id": 15}, {"realm": None, "hostname": None, "site_id": None, "value": "/usr/libexec/openssh/ssh-ldap-helper.sh", "table_name": "kv", "key": "ssh_authorized_keys_command", "id": 19}, {"realm": None, "hostname": None, "site_id": None, "value": "nobody", "table_name": "kv", "key": "ssh_authorized_keys_command_run_as", "id": 20}, {"realm": "satest", "hostname": "ldap1", "site_id": "jfk", "value": "topsecret", "table_name": "kv", "key": "ldap_master_slapd_rootpw", "id": 21}, {"realm": "satest", "hostname": "ldap2", "site_id": "jfk", "value": "topsecret1", "table_name": "kv", "key": "ldap_slave_slapd_rootpw", "id": 22}, {"realm": "satest", "hostname": "ci1", "site_id": "jfk", "value": "ree::bundler_gem", "table_name": "kv", "key": "class", "id": 25}, {"realm": None, "hostname": None, "site_id": None, "value": "xenserver1.satest.jfk", "table_name": "kv", "key": "ntp_servers", "id": 26}, {"realm": None, "hostname": None, "site_id": None, "value": "xenserver2.satest.jfk", "table_name": "kv", "key": "ntp_servers", "id": 27}, {"realm": "satest", "hostname": "ldap1", "site_id": "jfk", "value": "root", "table_name": "kv", "key": "ldap_admin_cn", "id": 33}, {"realm": "satest", "hostname": "ldap1", "site_id": "jfk", "value": "topsecret", "table_name": "kv", "key": "ldap_admin_pass", "id": 34}, {"realm": None, "hostname": None, "site_id": None, "value": "172.16.20.81,10.190.44.55,10.190.44.93", "table_name": "kv", "key": "ns", "id": 101}, {"realm": None, "hostname": None, "site_id": None, "value": "10 relay1,20 relay2", "table_name": "kv", "key": "mx", "id": 103}, {"realm": None, "hostname": None, "site_id": None, "value": "sashimi911", "table_name": "kv", "key": "xen_api_pass", "id": 50}, {"realm": "satest", "hostname": "stage2", "site_id": "jfk", "value": "splunklightforwarder", "table_name": "kv", "key": "tag", "id": 38}, {"realm": "satest", "hostname": "cobbler1", "site_id": "jfk", "value": "splunklightforwarder", "table_name": "kv", "key": "tag", "id": 39}, {"realm": "satest", "hostname": "ns1", "site_id": "jfk", "value": "splunklightforwarder", "table_name": "kv", "key": "tag", "id": 40}, {"realm": "satest", "hostname": "ns2", "site_id": "jfk", "value": "splunklightforwarder", "table_name": "kv", "key": "tag", "id": 41}, {"realm": "satest", "hostname": "jira1", "site_id": "jfk", "value": "mysql", "table_name": "kv", "key": "tag", "id": 51}, {"realm": "satest", "hostname": "jira1", "site_id": "jfk", "value": "java", "table_name": "kv", "key": "tag", "id": 52}, {"realm": "satest", "hostname": "mtest1", "site_id": "jfk", "value": "postgres", "table_name": "kv", "key": "tag", "id": 53}, {"realm": "satest", "hostname": "mtest3", "site_id": "jfk", "value": "postgres", "table_name": "kv", "key": "tag", "id": 54}, {"realm": "satest", "hostname": "mtest3", "site_id": "jfk", "value": "jira", "table_name": "kv", "key": "tag", "id": 55}, {"realm": "satest", "hostname": "zbx1", "site_id": "jfk", "value": "test", "table_name": "kv", "key": "tag", "id": 57}, {"realm": "satest", "hostname": None, "site_id": "jfk", "value": "ldap1.satest.jfk.gilt.local", "table_name": "kv", "key": "ldap_master_server", "id": 71}, {"realm": "satest", "hostname": None, "site_id": "jfk", "value": "ldapsync", "table_name": "kv", "key": "ldap_sync_user", "id": 72}, {"realm": "satest", "hostname": None, "site_id": "jfk", "value": "aJLxA33Ng", "table_name": "kv", "key": "ldap_sync_pass", "id": 73}, {"realm": "prod", "hostname": None, "site_id": "jfk", "value": "ldap1.satest.jfk.gilt.local", "table_name": "kv", "key": "ldap_master_server", "id": 74}, {"realm": "prod", "hostname": None, "site_id": "jfk", "value": "ldapsync", "table_name": "kv", "key": "ldap_sync_user", "id": 75}, {"realm": "prod", "hostname": None, "site_id": "jfk", "value": "aJLxA33Ng", "table_name": "kv", "key": "ldap_sync_pass", "id": 76}, {"realm": "prod", "hostname": "cm1", "site_id": "iad", "value": "postgres", "table_name": "kv", "key": "tag", "id": 88}, {"realm": "satest", "hostname": "jira1", "site_id": "jfk", "value": "apache", "table_name": "kv", "key": "tag", "id": 358}]

# UnitTesting for API_kv module
class TestAPI_kv(unittest.TestCase):

    ######################################
    # testing select()                   #
    ######################################

    # any=True, good output
    def test1(self):
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
        print "[API_kv] test1: PASSED"

    # any=True, bad output
    def test2(self):
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
        print "[API_kv] test2: PASSED"

    # test 'any' override ('any' option overrides all others)
    def test3(self):
        query = {'any': True, 'unqdn': 'stage2.satest.jfk', 'key': 'tag', 'value': 'splunklightforwarder'}
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
        print "[API_kv] test3: PASSED"

    # test key=tag, good results
    def test4(self):
        query = {'key': 'tag'}
        result = kv.select(query)
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
        print "[API_kv] test4: PASSED"

    # test key=tag, failure results
    def test5(self):
        query = {'key': 'tag'}
        result = kv.select(query)
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
        print "[API_kv] test5: PASSED"

    # test key=tag unqdn=jira1.satest.jfk, good results
    def test6(self):
        query = {'key': 'tag', 'unqdn': 'jira1.satest.jfk'}
        result = kv.select(query)
        # pre-define expected output
        ret = [{
               'realm': 'satest',
               'hostname': 'jira1',
               'site_id': 'jfk',
               'value': 'mysql',
               'table_name': 'kv',
               'key': 'tag',
               'id': 51
        },]
        self.assertEqual(result, ret)
        print "[API_kv] test6: PASSED"

    # test key=tag unqdn=jira1.satest.jfk, failure results
    def test7(self):
        query = {'key': 'tag', 'unqdn': 'jira1.satest.jfk'}
        result = kv.select(query)
        # pre-define expected output
        ret = [{
               'realm': 'satest',
               'hostname': 'jira1',
               'site_id': 'jfk',
               'value': 'FAILURE',
               'table_name': 'kv',
               'key': 'tag',
               'id': 49
        },]
        self.assertNotEqual(result, ret)
        print "[API_kv] test7: PASSED"

    # test value=mysql unqdn=jira1.satest.jfk, good results
    def test8(self):
        query = {'value': 'mysql', 'unqdn': 'jira1.satest.jfk'}
        result = kv.select(query)
        # pre-define expected output
        ret = [{
               'realm': 'satest',
               'hostname': 'jira1',
               'site_id': 'jfk',
               'value': 'mysql',
               'table_name': 'kv',
               'key': 'tag',
               'id': 51
        },]
        self.assertEqual(result, ret)
        print "[API_kv] test8: PASSED"

    # test value=mysql unqdn=jira1.satest.jfk, failure results
    def test9(self):
        query = {'value': 'apache', 'unqdn': 'jira1.satest.jfk'}
        result = kv.select(query)
        # pre-define expected output
        ret = [{
               'realm': 'satest',
               'hostname': 'jira1',
               'site_id': 'jfk',
               'value': 'FAILURE',
               'table_name': 'kv',
               'key': 'tag',
               'id': 49
        },]
        self.assertNotEqual(result, ret)
        print "[API_kv] test9: PASSED"

    # test unqdn=jira1.satest.jfk, good results
    def test10(self):
        query = {'unqdn': 'jira1.satest.jfk'}
        result = kv.select(query)
        # pre-define expected output
        ret = [{
               'realm': 'satest',
               'hostname': 'jira1',
               'site_id': 'jfk',
               'value': 'mysql',
               'table_name': 'kv',
               'key': 'tag',
               'id': 51
        },]
        self.assertEqual(result, ret)
        print "[API_kv] test10: PASSED"

    # test unqdn=jira1.satest.jfk, failure results
    def test11(self):
        query = {'unqdn': 'jira1.satest.jfk'}
        result = kv.select(query)
        # pre-define expected output
        ret = [{
               'realm': 'satest',
               'hostname': 'jira1',
               'site_id': 'jfk',
               'value': 'FAILURE',
               'table_name': 'kv',
               'key': 'tag',
               'id': 49
        },]
        self.assertNotEqual(result, ret)
        print "[API_kv] test11: PASSED"

    # test empty query, failure results
    def test12(self):
        self.assertRaises(KVError, kv.select, query={})
        print "[API_kv] test12: PASSED"

    # test unqdn=garbage, failure results
    def test13(self):
        query = {'unqdn': 'garbage'}
        self.assertRaises(KVError, kv.select, query)
        print "[API_kv] test13: PASSED"

    # test unqdn=blahblahblah.satest.jfk, null results
    def test14(self):
        query = {'unqdn': 'blahblahblah.satest.jfk'}
        result = kv.select(query)
        self.assertEqual(result, None)
        print "[API_kv] test14: PASSED"

    # test key=blahblahblah, null results
    def test15(self):
        query = {'key': 'blahblahblah'}
        result = kv.select(query)
        self.assertEqual(result, None)
        print "[API_kv] test15: PASSED"

    # test value=blahblahblah, null results
    def test16(self):
        query = {'value': 'blahblahblah'}
        result = kv.select(query)
        self.assertEqual(result, None)
        print "[API_kv] test16: PASSED"

    
    ######################################
    # testing collect()                  #
    ######################################

    # test all=true, good results
    def test17(self):
        query = {'all': True}
        result = kv.collect(query)
        self.assertEqual(result, longassret)
        print "[API_kv] test17: PASSED"

    # test all=true override, good results
    def test18(self):
        query = {'all': True, 'unqdn': 'stage2.satest.jfk', 'key': 'tag', 'value': 'splunklightforwarder'}
        result = kv.collect(query)
        self.assertEqual(result, longassret)
        print "[API_kv] test18: PASSED"
 
    # test key=tag, value=mysql, good results
    def test19(self):
        query = {'key': 'tag', 'value': 'mysql'}
        result = kv.collect(query)
        ret = [{
               'realm': 'satest',
               'hostname': 'jira1',
	       'site_id': 'jfk',
	       'value': 'mysql',
	       'table_name': 'kv',
	       'key': 'tag',
	       'id': 51 
	}]
        self.assertEqual(result, ret)
        print "[API_kv] test19: PASSED" 

    # test key=tag, value=failure, failure results 
    def test20(self):
        query = {'key': 'tag', 'value': 'FAILURE'}
        result = kv.collect(query)
        self.assertEqual(result, [])
        print "[API_kv] test20: PASSED"
 
    # test key=tag, value=mysql unqdn=jira1.satest.jfk, good results
    def test21(self):
        query = {'key': 'tag', 'value': 'mysql', 'unqdn': 'jira1.satest.jfk'}
        result = kv.collect(query)
        ret = [{
               'realm': 'satest',
               'hostname': 'jira1',
	       'site_id': 'jfk',
	       'value': 'mysql',
	       'table_name': 'kv',
	       'key': 'tag',
	       'id': 51 
	}]
        self.assertEqual(result, ret)
        print "[API_kv] test21: PASSED" 

    # test key=tag, value=failure, unqdn=jira1.satest.jfk, failure results 
    def test22(self):
        query = {'key': 'tag', 'value': 'FAILURE', 'unqdn': 'jira1.satest.jfk'}
        result = kv.collect(query)
        self.assertEqual(result, [])
        print "[API_kv] test22: PASSED"

    ######################################
    # testing add()                      #
    ######################################
 
    # test unqdn=jira1.satest.jfk, failure results  
    def test23(self):
        query = {'unqdn': 'jira1.satest.jfk'}
        self.assertRaises(KVError, kv.add, query)
        print "[API_kv] test23: PASSED"
 
    # test unqdn=jira1.satest.jfk, key=tag, failure results  
    def test24(self):
        query = {'unqdn': 'jira1.satest.jfk', 'key': 'tag'}
        self.assertRaises(KVError, kv.add, query)
        print "[API_kv] test24: PASSED"
 
    # test unqdn=jira1.satest.jfk, key=tag, value='randomstringofcrap', good results  
    def test25(self):
        query = {'unqdn': 'jira1.satest.jfk', 'key': 'tag', 'value': 'randomstringofcrap'}
        result = kv.add(query)
        kv.delete(query) # clean up after ourselves
        self.assertEqual(result, 'success')
        print "[API_kv] test25: PASSED"

    # test unqdn=jira1.satest.jfk, key=tag, value='apache', failure results  
    def test26(self):
        query = {'unqdn': 'jira1.satest.jfk', 'key': 'tag', 'value': 'apache'}
        self.assertRaises(KVError, kv.add, query)
        print "[API_kv] test26: PASSED"

    ######################################
    # testing delete()                   #
    ######################################

    # test unqdn=jira1.satest.jfk, key=tag, value='randomstringofcrap', good results  
    def test27(self):
        query = {'unqdn': 'jira1.satest.jfk', 'key': 'tag', 'value': 'randomstringofcrap'}
        kv.add(query) # setup for the test
        result = kv.delete(query)
        self.assertEqual(result, 'success')
        print "[API_kv] test27: PASSED"

    # test unqdn=jira1.satest.jfk, key=tag, value='randomstringofcrap', failure results  
    def test28(self):
        query = {'unqdn': 'jira1.satest.jfk', 'key': 'tag', 'value': 'randomstringofcrap'}
        self.assertRaises(KVError, kv.delete, query)
        print "[API_kv] test28: PASSED"

    # test unqdn=jira1.satest.jfk, failure results 
    def test29(self):
        query = {'unqdn': 'jira1.satest.jfk'}
        self.assertRaises(KVError, kv.delete, query)
        print "[API_kv] test29: PASSED"

    ######################################
    # testing update()                   #
    ######################################

    # test unqdn=jira1.satest.jfk, key=tag, value='randomstringofcrap',
    # new_value=anotherrandomstringofcrap, good results  
    def test30(self):
        # set up for the test
        query = {'unqdn': 'jira1.satest.jfk', 'key': 'tag', 'value': 'randomstringofcrap'}
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
        print "[API_kv] test30: PASSED"

    # test unqdn=jira1.satest.jfk, key=tag, value='stringofcrap',
    # new_value=anotherrandomstringofcrap, good results  
    def test31(self):
        # set up for the test
        query = {'unqdn': 'jira1.satest.jfk', 'key': 'tag', 'value': 'randomstringofcrap'}
        # the test
        query['new_value'] = 'anotherrandomstringofcrap'
        self.assertRaises(KVError, kv.update, query)
        print "[API_kv] test31: PASSED"

