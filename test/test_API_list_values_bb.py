import unittest

from mothership.API_list_values import * 
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
lsv = API_list_values(cfg)


# UnitTesting for API_list_values module
class TestAPI_list_values(unittest.TestCase):

    ######################################
    # testing lsv()                      #
    ######################################

    # users=True, good output
    def test_lsv_users_good(self):
        query = {'users': True}
        result = lsv.lsv(query)

        # pre-define expected output
        ret = [
            "cpothier.satest.jfk uid:502 active",
            "kmcgregor.satest.jfk uid:503 active",
            "sfowler.satest.jfk uid:504 active",
            "pfumagalli.satest.jfk uid:506 active",
            "jenglert.satest.jfk uid:507 active",
            "skale.satest.jfk uid:509 active",
            "zmasaadeh.satest.jfk uid:510 active",
            "rtreat.satest.jfk uid:511 active",
            "nsawant.satest.jfk uid:512 active",
            "nyusaf.satest.jfk uid:513 active",
            "yon.satest.jfk uid:514 active",
            "geir.satest.jfk uid:515 active",
            "wfreund.satest.jfk uid:532 active",
            "flung.satest.jfk uid:650 active",
            "ysugawar.satest.jfk uid:517 active",
            "jsalama.satest.jfk uid:518 active",
            "jgoldberg.satest.jfk uid:520 active",
            "kcohen.satest.jfk uid:521 active",
            "davids.satest.jfk uid:522 active",
            "mwunsch.satest.jfk uid:523 active",
            "rnalam.satest.jfk uid:524 active",
            "vjebelev.satest.jfk uid:525 active",
            "hfleming.satest.jfk uid:526 active",
            "adecicco.satest.jfk uid:527 active",
            "msullan.satest.jfk uid:528 active",
            "fhelbig.satest.jfk uid:529 active",
            "jboyes.satest.jfk uid:530 active",
            "awong.satest.jfk uid:531 active",
            "msingleton.satest.jfk uid:534 active",
            "permchk.satest.jfk uid:535 active",
            "cjeu.satest.jfk uid:536 active",
            "hudaipurwala.satest.jfk uid:537 active",
            "jquinn.satest.jfk uid:557 active",
            "plim.satest.jfk uid:538 active",
            "ielbert.satest.jfk uid:539 active",
            "mhaddadin.satest.jfk uid:540 active",
            "ahammad.satest.jfk uid:541 active",
            "rpufky.satest.jfk uid:542 active",
            "hmeeran.satest.jfk uid:544 active",
            "elorenzo.satest.jfk uid:545 active",
            "lnguyen.satest.jfk uid:546 active",
            "rmurphy.satest.jfk uid:547 active",
            "cmaher.satest.jfk uid:548 active",
            "anu.satest.jfk uid:550 active",
            "echung.satest.jfk uid:551 active",
            "astraussner.satest.jfk uid:552 active",
            "akoch.satest.jfk uid:554 active",
            "iwaisman.satest.jfk uid:555 active",
            "cyokoyama.satest.jfk uid:556 active",
            "rmojica.satest.jfk uid:558 active",
            "sobrien.satest.jfk uid:559 active",
            "mrebosa.satest.jfk uid:560 active",
            "ssrivastava.satest.jfk uid:562 active",
            "sabdalla.satest.jfk uid:564 active",
            "ksaleh.satest.jfk uid:565 active",
            "dgharaibeh.satest.jfk uid:566 active",
            "hlubaczewski.satest.jfk uid:567 active",
            "dpatel.satest.jfk uid:568 active",
            "tschlossnagle.satest.jfk uid:569 active",
            "knorling.satest.jfk uid:570 active",
            "bballantine.satest.jfk uid:571 active",
            "ajaradat.satest.jfk uid:572 active",
            "sshinde.satest.jfk uid:573 active",
            "kdavis.satest.jfk uid:585 active",
            "carpops.satest.jfk uid:574 active",
            "pnguyen.satest.jfk uid:575 active",
            "dmerriman.satest.jfk uid:576 active",
            "rdeshpande.satest.jfk uid:577 active",
            "amanfredi.satest.jfk uid:579 active",
            "kscaldef.satest.jfk uid:580 active",
            "ssebastian.satest.jfk uid:582 active",
            "mdemanett.satest.jfk uid:584 active",
            "rradhakrishnan.satest.jfk uid:508 active",
            "apereira.satest.jfk uid:587 active",
            "msakata.satest.jfk uid:588 active",
            "cbethel.satest.jfk uid:589 active",
            "bwong.satest.jfk uid:590 active",
            "szaluk.satest.jfk uid:591 active",
            "khaggard.satest.jfk uid:592 active",
            "manderson.satest.jfk uid:594 active",
            "sjacobs.satest.jfk uid:595 active",
            "wsmith.satest.jfk uid:596 active",
            "jsanchez.satest.jfk uid:597 active",
            "ayampolskiy.satest.jfk uid:598 active",
            "cjordan.satest.jfk uid:599 active",
            "plosco.satest.jfk uid:601 active",
            "tcheung.satest.jfk uid:602 active",
            "skassoumeh.satest.jfk uid:603 active",
            "chazlett.satest.jfk uid:605 active",
            "mramakrishnan.satest.jfk uid:606 active",
            "dzucker.satest.jfk uid:607 active",
            "khyland.satest.jfk uid:621 active",
            "jbrothers.satest.jfk uid:609 active",
            "jlee.satest.jfk uid:610 active",
            "evalqui.satest.jfk uid:611 active",
            "eshepherd.satest.jfk uid:612 active",
            "emaloney.satest.jfk uid:613 active",
            "jbaxter.satest.jfk uid:615 active",
            "mkumits.satest.jfk uid:616 active",
            "bdhatt.satest.jfk uid:617 active",
            "echu.satest.jfk uid:618 active",
            "rcaliolo.satest.jfk uid:619 active",
            "jhuntington.satest.jfk uid:620 active",
            "ckroll.satest.jfk uid:622 active",
            "ahoang.qa.jfk uid:581 active",
            "tpayne.satest.jfk uid:623 active",
            "qauser.satest.jfk uid:625 active",
            "dhofmann.satest.jfk uid:624 active",
            "klee.satest.jfk uid:604 active",
            "klee.prod.jfk uid:604 active",
            "akurkin.satest.jfk uid:614 active",
            "ajha.satest.jfk uid:500 active",
            "akartashov.satest.jfk uid:501 active",
            "atatla.satest.jfk uid:505 active",
            "wmetcalfe.satest.jfk uid:516 active",
            "rlivingston.satest.jfk uid:519 active",
            "tatlas.satest.jfk uid:533 active",
            "mbryzek.satest.jfk uid:543 active",
            "lribando.satest.jfk uid:549 active",
            "nvenkateswaran.satest.jfk uid:553 active",
            "ldapsync.satest.jfk uid:626 active",
            "musigma.satest.jfk uid:561 active",
            "sbailliez.satest.jfk uid:563 active",
            "amuntean.satest.jfk uid:583 active",
            "dkovach.satest.jfk uid:586 active",
            "mnutt.satest.jfk uid:593 active",
            "gguerdat.satest.jfk uid:600 active",
            "tgruzbarg.satest.jfk uid:608 active",
            "ahoang.satest.jfk uid:581 active",
            "dkovach.prod.jfk uid:586 active",
            "xenprovision.satest.jfk uid:627 active",
            "vbhagwat.satest.jfk uid:628 active",
            "gerrit.satest.jfk uid:578 active",
            "cpower.satest.jfk uid:741 active",
            "mosterhaus.satest.jfk uid:647 active",
            "mtest.satest.jfk uid:629 active",
            "mtest88.satest.jfk uid:630 active",
            "motest.satest.jfk uid:631 active",
            "mytest.satest.jfk uid:632 active",
            "mclovin.satest.jfk uid:633 active",
            "bob1.satest.jfk uid:634 active",
            "bob2.satest.jfk uid:635 active",
            "motester.satest.jfk uid:636 active",
            "matttest2.satest.jfk uid:637 active",
            "matttest3.satest.jfk uid:638 active",
            "bobsponge.satest.jfk uid:639 active",
            "hurricane.satest.jfk uid:640 active",
            "ssmith.satest.jfk uid:641 active"
        ]

        self.assertEqual(result, ret)
        print "[API_list_values] test_lsv_users_good: PASSED"

    # users=True tags=True, bad output
    def test_lsv_users_and_tags_bad(self):
        query = {'users': True, 'tags': True}

        self.assertRaises(ListValuesError, lsv.lsv, query)
        print "[API_list_values] test_lsv_users_and_tags_bad: PASSED (raised ListValuesError)"

    # tags=True, good output
    def test_lsv_tags_good(self):
        query = {'tags': True}
        result = lsv.lsv(query)

        ret = [
            "adhoc",
            "app",
            "authsvc",
            "backup",
            "bbiphone",
            "bb",
            "bosedgelb",
            "build",
            "cache",
            "cartsvc",
            "cms",
            "contint",
            "cs",
            "datasvc",
            "db",
            "dbutil",
            "deploy",
            "dns",
            "esp",
            "etl",
            "expdb",
            "falconcity",
            "falcon",
            "finance",
            "gblscms",
            "gem",
            "glx",
            "gold",
            "ids",
            "inv",
            "job",
            "jsetapi",
            "kvcart",
            "kvoo",
            "kvreginfo",
            "kvso",
            "lb",
            "ldap",
            "listserv",
            "login",
            "misc",
            "mon",
            "mothership",
            "nas",
            "oakedgelb",
            "originlb",
            "pagegen",
            "paysvc",
            "pm",
            "qalb",
            "qauser",
            "rep",
            "scms",
            "smtp",
            "solr",
            "spare",
            "spdf",
            "splunk",
            "stage",
            "stc",
            "svclb",
            "swift",
            "test",
            "usersvc",
            "util",
            "vertexapp",
            "vertexdb",
            "vertexqaapp",
            "vertexqadb",
            "waitlistsvc",
            "zendc",
            "zenoss",
            "database",
            "zabbix_db",
            "loghost",
            "log",
            "zabbix_server",
            "pweb",
            "weba",
            "bastion",
            "mta",
            "relay",
            "zenossdb",
            "hudson",
            "xen",
            "mysql",
            "apache",
            "dcmon",
            "jira",
            "postgres",
            "swappy"
        ]

        self.assertEqual(result, ret)
        print "[API_list_values] test_lsv_tags_good: PASSED"

    # ips=True, good output
    def test_lsv_ips_good(self):
        query = {'ips': True}
        result = lsv.lsv(query)

        ret = [
            "10.190.33.75",
            "10.190.33.150",
            "10.190.44.7",
            "10.190.44.8",
            "10.190.44.9",
            "10.190.44.12",
            "10.190.44.52",
            "10.190.44.53",
            "10.190.44.54",
            "10.190.44.55",
            "10.190.44.57",
            "10.190.44.81",
            "10.190.44.82",
            "10.190.44.83",
            "10.190.44.91",
            "10.190.44.92",
            "10.190.44.93",
            "10.190.44.94",
            "10.190.44.95",
            "10.190.44.96",
            "10.190.44.97",
            "10.190.44.99",
            "10.190.44.100",
            "10.190.44.101",
            "10.190.44.102",
            "10.190.44.103",
            "10.190.44.110",
            "10.190.44.115",
            "10.190.44.122",
            "10.190.44.123",
            "10.190.44.124",
            "10.190.44.127",
            "10.190.44.128",
            "172.16.20.7",
            "172.16.20.8",
            "172.16.20.9",
            "172.16.20.11",
            "172.16.20.12",
            "172.16.20.13",
            "172.16.20.52",
            "172.16.20.53",
            "172.16.20.54",
            "172.16.20.55",
            "172.16.20.56",
            "172.16.20.57",
            "172.16.20.81",
            "172.16.20.82",
            "172.16.20.83",
            "172.16.20.91",
            "172.16.20.92",
            "172.16.20.95",
            "172.16.20.96",
            "172.16.20.99",
            "172.16.20.100",
            "172.16.20.101",
            "172.16.20.103",
            "172.16.20.104",
            "172.16.20.105",
            "172.16.20.106",
            "172.16.20.107",
            "172.16.20.111",
            "172.16.20.113",
            "172.16.20.114",
            "172.16.20.115",
            "172.16.20.116",
            "172.16.20.117",
            "172.16.20.251",
            "172.16.20.252"
        ]

        self.assertEqual(result, ret)
        print "[API_list_values] test_lsv_ips_good: PASSED"

    # groups=True, good output
    def test_lsv_groups_good(self):
        query = {'groups': True}
        result = lsv.lsv(query)

        ret = [
            "cognos.satest.jfk gid:3005",
            "data.satest.jfk gid:3008",
            "dbadmin.satest.jfk gid:2501",
            "dwuser.satest.jfk gid:3002",
            "emailpers.satest.jfk gid:3007",
            "fcpigeon.satest.jfk gid:3051",
            "giltread.satest.jfk gid:5001",
            "hadoop.satest.jfk gid:3001",
            "iphone.satest.jfk gid:403",
            "kettleuser_dev.satest.jfk gid:3003",
            "kettleuser_preprod.satest.jfk gid:3004",
            "msgsys.satest.jfk gid:1002",
            "puppet.satest.jfk gid:52",
            "spotfire.satest.jfk gid:3006",
            "zabbix.satest.jfk gid:142",
            "zenoss.satest.jfk gid:143",
            "zeus.satest.jfk gid:1001",
            "adhoc.satest.jfk gid:15000",
            "app.satest.jfk gid:15001",
            "authsvc.satest.jfk gid:15002",
            "backup.satest.jfk gid:15003",
            "bbiphone.satest.jfk gid:15004",
            "bb.satest.jfk gid:15005",
            "bosedgelb.satest.jfk gid:15006",
            "build.satest.jfk gid:15007",
            "cache.satest.jfk gid:15008",
            "cartsvc.satest.jfk gid:15009",
            "cms.satest.jfk gid:15010",
            "contint.satest.jfk gid:15011",
            "cs.satest.jfk gid:15012",
            "datasvc.satest.jfk gid:15013",
            "dbutil.satest.jfk gid:15014",
            "deploy.satest.jfk gid:15015",
            "dns.satest.jfk gid:15016",
            "esp.satest.jfk gid:15017",
            "etl.satest.jfk gid:15018",
            "expdb.satest.jfk gid:15019",
            "falconcity.satest.jfk gid:15020",
            "falcon.satest.jfk gid:15021",
            "finance.satest.jfk gid:15022",
            "gblscms.satest.jfk gid:15023",
            "gem.satest.jfk gid:15024",
            "glx.satest.jfk gid:15025",
            "gold.satest.jfk gid:15026",
            "ids.satest.jfk gid:15027",
            "inv.satest.jfk gid:15028",
            "job.satest.jfk gid:15029",
            "jsetapi.satest.jfk gid:15030",
            "kvcart.satest.jfk gid:15031",
            "kvoo.satest.jfk gid:15032",
            "kvreginfo.satest.jfk gid:15033",
            "kvso.satest.jfk gid:15034",
            "lb.satest.jfk gid:15035",
            "ldap.satest.jfk gid:15036",
            "listserv.satest.jfk gid:15037",
            "misc.satest.jfk gid:15038",
            "mon.satest.jfk gid:15039",
            "mothership.satest.jfk gid:15040",
            "oakedgelb.satest.jfk gid:15041",
            "originlb.satest.jfk gid:15042",
            "pagegen.satest.jfk gid:15043",
            "paysvc.satest.jfk gid:15044",
            "pm.satest.jfk gid:15045",
            "qalb.satest.jfk gid:15046",
            "qauser.satest.jfk gid:15047",
            "rep.satest.jfk gid:15048",
            "scms.satest.jfk gid:15049",
            "smtp.satest.jfk gid:15050",
            "solr.satest.jfk gid:15051",
            "spare.satest.jfk gid:15052",
            "web.satest.jfk gid:402",
            "users.satest.jfk gid:401",
            "splunk.satest.jfk gid:15054",
            "stc.satest.jfk gid:15056",
            "svclb.satest.jfk gid:15057",
            "swift.satest.jfk gid:15058",
            "test.satest.jfk gid:15059",
            "usersvc.satest.jfk gid:15060",
            "util.satest.jfk gid:15061",
            "vertexapp.satest.jfk gid:15062",
            "vertexdb.satest.jfk gid:15063",
            "vertexqaapp.satest.jfk gid:15064",
            "vertexqadb.satest.jfk gid:15065",
            "waitlistsvc.satest.jfk gid:15066",
            "zendc.satest.jfk gid:15067",
            "zabbix_db.satest.jfk gid:15068",
            "loghost.satest.jfk gid:15069",
            "log.satest.jfk gid:15070",
            "zabbix_server.satest.jfk gid:15071",
            "pweb.satest.jfk gid:15072",
            "weba.satest.jfk gid:15073",
            "bastion.satest.jfk gid:15074",
            "mta.satest.jfk gid:15075",
            "relay.satest.jfk gid:15076",
            "svc.satest.jfk gid:15077",
            "nas.satest.jfk gid:15078",
            "db.satest.jfk gid:15079",
            "zenossdb.satest.jfk gid:15080",
            "task.satest.jfk gid:15081",
            "checkout.satest.jfk gid:15082",
            "login.satest.jfk gid:15083",
            "fusionio.satest.jfk gid:15084",
            "rhcluster.satest.jfk gid:15085",
            "multipath.satest.jfk gid:15086",
            "extranet.satest.jfk gid:15087",
            "zenoss_server.satest.jfk gid:15088",
            "tripwire.satest.jfk gid:15089",
            "sysadmin.satest.jfk gid:400",
            "iad.satest.jfk gid:16000",
            "prod_iad.satest.jfk gid:16001",
            "authsvc1_prod_iad.satest.jfk gid:16002",
            "authsvc2_prod_iad.satest.jfk gid:16003",
            "authsvc3_prod_iad.satest.jfk gid:16004",
            "bbi1_prod_iad.satest.jfk gid:16005",
            "bbi2_prod_iad.satest.jfk gid:16006",
            "bbi3_prod_iad.satest.jfk gid:16007",
            "bbi4_prod_iad.satest.jfk gid:16008",
            "checkout1_prod_iad.satest.jfk gid:16009",
            "checkout2_prod_iad.satest.jfk gid:16010",
            "checkout3_prod_iad.satest.jfk gid:16011",
            "checkout4_prod_iad.satest.jfk gid:16012",
            "city1_prod_iad.satest.jfk gid:16013",
            "city2_prod_iad.satest.jfk gid:16014",
            "cm1_prod_iad.satest.jfk gid:16015",
            "db1_prod_iad.satest.jfk gid:16016",
            "db2_prod_iad.satest.jfk gid:16017",
            "db3_prod_iad.satest.jfk gid:16018",
            "db4_prod_iad.satest.jfk gid:16019",
            "db5_prod_iad.satest.jfk gid:16020",
            "dep1_prod_iad.satest.jfk gid:16021",
            "dw1_prod_iad.satest.jfk gid:16022",
            "etl1_prod_iad.satest.jfk gid:16023",
            "etl2_prod_iad.satest.jfk gid:16024",
            "gw1_prod_iad.satest.jfk gid:16025",
            "gw2_prod_iad.satest.jfk gid:16026",
            "job1_prod_iad.satest.jfk gid:16027",
            "job2_prod_iad.satest.jfk gid:16028",
            "ldap1_prod_iad.satest.jfk gid:16029",
            "ldap2_prod_iad.satest.jfk gid:16030",
            "ldap3_prod_iad.satest.jfk gid:16031",
            "log1_prod_iad.satest.jfk gid:16032",
            "log2_prod_iad.satest.jfk gid:16033",
            "login1_prod_iad.satest.jfk gid:16034",
            "login2_prod_iad.satest.jfk gid:16035",
            "login3_prod_iad.satest.jfk gid:16036",
            "login4_prod_iad.satest.jfk gid:16037",
            "nas1_prod_iad.satest.jfk gid:16038",
            "ns1_prod_iad.satest.jfk gid:16039",
            "ns2_prod_iad.satest.jfk gid:16040",
            "spdf.satest.jfk gid:15053",
            "stage.satest.jfk gid:15055",
            "olb1_prod_iad.satest.jfk gid:16041",
            "olb2_prod_iad.satest.jfk gid:16042",
            "olb3_prod_iad.satest.jfk gid:16043",
            "pagegen1_prod_iad.satest.jfk gid:16044",
            "pagegen2_prod_iad.satest.jfk gid:16045",
            "pagegen3_prod_iad.satest.jfk gid:16046",
            "pagegen4_prod_iad.satest.jfk gid:16047",
            "pagegen5_prod_iad.satest.jfk gid:16048",
            "pweb1_prod_iad.satest.jfk gid:16049",
            "pweb2_prod_iad.satest.jfk gid:16050",
            "pweb3_prod_iad.satest.jfk gid:16051",
            "relay1_prod_iad.satest.jfk gid:16052",
            "relay2_prod_iad.satest.jfk gid:16053",
            "spare1_prod_iad.satest.jfk gid:16054",
            "spare2_prod_iad.satest.jfk gid:16055",
            "spare3_prod_iad.satest.jfk gid:16056",
            "splunk1_prod_iad.satest.jfk gid:16057",
            "splunk2_prod_iad.satest.jfk gid:16058",
            "splunk3_prod_iad.satest.jfk gid:16059",
            "svc1_prod_iad.satest.jfk gid:16060",
            "svc10_prod_iad.satest.jfk gid:16061",
            "svc11_prod_iad.satest.jfk gid:16062",
            "svc12_prod_iad.satest.jfk gid:16063",
            "svc13_prod_iad.satest.jfk gid:16064",
            "svc14_prod_iad.satest.jfk gid:16065",
            "svc15_prod_iad.satest.jfk gid:16066",
            "svc16_prod_iad.satest.jfk gid:16067",
            "svc2_prod_iad.satest.jfk gid:16068",
            "svc3_prod_iad.satest.jfk gid:16069",
            "svc4_prod_iad.satest.jfk gid:16070",
            "svc5_prod_iad.satest.jfk gid:16071",
            "svc6_prod_iad.satest.jfk gid:16072",
            "svc7_prod_iad.satest.jfk gid:16073",
            "svc8_prod_iad.satest.jfk gid:16074",
            "svc9_prod_iad.satest.jfk gid:16075",
            "svclb1_prod_iad.satest.jfk gid:16076",
            "svclb2_prod_iad.satest.jfk gid:16077",
            "svclb3_prod_iad.satest.jfk gid:16078",
            "swift1_prod_iad.satest.jfk gid:16079",
            "swift2_prod_iad.satest.jfk gid:16080",
            "swift3_prod_iad.satest.jfk gid:16081",
            "swift4_prod_iad.satest.jfk gid:16082",
            "task1_prod_iad.satest.jfk gid:16083",
            "task2_prod_iad.satest.jfk gid:16084",
            "tw1_prod_iad.satest.jfk gid:16085",
            "weba1_prod_iad.satest.jfk gid:16086",
            "weba2_prod_iad.satest.jfk gid:16087",
            "weba3_prod_iad.satest.jfk gid:16088",
            "xen1_prod_iad.satest.jfk gid:16089",
            "xen2_prod_iad.satest.jfk gid:16090",
            "xen3_prod_iad.satest.jfk gid:16091",
            "xen4_prod_iad.satest.jfk gid:16092",
            "zbx1_prod_iad.satest.jfk gid:16093",
            "zbx2_prod_iad.satest.jfk gid:16094",
            "zenoss1_prod_iad.satest.jfk gid:16095",
            "zenossdb1_prod_iad.satest.jfk gid:16096",
            "hudson.satest.jfk gid:16099",
            "bogus.satest.jfk gid:502",
            "ns2_satest_jfk.satest.jfk gid:503",
            "users.qa.jfk gid:401",
            "web.qa.jfk gid:402",
            "hudson2_satest_jfk.satest.jfk gid:500",
            "hudson1_satest_jfk.satest.jfk gid:501",
            "xen.satest.jfk gid:505",
            "dcmon1_satest_jfk.satest.jfk gid:507",
            "cm2_satest_jfk.satest.jfk gid:506",
            "jira1_satest_jfk.satest.jfk gid:508",
            "mtest3_satest_jfk.satest.jfk gid:511",
            "ci1_satest_jfk.satest.jfk gid:510",
            "cobbler1_satest_jfk.satest.jfk gid:512",
            "ldap1_satest_jfk.satest.jfk gid:513",
            "ldap2_satest_jfk.satest.jfk gid:514",
            "ns1_satest_jfk.satest.jfk gid:515",
            "rpmbuilder1_satest_jfk.satest.jfk gid:516",
            "ci1_satest_jfk_sudo.satest.jfk gid:517",
            "cm2_satest_jfk_sudo.satest.jfk gid:518",
            "cobbler1_satest_jfk_sudo.satest.jfk gid:519",
            "dcmon1_satest_jfk_sudo.satest.jfk gid:520",
            "hudson1_satest_jfk_sudo.satest.jfk gid:521",
            "hudson2_satest_jfk_sudo.satest.jfk gid:522",
            "jira1_satest_jfk_sudo.satest.jfk gid:523",
            "ldap1_satest_jfk_sudo.satest.jfk gid:524",
            "ldap2_satest_jfk_sudo.satest.jfk gid:525",
            "mtest3_satest_jfk_sudo.satest.jfk gid:526",
            "ns1_satest_jfk_sudo.satest.jfk gid:527",
            "ns2_satest_jfk_sudo.satest.jfk gid:528",
            "puppet_satest_jfk_sudo.satest.jfk gid:529",
            "rpmbuilder1_satest_jfk_sudo.satest.jfk gid:530",
            "splunk1_satest_jfk_sudo.satest.jfk gid:531",
            "stage2_satest_jfk_sudo.satest.jfk gid:532",
            "stage7_satest_jfk_sudo.satest.jfk gid:533",
            "testing123_satest_jfk_sudo.satest.jfk gid:535",
            "xenserver1_satest_jfk_sudo.satest.jfk gid:536",
            "xenserver2_satest_jfk_sudo.satest.jfk gid:537",
            "xenserver3_satest_jfk_sudo.satest.jfk gid:538",
            "zbx1_satest_jfk_sudo.satest.jfk gid:539",
            "zendc1_satest_jfk_sudo.satest.jfk gid:540",
            "zenoss1_satest_jfk_sudo.satest.jfk gid:541",
            "jfk_sudo.satest.jfk gid:542",
            "Group_sudo.satest.jfk gid:509",
            "cognos_sudo.satest.jfk gid:543",
            "data_sudo.satest.jfk gid:544",
            "dbadmin_sudo.satest.jfk gid:545",
            "dwuser_sudo.satest.jfk gid:546",
            "emailpers_sudo.satest.jfk gid:547",
            "fcpigeon_sudo.satest.jfk gid:548",
            "giltread_sudo.satest.jfk gid:549",
            "hadoop_sudo.satest.jfk gid:550",
            "iphone_sudo.satest.jfk gid:551",
            "kettleuser_dev_sudo.satest.jfk gid:552",
            "kettleuser_preprod_sudo.satest.jfk gid:553",
            "msgsys_sudo.satest.jfk gid:554",
            "puppet_sudo.satest.jfk gid:555",
            "spotfire_sudo.satest.jfk gid:556",
            "zabbix_sudo.satest.jfk gid:557",
            "zenoss_sudo.satest.jfk gid:558",
            "zeus_sudo.satest.jfk gid:559",
            "adhoc_sudo.satest.jfk gid:560",
            "app_sudo.satest.jfk gid:561",
            "authsvc_sudo.satest.jfk gid:562",
            "backup_sudo.satest.jfk gid:563",
            "bbiphone_sudo.satest.jfk gid:564",
            "bb_sudo.satest.jfk gid:565",
            "bosedgelb_sudo.satest.jfk gid:566",
            "build_sudo.satest.jfk gid:567",
            "cache_sudo.satest.jfk gid:568",
            "cartsvc_sudo.satest.jfk gid:569",
            "cms_sudo.satest.jfk gid:570",
            "contint_sudo.satest.jfk gid:571",
            "cs_sudo.satest.jfk gid:572",
            "datasvc_sudo.satest.jfk gid:573",
            "dbutil_sudo.satest.jfk gid:574",
            "deploy_sudo.satest.jfk gid:575",
            "dns_sudo.satest.jfk gid:576",
            "esp_sudo.satest.jfk gid:577",
            "etl_sudo.satest.jfk gid:578",
            "expdb_sudo.satest.jfk gid:579",
            "falconcity_sudo.satest.jfk gid:580",
            "falcon_sudo.satest.jfk gid:581",
            "finance_sudo.satest.jfk gid:582",
            "gblscms_sudo.satest.jfk gid:583",
            "gem_sudo.satest.jfk gid:584",
            "glx_sudo.satest.jfk gid:585",
            "gold_sudo.satest.jfk gid:586",
            "ids_sudo.satest.jfk gid:587",
            "inv_sudo.satest.jfk gid:588",
            "job_sudo.satest.jfk gid:589",
            "jsetapi_sudo.satest.jfk gid:590",
            "kvcart_sudo.satest.jfk gid:591",
            "kvoo_sudo.satest.jfk gid:592",
            "kvreginfo_sudo.satest.jfk gid:593",
            "kvso_sudo.satest.jfk gid:594",
            "lb_sudo.satest.jfk gid:595",
            "ldap_sudo.satest.jfk gid:596",
            "listserv_sudo.satest.jfk gid:597",
            "misc_sudo.satest.jfk gid:598",
            "mon_sudo.satest.jfk gid:599",
            "mothership_sudo.satest.jfk gid:600",
            "oakedgelb_sudo.satest.jfk gid:601",
            "originlb_sudo.satest.jfk gid:602",
            "pagegen_sudo.satest.jfk gid:603",
            "paysvc_sudo.satest.jfk gid:604",
            "pm_sudo.satest.jfk gid:605",
            "qalb_sudo.satest.jfk gid:606",
            "qauser_sudo.satest.jfk gid:607",
            "rep_sudo.satest.jfk gid:608",
            "scms_sudo.satest.jfk gid:609",
            "smtp_sudo.satest.jfk gid:610",
            "solr_sudo.satest.jfk gid:611",
            "spare_sudo.satest.jfk gid:612",
            "web_sudo.satest.jfk gid:613",
            "users_sudo.satest.jfk gid:614",
            "splunk_sudo.satest.jfk gid:615",
            "stc_sudo.satest.jfk gid:616",
            "svclb_sudo.satest.jfk gid:617",
            "swift_sudo.satest.jfk gid:618",
            "test_sudo.satest.jfk gid:619",
            "usersvc_sudo.satest.jfk gid:620",
            "util_sudo.satest.jfk gid:621",
            "vertexapp_sudo.satest.jfk gid:622",
            "vertexdb_sudo.satest.jfk gid:623",
            "vertexqaapp_sudo.satest.jfk gid:624",
            "vertexqadb_sudo.satest.jfk gid:625",
            "waitlistsvc_sudo.satest.jfk gid:626",
            "zendc_sudo.satest.jfk gid:627",
            "zabbix_db_sudo.satest.jfk gid:628",
            "loghost_sudo.satest.jfk gid:629",
            "log_sudo.satest.jfk gid:630",
            "pweb_sudo.satest.jfk gid:632",
            "weba_sudo.satest.jfk gid:633",
            "bastion_sudo.satest.jfk gid:634",
            "mta_sudo.satest.jfk gid:635",
            "relay_sudo.satest.jfk gid:636",
            "svc_sudo.satest.jfk gid:637",
            "nas_sudo.satest.jfk gid:638",
            "db_sudo.satest.jfk gid:639",
            "zenossdb_sudo.satest.jfk gid:640",
            "task_sudo.satest.jfk gid:641",
            "checkout_sudo.satest.jfk gid:642",
            "login_sudo.satest.jfk gid:643",
            "fusionio_sudo.satest.jfk gid:644",
            "rhcluster_sudo.satest.jfk gid:645",
            "multipath_sudo.satest.jfk gid:646",
            "extranet_sudo.satest.jfk gid:647",
            "zenoss_server_sudo.satest.jfk gid:648",
            "tripwire_sudo.satest.jfk gid:649",
            "sysadmin_sudo.satest.jfk gid:650",
            "iad_sudo.satest.jfk gid:651",
            "prod_iad_sudo.satest.jfk gid:652",
            "authsvc1_prod_iad_sudo.satest.jfk gid:653",
            "authsvc2_prod_iad_sudo.satest.jfk gid:654",
            "authsvc3_prod_iad_sudo.satest.jfk gid:655",
            "bbi1_prod_iad_sudo.satest.jfk gid:656",
            "bbi2_prod_iad_sudo.satest.jfk gid:657",
            "bbi3_prod_iad_sudo.satest.jfk gid:658",
            "bbi4_prod_iad_sudo.satest.jfk gid:659",
            "checkout1_prod_iad_sudo.satest.jfk gid:660",
            "checkout2_prod_iad_sudo.satest.jfk gid:661",
            "checkout3_prod_iad_sudo.satest.jfk gid:662",
            "checkout4_prod_iad_sudo.satest.jfk gid:663",
            "city1_prod_iad_sudo.satest.jfk gid:664",
            "city2_prod_iad_sudo.satest.jfk gid:665",
            "cm1_prod_iad_sudo.satest.jfk gid:666",
            "db1_prod_iad_sudo.satest.jfk gid:667",
            "db2_prod_iad_sudo.satest.jfk gid:668",
            "db3_prod_iad_sudo.satest.jfk gid:669",
            "db4_prod_iad_sudo.satest.jfk gid:670",
            "db5_prod_iad_sudo.satest.jfk gid:671",
            "dep1_prod_iad_sudo.satest.jfk gid:672",
            "dw1_prod_iad_sudo.satest.jfk gid:673",
            "etl1_prod_iad_sudo.satest.jfk gid:674",
            "etl2_prod_iad_sudo.satest.jfk gid:675",
            "gw1_prod_iad_sudo.satest.jfk gid:676",
            "gw2_prod_iad_sudo.satest.jfk gid:677",
            "job1_prod_iad_sudo.satest.jfk gid:678",
            "job2_prod_iad_sudo.satest.jfk gid:679",
            "ldap1_prod_iad_sudo.satest.jfk gid:680",
            "ldap2_prod_iad_sudo.satest.jfk gid:681",
            "ldap3_prod_iad_sudo.satest.jfk gid:682",
            "log1_prod_iad_sudo.satest.jfk gid:683",
            "log2_prod_iad_sudo.satest.jfk gid:684",
            "login1_prod_iad_sudo.satest.jfk gid:685",
            "login2_prod_iad_sudo.satest.jfk gid:686",
            "login3_prod_iad_sudo.satest.jfk gid:687",
            "login4_prod_iad_sudo.satest.jfk gid:688",
            "nas1_prod_iad_sudo.satest.jfk gid:689",
            "ns1_prod_iad_sudo.satest.jfk gid:690",
            "ns2_prod_iad_sudo.satest.jfk gid:691",
            "spdf_sudo.satest.jfk gid:692",
            "stage_sudo.satest.jfk gid:693",
            "olb1_prod_iad_sudo.satest.jfk gid:694",
            "olb2_prod_iad_sudo.satest.jfk gid:695",
            "olb3_prod_iad_sudo.satest.jfk gid:696",
            "pagegen1_prod_iad_sudo.satest.jfk gid:697",
            "pagegen2_prod_iad_sudo.satest.jfk gid:698",
            "pagegen3_prod_iad_sudo.satest.jfk gid:699",
            "pagegen4_prod_iad_sudo.satest.jfk gid:700",
            "pagegen5_prod_iad_sudo.satest.jfk gid:701",
            "pweb1_prod_iad_sudo.satest.jfk gid:702",
            "pweb2_prod_iad_sudo.satest.jfk gid:703",
            "pweb3_prod_iad_sudo.satest.jfk gid:704",
            "relay1_prod_iad_sudo.satest.jfk gid:705",
            "relay2_prod_iad_sudo.satest.jfk gid:706",
            "spare1_prod_iad_sudo.satest.jfk gid:707",
            "spare2_prod_iad_sudo.satest.jfk gid:708",
            "spare3_prod_iad_sudo.satest.jfk gid:709",
            "splunk1_prod_iad_sudo.satest.jfk gid:710",
            "splunk2_prod_iad_sudo.satest.jfk gid:711",
            "splunk3_prod_iad_sudo.satest.jfk gid:712",
            "svc1_prod_iad_sudo.satest.jfk gid:713",
            "svc10_prod_iad_sudo.satest.jfk gid:714",
            "svc11_prod_iad_sudo.satest.jfk gid:715",
            "svc12_prod_iad_sudo.satest.jfk gid:716",
            "svc13_prod_iad_sudo.satest.jfk gid:717",
            "svc14_prod_iad_sudo.satest.jfk gid:718",
            "svc15_prod_iad_sudo.satest.jfk gid:719",
            "svc16_prod_iad_sudo.satest.jfk gid:720",
            "svc2_prod_iad_sudo.satest.jfk gid:721",
            "svc3_prod_iad_sudo.satest.jfk gid:722",
            "svc4_prod_iad_sudo.satest.jfk gid:723",
            "svc5_prod_iad_sudo.satest.jfk gid:724",
            "svc6_prod_iad_sudo.satest.jfk gid:725",
            "svc7_prod_iad_sudo.satest.jfk gid:726",
            "svc8_prod_iad_sudo.satest.jfk gid:727",
            "svc9_prod_iad_sudo.satest.jfk gid:728",
            "svclb1_prod_iad_sudo.satest.jfk gid:729",
            "svclb2_prod_iad_sudo.satest.jfk gid:730",
            "svclb3_prod_iad_sudo.satest.jfk gid:731",
            "swift1_prod_iad_sudo.satest.jfk gid:732",
            "swift2_prod_iad_sudo.satest.jfk gid:733",
            "swift3_prod_iad_sudo.satest.jfk gid:734",
            "swift4_prod_iad_sudo.satest.jfk gid:735",
            "task1_prod_iad_sudo.satest.jfk gid:736",
            "task2_prod_iad_sudo.satest.jfk gid:737",
            "tw1_prod_iad_sudo.satest.jfk gid:738",
            "weba1_prod_iad_sudo.satest.jfk gid:739",
            "weba2_prod_iad_sudo.satest.jfk gid:740",
            "weba3_prod_iad_sudo.satest.jfk gid:741",
            "xen1_prod_iad_sudo.satest.jfk gid:742",
            "xen2_prod_iad_sudo.satest.jfk gid:743",
            "xen3_prod_iad_sudo.satest.jfk gid:744",
            "xen4_prod_iad_sudo.satest.jfk gid:745",
            "zbx1_prod_iad_sudo.satest.jfk gid:746",
            "zbx2_prod_iad_sudo.satest.jfk gid:747",
            "zenoss1_prod_iad_sudo.satest.jfk gid:748",
            "zenossdb1_prod_iad_sudo.satest.jfk gid:749",
            "hudson_sudo.satest.jfk gid:750",
            "bogus_sudo.satest.jfk gid:751",
            "xen_sudo.satest.jfk gid:752",
            "zabbix_server_sudo.satest.jfk gid:631",
            "mysql_sudo.satest.jfk gid:754",
            "java_sudo.satest.jfk gid:756",
            "postgres_sudo.satest.jfk gid:753",
            "teststore_satest_jfk.satest.jfk gid:757",
            "test6_satest_jfk.mgmt.jfk gid:500",
            "cm1_satest_jfk.satest.jfk gid:758",
            "testeasyinstall_satest_jfk.satest.jfk gid:504",
            "users.prod.jfk gid:500",
            "web.prod.jfk gid:501",
            "cobbler1_satest_jfk.prod.jfk gid:512",
            "jira_sudo.satest.jfk gid:755",
            "xen4_prod_iad_sudo.prod.jfk gid:745",
            "extranet_sudo.prod.jfk gid:647",
            "jira_sudo.prod.jfk gid:755",
            "test2_satest_jfk.satest.jfk gid:534",
            "test2_satest_jfk_sudo.satest.jfk gid:760",
            "swaptest2_satest_jfk.satest.jfk gid:761",
            "swaptest2_satest_jfk_sudo.satest.jfk gid:762",
            "swaptest1_satest_jfk_sudo.satest.jfk gid:764",
            "test5_satest_jfk.satest.jfk gid:759",
            "test5_satest_jfk_sudo.satest.jfk gid:765",
            "solr12_satest_jfk.satest.jfk gid:766",
            "test6_satest_jfk_sudo.mgmt.jfk gid:501",
            "swaptest1_satest_jfk.mgmt.jfk gid:502",
            "swaptest1_satest_jfk_sudo.mgmt.jfk gid:503",
            "swaptest1_satest_jfk.satest.jfk gid:763",
            "test6_satest_jfk.satest.jfk gid:767",
            "test6_satest_jfk_sudo.satest.jfk gid:768"
        ]

        self.assertEqual(result, ret)
        print "[API_list_values] test_lsv_groups_good: PASSED"

    # available_hardware=True, good output
    def test_lsv_available_hardware_good(self):
        query = {'available_hardware': True}
        result = lsv.lsv(query)

        ret = [ "H739TK1" ]

        self.assertEqual(result, ret)
        print "[API_list_values] test_lsv_available_hardware_good: PASSED"

    # vlans=True, good output
    def test_lsv_vlans_good(self):
        query = {'vlans': True}
        result = lsv.lsv(query)

        ret = [ 200, 201, 666 ]

        self.assertEqual(result, ret)
        print "[API_list_values] test_lsv_vlans_good: PASSED"
