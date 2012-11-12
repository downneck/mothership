import unittest

from mothership.API_dns import * 
from mothership.API_kv import API_kv 
from mothership.configure import *
from mothership.common import *

import os
import filecmp

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
dns = API_dns(cfg)
cfg.module_metadata['API_dns'] = dns 
# needed to keep the KV from freaking out
cfg.module_metadata['API_kv'] = API_kv(cfg)

# large response to query to API_dns/display_forward?all
allforward = {"status": 0, "nodename": "localhost.localdomain", "timestamp": "2012-11-12 15:57:24.206737", "request": "/API_dns/display_forward", "msg": "", "data": [{"header": {"retry": "3600", "fqn": "satest.jfk.gilt.local", "refresh": "21600", "contact": "hostmaster.localhost.localdomain", "expire": "604800", "ttl": "86400", "serial": 1352753844, "ns": ["ns1.satest.jfk.gilt.local", "ns2.satest.jfk.gilt.local"]}, "records": [{"host": "ci1", "type": "A", "target": "10.190.44.150"}, {"host": "cm1", "type": "A", "target": "10.190.44.110"}, {"host": "cm2", "type": "A", "target": "10.190.44.99"}, {"host": "cobbler1", "type": "A", "target": "10.190.44.81"}, {"host": "dcmon1", "type": "A", "target": "10.190.44.97"}, {"host": "hudson1", "type": "A", "target": "10.190.44.95"}, {"host": "hudson2", "type": "A", "target": "10.190.44.96"}, {"host": "jira1", "type": "A", "target": "10.190.44.75"}, {"host": "ldap1", "type": "A", "target": "10.190.44.91"}, {"host": "ldap2", "type": "A", "target": "10.190.44.92"}, {"host": "matttest", "type": "A", "target": "90.90.90.90"}, {"host": "mtest3", "type": "A", "target": "10.190.44.102"}, {"host": "ns1", "type": "A", "target": "10.190.44.55"}, {"host": "ns2", "type": "A", "target": "10.190.44.93"}, {"host": "puppet", "type": "A", "target": "10.190.44.83"}, {"host": "rpmbuilder1", "type": "A", "target": "10.190.44.82"}, {"host": "solr12", "type": "A", "target": "10.190.44.124"}, {"host": "splunk1", "type": "A", "target": "10.190.44.54"}, {"host": "stage2", "type": "A", "target": "10.190.44.52"}, {"host": "stage7", "type": "A", "target": "10.190.44.57"}, {"host": "swaptest1", "type": "A", "target": "10.190.44.101"}, {"host": "swaptest2", "type": "A", "target": "10.190.44.100"}, {"host": "test2", "type": "A", "target": "10.190.44.122"}, {"host": "test5", "type": "A", "target": "10.190.44.123"}, {"host": "test6", "type": "A", "target": "10.190.44.127"}, {"host": "testeasyinstall", "type": "A", "target": "10.190.44.115"}, {"host": "teststore", "type": "A", "target": "10.190.44.103"}, {"host": "xenserver1", "type": "A", "target": "10.190.44.8"}, {"host": "xenserver2", "type": "A", "target": "10.190.44.9"}, {"host": "xenserver3", "type": "A", "target": "10.190.44.7"}, {"host": "zbx1", "type": "A", "target": "10.190.44.94"}, {"host": "zendc1", "type": "A", "target": "10.190.44.12"}, {"host": "zenoss1", "type": "A", "target": "10.190.44.53"}, {"host": "logstage1", "type": "CNAME", "target": "hudson1.satest.jfk.gilt.local"}, {"host": "yum", "type": "CNAME", "target": "cobbler1.satest.jfk.gilt.local"}, {"host": "cobbler1", "type": "SSHFP", "target": "1 1 6213841634CFF89C106A2160E50588A2DCF7AD25"}, {"host": "cobbler1", "type": "SSHFP", "target": "2 1 E664E950F1A9F8D4C9FBE9C93792561A91C3F48A"}, {"host": "jira1", "type": "SSHFP", "target": "1 1 CBBBF0B19EEE2C33BDF644D7A44020CBF668690F"}, {"host": "jira1", "type": "SSHFP", "target": "2 1 7186E6EDA1CDBC11D53C642F00AEFD12F264FD3C"}, {"host": "ldap1", "type": "SSHFP", "target": "1 1 03A227EF5AD744BED8141EE37714D8F0DB15FDDF"}, {"host": "ldap1", "type": "SSHFP", "target": "2 1 E6DDA41C1D057249ED60A0B0061A0ED303A54F82"}, {"host": "ldap2", "type": "SSHFP", "target": "1 1 7C0003BB9BAD374521E9B676A1188695B5F65304"}, {"host": "ldap2", "type": "SSHFP", "target": "2 1 B38657D04A074C987EABA0F1201246FDF32A2D83"}, {"host": "ns1", "type": "SSHFP", "target": "1 1 12293E656BD9DEFBC5FE61446FF7CB51DEEF2D95"}, {"host": "ns1", "type": "SSHFP", "target": "2 1 9B1B6D5A72EF82BD138D799F1F7105B4AA06AD76"}, {"host": "ns2", "type": "SSHFP", "target": "1 1 755283A22BCB2A171FE298296FC9AF75B0A13175"}, {"host": "ns2", "type": "SSHFP", "target": "2 1 6B1AF6FEBDDD04121B2313090A52D0F4549007F1"}, {"host": "rpmbuilder1", "type": "SSHFP", "target": "1 1 A4C8DEFD44F8251B936BF6CBAE7D5BD1C7F73D9A"}, {"host": "rpmbuilder1", "type": "SSHFP", "target": "2 1 7E70CCF9C73876E9CCEFE40D258584FBF92BE6F8"}, {"host": "xenserver1", "type": "SSHFP", "target": "1 1 6B5A8189D77C870C0881F623E9ED77BE1B20F8ED"}, {"host": "xenserver1", "type": "SSHFP", "target": "2 1 50163C97C4635D09ED8444F10F1D55901D6965F6"}, {"host": "xenserver2", "type": "SSHFP", "target": "1 1 4E7C922EA859127B697014D743EB3495BD29C19E"}, {"host": "xenserver2", "type": "SSHFP", "target": "2 1 4FF5B43C9AA52160C43C0BD6B5025F93E77B26C8"}, {"host": "xenserver3", "type": "SSHFP", "target": "1 1 4EA408C77F2F552DDAAD7979E3AE2E94378F7F86"}, {"host": "xenserver3", "type": "SSHFP", "target": "2 1 0DED0352089ED6332BC98E90B9E1B9258748057D"}]}, {"header": {"retry": "3600", "fqn": "mgmt.satest.jfk.gilt.local", "refresh": "21600", "contact": "hostmaster.localhost.localdomain", "expire": "604800", "ttl": "86400", "serial": 1352753844, "ns": ["ns1.satest.jfk.gilt.local", "ns2.satest.jfk.gilt.local"]}, "records": [{"host": "ci1", "type": "A", "target": "172.16.20.13"}, {"host": "cm1", "type": "A", "target": "172.16.20.56"}, {"host": "cm2", "type": "A", "target": "172.16.20.103"}, {"host": "cobbler1", "type": "A", "target": "172.16.20.81"}, {"host": "dcmon1", "type": "A", "target": "172.16.20.101"}, {"host": "hudson1", "type": "A", "target": "172.16.20.100"}, {"host": "hudson2", "type": "A", "target": "172.16.20.99"}, {"host": "jira1", "type": "A", "target": "172.16.20.106"}, {"host": "ldap1", "type": "A", "target": "172.16.20.91"}, {"host": "ldap2", "type": "A", "target": "172.16.20.92"}, {"host": "mtest3", "type": "A", "target": "172.16.20.105"}, {"host": "ns1", "type": "A", "target": "172.16.20.54"}, {"host": "ns2", "type": "A", "target": "172.16.20.95"}, {"host": "puppet", "type": "A", "target": "172.16.20.83"}, {"host": "rpmbuilder1", "type": "A", "target": "172.16.20.82"}, {"host": "solr12", "type": "A", "target": "172.16.20.115"}, {"host": "splunk1", "type": "A", "target": "172.16.20.55"}, {"host": "stage2", "type": "A", "target": "172.16.20.52"}, {"host": "stage7", "type": "A", "target": "172.16.20.57"}, {"host": "swaptest1", "type": "A", "target": "172.16.20.251"}, {"host": "swaptest2", "type": "A", "target": "172.16.20.252"}, {"host": "test2", "type": "A", "target": "172.16.20.114"}, {"host": "test5", "type": "A", "target": "172.16.20.107"}, {"host": "test6", "type": "A", "target": "172.16.20.116"}, {"host": "testeasyinstall", "type": "A", "target": "172.16.20.113"}, {"host": "teststore", "type": "A", "target": "172.16.20.104"}, {"host": "xenserver1", "type": "A", "target": "172.16.20.8"}, {"host": "xenserver2", "type": "A", "target": "172.16.20.9"}, {"host": "xenserver3", "type": "A", "target": "172.16.20.7"}, {"host": "zbx1", "type": "A", "target": "172.16.20.96"}, {"host": "zendc1", "type": "A", "target": "172.16.20.12"}, {"host": "zenoss1", "type": "A", "target": "172.16.20.53"}]}, {"header": {"retry": "3600", "fqn": "qa.jfk.gilt.local", "refresh": "21600", "contact": "hostmaster.localhost.localdomain", "expire": "604800", "ttl": "86400", "serial": 1352753844, "ns": ["ns1.qa.jfk.gilt.local", "ns2.qa.jfk.gilt.local"]}, "records": [{"host": "pug", "type": "A", "target": "192.168.10.8"}]}, {"header": {"retry": "3600", "fqn": "mgmt.qa.jfk.gilt.local", "refresh": "21600", "contact": "hostmaster.localhost.localdomain", "expire": "604800", "ttl": "86400", "serial": 1352753844, "ns": ["ns1.qa.jfk.gilt.local", "ns2.qa.jfk.gilt.local"]}, "records": []}, {"header": {"retry": "3600", "fqn": "satest.sfo.gilt.local", "refresh": "21600", "contact": "hostmaster.localhost.localdomain", "expire": "604800", "ttl": "86400", "serial": 1352753844, "ns": ["ns1.satest.sfo.gilt.local", "ns2.satest.sfo.gilt.local"]}, "records": []}, {"header": {"retry": "3600", "fqn": "mgmt.satest.sfo.gilt.local", "refresh": "21600", "contact": "hostmaster.localhost.localdomain", "expire": "604800", "ttl": "86400", "serial": 1352753844, "ns": ["ns1.satest.sfo.gilt.local", "ns2.satest.sfo.gilt.local"]}, "records": []}, {"header": {"retry": "3600", "fqn": "qa.sfo.gilt.local", "refresh": "21600", "contact": "hostmaster.localhost.localdomain", "expire": "604800", "ttl": "86400", "serial": 1352753844, "ns": ["ns1.qa.sfo.gilt.local", "ns2.qa.sfo.gilt.local"]}, "records": []}, {"header": {"retry": "3600", "fqn": "mgmt.qa.sfo.gilt.local", "refresh": "21600", "contact": "hostmaster.localhost.localdomain", "expire": "604800", "ttl": "86400", "serial": 1352753844, "ns": ["ns1.qa.sfo.gilt.local", "ns2.qa.sfo.gilt.local"]}, "records": []}]}

# large response to query to API_dns/display_reverse?all
allreverse = {"status": 0, "nodename": "localhost.localdomain", "timestamp": "2012-11-12 15:58:12.548936", "request": "/API_dns/display_reverse", "msg": "", "data": [{"header": {"retry": "3600", "fqn": "20.16.172.in-addr.arpa", "refresh": "21600", "contact": "hostmaster.localhost.localdomain", "expire": "604800", "ttl": "86400", "serial": 1352753892, "ns": ["ns1.satest.jfk.gilt.local", "ns2.satest.jfk.gilt.local"]}, "records": [{"host": "7", "type": "PTR", "target": "xenserver3.mgmt.satest.jfk.gilt.local."}, {"host": "8", "type": "PTR", "target": "xenserver1.mgmt.satest.jfk.gilt.local."}, {"host": "9", "type": "PTR", "target": "xenserver2.mgmt.satest.jfk.gilt.local."}, {"host": "12", "type": "PTR", "target": "zendc1.mgmt.satest.jfk.gilt.local."}, {"host": "13", "type": "PTR", "target": "ci1.mgmt.satest.jfk.gilt.local."}, {"host": "52", "type": "PTR", "target": "stage2.mgmt.satest.jfk.gilt.local."}, {"host": "53", "type": "PTR", "target": "zenoss1.mgmt.satest.jfk.gilt.local."}, {"host": "54", "type": "PTR", "target": "ns1.mgmt.satest.jfk.gilt.local."}, {"host": "55", "type": "PTR", "target": "splunk1.mgmt.satest.jfk.gilt.local."}, {"host": "56", "type": "PTR", "target": "cm1.mgmt.satest.jfk.gilt.local."}, {"host": "57", "type": "PTR", "target": "stage7.mgmt.satest.jfk.gilt.local."}, {"host": "81", "type": "PTR", "target": "cobbler1.mgmt.satest.jfk.gilt.local."}, {"host": "82", "type": "PTR", "target": "rpmbuilder1.mgmt.satest.jfk.gilt.local."}, {"host": "83", "type": "PTR", "target": "puppet.mgmt.satest.jfk.gilt.local."}, {"host": "91", "type": "PTR", "target": "ldap1.mgmt.satest.jfk.gilt.local."}, {"host": "92", "type": "PTR", "target": "ldap2.mgmt.satest.jfk.gilt.local."}, {"host": "95", "type": "PTR", "target": "ns2.mgmt.satest.jfk.gilt.local."}, {"host": "96", "type": "PTR", "target": "zbx1.mgmt.satest.jfk.gilt.local."}, {"host": "99", "type": "PTR", "target": "hudson2.mgmt.satest.jfk.gilt.local."}, {"host": "100", "type": "PTR", "target": "hudson1.mgmt.satest.jfk.gilt.local."}, {"host": "101", "type": "PTR", "target": "dcmon1.mgmt.satest.jfk.gilt.local."}, {"host": "103", "type": "PTR", "target": "cm2.mgmt.satest.jfk.gilt.local."}, {"host": "104", "type": "PTR", "target": "teststore.mgmt.satest.jfk.gilt.local."}, {"host": "105", "type": "PTR", "target": "mtest3.mgmt.satest.jfk.gilt.local."}, {"host": "106", "type": "PTR", "target": "jira1.mgmt.satest.jfk.gilt.local."}, {"host": "107", "type": "PTR", "target": "test5.mgmt.satest.jfk.gilt.local."}, {"host": "113", "type": "PTR", "target": "testeasyinstall.mgmt.satest.jfk.gilt.local."}, {"host": "114", "type": "PTR", "target": "test2.mgmt.satest.jfk.gilt.local."}, {"host": "115", "type": "PTR", "target": "solr12.mgmt.satest.jfk.gilt.local."}, {"host": "116", "type": "PTR", "target": "test6.mgmt.satest.jfk.gilt.local."}, {"host": "251", "type": "PTR", "target": "swaptest1.mgmt.satest.jfk.gilt.local."}, {"host": "252", "type": "PTR", "target": "swaptest2.mgmt.satest.jfk.gilt.local."}]}, {"header": {"retry": "3600", "fqn": "44.190.10.in-addr.arpa", "refresh": "21600", "contact": "hostmaster.localhost.localdomain", "expire": "604800", "ttl": "86400", "serial": 1352753892, "ns": ["ns1.satest.jfk.gilt.local", "ns2.satest.jfk.gilt.local"]}, "records": [{"host": "7", "type": "PTR", "target": "xenserver3.satest.jfk.gilt.local."}, {"host": "8", "type": "PTR", "target": "xenserver1.satest.jfk.gilt.local."}, {"host": "9", "type": "PTR", "target": "xenserver2.satest.jfk.gilt.local."}, {"host": "12", "type": "PTR", "target": "zendc1.satest.jfk.gilt.local."}, {"host": "52", "type": "PTR", "target": "stage2.satest.jfk.gilt.local."}, {"host": "53", "type": "PTR", "target": "zenoss1.satest.jfk.gilt.local."}, {"host": "54", "type": "PTR", "target": "splunk1.satest.jfk.gilt.local."}, {"host": "55", "type": "PTR", "target": "ns1.satest.jfk.gilt.local."}, {"host": "57", "type": "PTR", "target": "stage7.satest.jfk.gilt.local."}, {"host": "75", "type": "PTR", "target": "jira1.satest.jfk.gilt.local."}, {"host": "81", "type": "PTR", "target": "cobbler1.satest.jfk.gilt.local."}, {"host": "82", "type": "PTR", "target": "rpmbuilder1.satest.jfk.gilt.local."}, {"host": "83", "type": "PTR", "target": "puppet.satest.jfk.gilt.local."}, {"host": "91", "type": "PTR", "target": "ldap1.satest.jfk.gilt.local."}, {"host": "92", "type": "PTR", "target": "ldap2.satest.jfk.gilt.local."}, {"host": "93", "type": "PTR", "target": "ns2.satest.jfk.gilt.local."}, {"host": "94", "type": "PTR", "target": "zbx1.satest.jfk.gilt.local."}, {"host": "95", "type": "PTR", "target": "hudson1.satest.jfk.gilt.local."}, {"host": "96", "type": "PTR", "target": "hudson2.satest.jfk.gilt.local."}, {"host": "97", "type": "PTR", "target": "dcmon1.satest.jfk.gilt.local."}, {"host": "99", "type": "PTR", "target": "cm2.satest.jfk.gilt.local."}, {"host": "100", "type": "PTR", "target": "swaptest2.satest.jfk.gilt.local."}, {"host": "101", "type": "PTR", "target": "swaptest1.satest.jfk.gilt.local."}, {"host": "102", "type": "PTR", "target": "mtest3.satest.jfk.gilt.local."}, {"host": "103", "type": "PTR", "target": "teststore.satest.jfk.gilt.local."}, {"host": "110", "type": "PTR", "target": "cm1.satest.jfk.gilt.local."}, {"host": "115", "type": "PTR", "target": "testeasyinstall.satest.jfk.gilt.local."}, {"host": "122", "type": "PTR", "target": "test2.satest.jfk.gilt.local."}, {"host": "123", "type": "PTR", "target": "test5.satest.jfk.gilt.local."}, {"host": "124", "type": "PTR", "target": "solr12.satest.jfk.gilt.local."}, {"host": "127", "type": "PTR", "target": "test6.satest.jfk.gilt.local."}, {"host": "150", "type": "PTR", "target": "ci1.satest.jfk.gilt.local."}]}]}

# large response to query to API_dns/display_forward?uqun=satest.jfk
df_unqn_satest_jfk = {"status": 0, "nodename": "localhost.localdomain", "timestamp": "2012-11-12 16:00:42.725164", "request": "/API_dns/display_forward", "msg": "", "data": [{"header": {"retry": "3600", "fqn": "satest.jfk.gilt.local", "refresh": "21600", "contact": "hostmaster.localhost.localdomain", "expire": "604800", "ttl": "86400", "serial": 1352754042, "ns": ["ns1.satest.jfk.gilt.local", "ns2.satest.jfk.gilt.local"]}, "records": [{"host": "ci1", "type": "A", "target": "10.190.44.150"}, {"host": "cm1", "type": "A", "target": "10.190.44.110"}, {"host": "cm2", "type": "A", "target": "10.190.44.99"}, {"host": "cobbler1", "type": "A", "target": "10.190.44.81"}, {"host": "dcmon1", "type": "A", "target": "10.190.44.97"}, {"host": "hudson1", "type": "A", "target": "10.190.44.95"}, {"host": "hudson2", "type": "A", "target": "10.190.44.96"}, {"host": "jira1", "type": "A", "target": "10.190.44.75"}, {"host": "ldap1", "type": "A", "target": "10.190.44.91"}, {"host": "ldap2", "type": "A", "target": "10.190.44.92"}, {"host": "matttest", "type": "A", "target": "90.90.90.90"}, {"host": "mtest3", "type": "A", "target": "10.190.44.102"}, {"host": "ns1", "type": "A", "target": "10.190.44.55"}, {"host": "ns2", "type": "A", "target": "10.190.44.93"}, {"host": "puppet", "type": "A", "target": "10.190.44.83"}, {"host": "rpmbuilder1", "type": "A", "target": "10.190.44.82"}, {"host": "solr12", "type": "A", "target": "10.190.44.124"}, {"host": "splunk1", "type": "A", "target": "10.190.44.54"}, {"host": "stage2", "type": "A", "target": "10.190.44.52"}, {"host": "stage7", "type": "A", "target": "10.190.44.57"}, {"host": "swaptest1", "type": "A", "target": "10.190.44.101"}, {"host": "swaptest2", "type": "A", "target": "10.190.44.100"}, {"host": "test2", "type": "A", "target": "10.190.44.122"}, {"host": "test5", "type": "A", "target": "10.190.44.123"}, {"host": "test6", "type": "A", "target": "10.190.44.127"}, {"host": "testeasyinstall", "type": "A", "target": "10.190.44.115"}, {"host": "teststore", "type": "A", "target": "10.190.44.103"}, {"host": "xenserver1", "type": "A", "target": "10.190.44.8"}, {"host": "xenserver2", "type": "A", "target": "10.190.44.9"}, {"host": "xenserver3", "type": "A", "target": "10.190.44.7"}, {"host": "zbx1", "type": "A", "target": "10.190.44.94"}, {"host": "zendc1", "type": "A", "target": "10.190.44.12"}, {"host": "zenoss1", "type": "A", "target": "10.190.44.53"}, {"host": "logstage1", "type": "CNAME", "target": "hudson1.satest.jfk.gilt.local"}, {"host": "yum", "type": "CNAME", "target": "cobbler1.satest.jfk.gilt.local"}, {"host": "cobbler1", "type": "SSHFP", "target": "1 1 6213841634CFF89C106A2160E50588A2DCF7AD25"}, {"host": "cobbler1", "type": "SSHFP", "target": "2 1 E664E950F1A9F8D4C9FBE9C93792561A91C3F48A"}, {"host": "jira1", "type": "SSHFP", "target": "1 1 CBBBF0B19EEE2C33BDF644D7A44020CBF668690F"}, {"host": "jira1", "type": "SSHFP", "target": "2 1 7186E6EDA1CDBC11D53C642F00AEFD12F264FD3C"}, {"host": "ldap1", "type": "SSHFP", "target": "1 1 03A227EF5AD744BED8141EE37714D8F0DB15FDDF"}, {"host": "ldap1", "type": "SSHFP", "target": "2 1 E6DDA41C1D057249ED60A0B0061A0ED303A54F82"}, {"host": "ldap2", "type": "SSHFP", "target": "1 1 7C0003BB9BAD374521E9B676A1188695B5F65304"}, {"host": "ldap2", "type": "SSHFP", "target": "2 1 B38657D04A074C987EABA0F1201246FDF32A2D83"}, {"host": "ns1", "type": "SSHFP", "target": "1 1 12293E656BD9DEFBC5FE61446FF7CB51DEEF2D95"}, {"host": "ns1", "type": "SSHFP", "target": "2 1 9B1B6D5A72EF82BD138D799F1F7105B4AA06AD76"}, {"host": "ns2", "type": "SSHFP", "target": "1 1 755283A22BCB2A171FE298296FC9AF75B0A13175"}, {"host": "ns2", "type": "SSHFP", "target": "2 1 6B1AF6FEBDDD04121B2313090A52D0F4549007F1"}, {"host": "rpmbuilder1", "type": "SSHFP", "target": "1 1 A4C8DEFD44F8251B936BF6CBAE7D5BD1C7F73D9A"}, {"host": "rpmbuilder1", "type": "SSHFP", "target": "2 1 7E70CCF9C73876E9CCEFE40D258584FBF92BE6F8"}, {"host": "xenserver1", "type": "SSHFP", "target": "1 1 6B5A8189D77C870C0881F623E9ED77BE1B20F8ED"}, {"host": "xenserver1", "type": "SSHFP", "target": "2 1 50163C97C4635D09ED8444F10F1D55901D6965F6"}, {"host": "xenserver2", "type": "SSHFP", "target": "1 1 4E7C922EA859127B697014D743EB3495BD29C19E"}, {"host": "xenserver2", "type": "SSHFP", "target": "2 1 4FF5B43C9AA52160C43C0BD6B5025F93E77B26C8"}, {"host": "xenserver3", "type": "SSHFP", "target": "1 1 4EA408C77F2F552DDAAD7979E3AE2E94378F7F86"}, {"host": "xenserver3", "type": "SSHFP", "target": "2 1 0DED0352089ED6332BC98E90B9E1B9258748057D"}]}]}

# large response to query to API_dns/display_reverse?ip=10.190.44.0
dr_ip_10_190_44_0 = {"status": 0, "nodename": "localhost.localdomain", "timestamp": "2012-11-12 16:02:02.240208", "request": "/API_dns/display_reverse", "msg": "", "data": [{"header": {"retry": "3600", "fqn": "44.190.10.in-addr.arpa", "refresh": "21600", "contact": "hostmaster.localhost.localdomain", "expire": "604800", "ttl": "86400", "serial": 1352754122, "ns": ["ns1.satest.jfk.gilt.local", "ns2.satest.jfk.gilt.local"]}, "records": [{"host": "7", "type": "PTR", "target": "xenserver3.satest.jfk.gilt.local."}, {"host": "8", "type": "PTR", "target": "xenserver1.satest.jfk.gilt.local."}, {"host": "9", "type": "PTR", "target": "xenserver2.satest.jfk.gilt.local."}, {"host": "12", "type": "PTR", "target": "zendc1.satest.jfk.gilt.local."}, {"host": "52", "type": "PTR", "target": "stage2.satest.jfk.gilt.local."}, {"host": "53", "type": "PTR", "target": "zenoss1.satest.jfk.gilt.local."}, {"host": "54", "type": "PTR", "target": "splunk1.satest.jfk.gilt.local."}, {"host": "55", "type": "PTR", "target": "ns1.satest.jfk.gilt.local."}, {"host": "57", "type": "PTR", "target": "stage7.satest.jfk.gilt.local."}, {"host": "75", "type": "PTR", "target": "jira1.satest.jfk.gilt.local."}, {"host": "81", "type": "PTR", "target": "cobbler1.satest.jfk.gilt.local."}, {"host": "82", "type": "PTR", "target": "rpmbuilder1.satest.jfk.gilt.local."}, {"host": "83", "type": "PTR", "target": "puppet.satest.jfk.gilt.local."}, {"host": "91", "type": "PTR", "target": "ldap1.satest.jfk.gilt.local."}, {"host": "92", "type": "PTR", "target": "ldap2.satest.jfk.gilt.local."}, {"host": "93", "type": "PTR", "target": "ns2.satest.jfk.gilt.local."}, {"host": "94", "type": "PTR", "target": "zbx1.satest.jfk.gilt.local."}, {"host": "95", "type": "PTR", "target": "hudson1.satest.jfk.gilt.local."}, {"host": "96", "type": "PTR", "target": "hudson2.satest.jfk.gilt.local."}, {"host": "97", "type": "PTR", "target": "dcmon1.satest.jfk.gilt.local."}, {"host": "99", "type": "PTR", "target": "cm2.satest.jfk.gilt.local."}, {"host": "100", "type": "PTR", "target": "swaptest2.satest.jfk.gilt.local."}, {"host": "101", "type": "PTR", "target": "swaptest1.satest.jfk.gilt.local."}, {"host": "102", "type": "PTR", "target": "mtest3.satest.jfk.gilt.local."}, {"host": "103", "type": "PTR", "target": "teststore.satest.jfk.gilt.local."}, {"host": "110", "type": "PTR", "target": "cm1.satest.jfk.gilt.local."}, {"host": "115", "type": "PTR", "target": "testeasyinstall.satest.jfk.gilt.local."}, {"host": "122", "type": "PTR", "target": "test2.satest.jfk.gilt.local."}, {"host": "123", "type": "PTR", "target": "test5.satest.jfk.gilt.local."}, {"host": "124", "type": "PTR", "target": "solr12.satest.jfk.gilt.local."}, {"host": "127", "type": "PTR", "target": "test6.satest.jfk.gilt.local."}, {"host": "150", "type": "PTR", "target": "ci1.satest.jfk.gilt.local."}]}]}

# UnitTesting for API_dns
class TestAPI_dns(unittest.TestCase):

    ######################################
    # testing display_forward()          #
    ######################################

    # all=True, good output
    def test1(self):
        query = {'all': True}
        result = dns.display_forward(query)
        for i in result:
            del i['header']['serial']
        for i in allforward['data']:
            del i['header']['serial']
        self.assertEqual(result, allforward['data'])
        print "[API_dns] test1: PASSED"

    # test empty query, failure results
    def test2(self):
        query = {}
        self.assertRaises(DNSError, dns.display_forward, query)
        print "[API_dns] test2: PASSED"

    # unqn=satest.jfk, good output
    def test3(self):
        query = {'unqn': 'satest.jfk'}
        result = dns.display_forward(query)
        for i in result:
            del i['header']['serial']
        for i in df_unqn_satest_jfk['data']:
            del i['header']['serial']
        self.assertEqual(result, df_unqn_satest_jfk['data'])
        print "[API_dns] test3: PASSED"

    # test bad unqn, failure results
    def test4(self):
        query = {'unqn': 'laksjdf.garbage'}
        self.assertRaises(DNSError, dns.display_forward, query)
        print "[API_dns] test4: PASSED"

    ######################################
    # testing display_reverse()          #
    ######################################

    # all=True, good output
    def test5(self):
        query = {'all': True}
        result = dns.display_reverse(query)
        for i in result:
            del i['header']['serial']
        for i in allreverse['data']:
            del i['header']['serial']
        self.assertEqual(result, allreverse['data'])
        print "[API_dns] test5: PASSED"

    # test empty query, failure results
    def test6(self):
        query = {}
        self.assertRaises(DNSError, dns.display_reverse, query)
        print "[API_dns] test6: PASSED"

    # ip=10.190.44.0, good output
    def test7(self):
        query = {'ip': '10.190.44.0'}
        result = dns.display_reverse(query)
        for i in result:
            del i['header']['serial']
        for i in dr_ip_10_190_44_0['data']:
            del i['header']['serial']
        self.assertEqual(result, dr_ip_10_190_44_0['data'])
        print "[API_dns] test7: PASSED"

    # test bad ip, failure results
    def test8(self):
        query = {'ip': '10.190.44.400'}
        self.assertRaises(DNSError, dns.display_reverse, query)
        print "[API_dns] test8: PASSED"

    ######################################
    # testing write_forward()            #
    ######################################

    # all=True, good output
    def test9(self):
        cfg.zonedir = '/tmp/mothership_dns_temp'
        if os.path.isdir(cfg.zonedir):
            for file in os.listdir(cfg.zonedir):
                os.remove(cfg.zonedir+'/'+file)
            os.removedirs(cfg.zonedir)
        os.makedirs(cfg.zonedir)
        query = {'all': True}
        dns.write_forward(query)
        result = 0
        for file in os.listdir(cfg.zonedir):
            file1 = "%s/%s" % (cfg.zonedir, file)
            file2 = "test/dns_files/forward/%s" % file
            ftemp = open (file1, "r")
            linelist = ftemp.readlines()
            ftemp.close()
            del linelist[4]
            ftemp = open (file1, "w")
            ftemp.writelines(linelist)
            ftemp.close()
            if not filecmp.cmp(file1, file2):
                result += 1
        self.assertEqual(result, 0)
        print "[API_dns] test5: PASSED"

    # test empty query, failure results
    def test6(self):
        query = {}
        self.assertRaises(DNSError, dns.display_reverse, query)
        print "[API_dns] test6: PASSED"

    # ip=10.190.44.0, good output
    def test7(self):
        query = {'ip': '10.190.44.0'}
        result = dns.display_reverse(query)
        for i in result:
            del i['header']['serial']
        for i in dr_ip_10_190_44_0['data']:
            del i['header']['serial']
        self.assertEqual(result, dr_ip_10_190_44_0['data'])
        print "[API_dns] test7: PASSED"

    # test bad ip, failure results
    def test8(self):
        query = {'ip': '10.190.44.400'}
        self.assertRaises(DNSError, dns.display_reverse, query)
        print "[API_dns] test8: PASSED"

