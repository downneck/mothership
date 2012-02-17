# Copyright 2011 Gilt Groupe, INC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
    mothership.serverinfo

    Collects and displays information about servers
"""

# import some modules
import sys
import mothership
import mothership.kv
from mothership.mothership_models import *
from sqlalchemy import or_, desc, MetaData

class ServerInfoError(Exception):
    pass


def get_host(cfg, hw_tag=None, ip=None, mac=None):
    """
    [description]
    search for a host based on info supplied 

    [parameter info]
    required:
        cfg: the config object. useful everywhere
    optional:
        hw_tag: the hardware tag to search for
        ip: the ip to search for
        mac: the mac address to search for

    [return value]
    returns a hostname if successful, raises an exception if unsuccessful
    """

    if sum(x != None for x in (hw_tag, ip, mac)) != 1:
        raise ServerInfoError(
                "get_host() takes precisely ONE value to search on.\n"
                "hw_tag=%s ip=%s mac=%s" % hw_tag, ip, mac)
    elif hw_tag != None:
        try:
            s = cfg.dbsess.query(Server).\
                filter(Server.hw_tag==hw_tag).\
                filter(Server.virtual==False).first()
            if s.hostname:
                return s.hostname
        except TypeError:
            raise ServerInfoError("no host found with hw_tag: %s" % hw_tag)
    elif ip != None:
        # try the private ip
        try:
            s, n = cfg.dbsess.query(Server, Network).\
                filter(Server.id==Network.server_id).\
                filter(Network.ip==ip).first()
            if s.hostname:
                return s.hostname
        except TypeError:
            pass
        # try the public ip
        try:
            s, n = cfg.dbsess.query(Server, Network).\
                filter(Server.id==Network.server_id).\
                filter(Network.public_ip==ip).first()
            if s.hostname:
                return s.hostname
        except TypeError:
            pass
        raise ServerInfoError(
                "no host found with public or private ip: %s" % ip)
    elif mac != None:
        try:
            h, s = cfg.dbsess.query(Network, Server).\
                filter(Network.hw_tag==Server.hw_tag).\
                filter(Network.mac==mac).\
                filter(Server.virtual==False).first()
            if s.hostname:
                return s.hostname
        except TypeError:
            pass
        raise ServerInfoError("no host found with MAC address: %s" % mac)
    else:
        raise ServerInfoError("You did something weird, please don't."
                "hw_tag=%s ip=%s mac=%s" % hw_tag, ip, mac)

def all(cfg, host, realm, site_id):
    """
    [description]
    search for a host based on info supplied 

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        host: the hostname of the server we're displaying
        realm: the realm of the server we're displaying
        site_id: the site_id of the server we're displaying

    [return value]
    no explicit return 
    """

    # gather server info from mothership's db
    fqdn = '.'.join([host,realm,site_id])
    try:
        kvs = mothership.kv.collect(cfg, fqdn, key='tag')
    except:
        kvs = []

    try:
        h, s = cfg.dbsess.query(Hardware, Server).\
            filter(Server.hostname==host).\
            filter(Server.realm==realm).\
            filter(Server.site_id==site_id).\
            filter(Hardware.hw_tag==Server.hw_tag).first()
    except TypeError:
        raise ServerInfoError("host \"%s\" not found" % fqdn)
    except:
        raise ServerInfoError("something horrible happened")

    # fire EVERYTHING!
    print ""
    print "hostname:\t\t%s.%s.%s" % (s.hostname, s.realm, s.site_id)
    print "provisioned:\t\t%s" % (s.provision_date)
    print "purchased:\t\t%s" % (h.purchase_date)
    print "primary tag, index:\t%s, %s" % (s.tag, s.tag_index)
    print "ancillary tags:\t%s" % (', '.join([kv.value for kv in kvs]))
    print "security level:\t\t%s" % s.security_level
    print "cobbler_profile:\t%s" % (s.cobbler_profile)
    print "manufacturer, model:\t%s, %s" % (h.manufacturer, h.model)
    print "hardware tag:\t\t%s" % (h.hw_tag)
    if s.virtual is False:
        print "cores:\t\t\t%s" % (h.cores)
        print "ram (GB):\t\t%s" % (h.ram)
        print "disk:\t\t\t%s" % (h.disk)
    else:
        print "cores:\t\t\t%s" % (s.cores)
        print "ram (GB):\t\t%s" % (s.ram)
        print "disk:\t\t\t%s" % (s.disk)
    print "cpu speed:\t\t%s" % (h.cpu_speed)
    print ""
    for n in cfg.dbsess.query(Network).\
        filter(Network.server_id==s.id).\
        order_by(Network.interface).all():
        print "%s| mac: %-17s | ip: %-15s | public_ip: %-15s" % (n.interface, n.mac, n.ip, n.public_ip)
        print "%s| vlan: %-3s | switch: %-15s | switch_port: %-10s" % (n.interface, n.vlan, n.switch, n.switch_port)

def ip_only(cfg, host, realm, site_id):
    """
    [description]
    print ip information for a server 

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        host: the hostname of the server we're displaying
        realm: the realm of the server we're displaying
        site_id: the site_id of the server we're displaying

    [return value]
    no explicit return 
    """


    # gather host info from mothership
    h, s = cfg.dbsess.query(Hardware, Server).filter(Server.hostname==host).\
    filter(Server.realm==realm).\
    filter(Server.site_id==site_id).\
    filter(Hardware.hw_tag==Server.hw_tag).first()

    print "host|\t%s.%s.%s" % (host, realm, site_id)

    # display the interface and associated ips
    for n in cfg.dbsess.query(Network).\
    filter(Network.server_id==s.id).\
    order_by(Network.interface).all():
      if n.ip == None:
        print "%s|\tprivate ip: %s\t | public ip: %s" % (n.interface, n.ip, n.public_ip)
      else:
        print "%s|\tprivate ip: %s\t | public ip: %s" % (n.interface, n.ip, n.public_ip)

def mac_only(cfg, host, realm, site_id):
    """
    [description]
    print mac address information for a server 

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        host: the hostname of the server we're displaying
        realm: the realm of the server we're displaying
        site_id: the site_id of the server we're displaying

    [return value]
    no explicit return 
    """

    # gather host info from mothership
    h, s = cfg.dbsess.query(Hardware, Server).filter(Server.hostname==host).\
    filter(Server.realm==realm).\
    filter(Server.site_id==site_id).\
    filter(Hardware.hw_tag==Server.hw_tag).first()

    print "host|\t%s.%s.%s" % (host, realm, site_id)

    # display the interface and associated mac address
    for n in cfg.dbsess.query(Network).\
    filter(Network.server_id==s.id).\
    order_by(Network.interface).all():
      print "%s|\tip: %s" % (n.interface, n.mac)

