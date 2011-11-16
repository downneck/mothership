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

class ServerInfo:

    def __init__(self, cfg):
        self.cfg = cfg
        self.name = "ServerInfo"
        self.modulename = "serverinfo"
        self.urls = [
                     {
                      'url': '/serverinfo',
                      'call': 'get()',
                      'required_args': ['host', 'realm', 'site_id'],
                      'optional_args': [],
                     },
                     {
                      'url': '/serverinfo/search',
                      'call': 'get_host()',
                      'required_args': [],
                      'optional_args': ['hw_tag', 'ip', 'mac']
                     },
                    ]

    # ask the module to define its REST urls
    def get_urls(self):
        return urls

    def get_host(self, hw_tag=None, ip=None, mac=None):
        """
        [description]
        search for a host based on info supplied

        [parameter info]
        optional:
            hw_tag: the hardware tag to search for
            ip: the ip to search for
            mac: the mac address to search for

        [return value]
        returns a hostname if successful, raises an exception if unsuccessful
        """

        cfg = self.cfg

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

    def getserverinfo(self, host, realm, site_id):
        """
        [description]
        return all information for a server, identified by host.realm.site_id 

        [parameter info]
        required:
            host: the hostname of the server we're displaying
            realm: the realm of the server we're displaying
            site_id: the site_id of the server we're displaying

        [return value]
        ret = a list of objects related to the server entry 
        """

        cfg = self.cfg
        kvs = [] # stores values from kv search for tag=? that apply to our server
        ret = [] # order: [0]=server, [1]=hardware, [2]=kv, [3]=network, [4]=network, (+more network objects if there are more)

        # gather server info from mothership's db
        try:
          # hardware and server entries
          h, s = cfg.dbsess.query(Hardware, Server).\
          filter(Server.hostname==host).\
          filter(Server.realm==realm).\
          filter(Server.site_id==site_id).\
          filter(Hardware.hw_tag==Server.hw_tag).first()

          ret.append(s) # add server to return list
          ret.append(h) # add hardware to return list

          # kv entries
          for h2, s2 in cfg.dbsess.query(Hardware, Server).\
          filter(Server.hostname==host).\
          filter(Server.realm==realm).\
          filter(Server.site_id==site_id).\
          filter(Hardware.hw_tag==Server.hw_tag):
            fqdn = '.'.join([host,realm,site_id])
            kvs = mothership.kv.collect(cfg, fqdn, key='tag')
          ret.append(kvs) # add kv values to return list

          # network entries
          for n in cfg.dbsess.query(Network).\
          filter(Server.id==Network.server_id).\
          filter(Server.hostname==s.hostname).\
          order_by(Network.interface).all():
              ret.append(n)

        except TypeError:
          raise ServerInfoError("host \"%s\" not found" % host)
        except:
          raise ServerInfoError("something horrible happened")

        return ret


    def ip_only(self, host, realm, site_id):
        """
        [description]
        print ip information for a server

        [parameter info]
        required:
            host: the hostname of the server we're displaying
            realm: the realm of the server we're displaying
            site_id: the site_id of the server we're displaying

        [return value]
        no explicit return
        """

        cfg = self.cfg

        # gather host info from mothership
        h, s = cfg.dbsess.query(Hardware, Server).filter(Server.hostname==host).\
        filter(Server.realm==realm).\
        filter(Server.site_id==site_id).\
        filter(Hardware.hw_tag==Server.hw_tag).first()
    
        print "host|\t%s.%s.%s" % (host, realm, site_id)
    
        # display the interface and associated ips
        for n in cfg.dbsess.query(Network).\
        filter(Server.id==Network.server_id).\
        filter(Server.hostname==s.hostname).\
        order_by(Network.interface).all():
          if n.ip == None:
            print "%s|\tprivate ip: %s\t | public ip: %s" % (n.interface, n.ip, n.public_ip)
          else:
            print "%s|\tprivate ip: %s\t | public ip: %s" % (n.interface, n.ip, n.public_ip)
    
    def mac_only(self, host, realm, site_id):
        """
        [description]
        print mac address information for a server 
    
        [parameter info]
        required:
            host: the hostname of the server we're displaying
            realm: the realm of the server we're displaying
            site_id: the site_id of the server we're displaying
    
        [return value]
        no explicit return 
        """
    
        cfg = self.cfg

        # gather host info from mothership
        h, s = cfg.dbsess.query(Hardware, Server).filter(Server.hostname==host).\
        filter(Server.realm==realm).\
        filter(Server.site_id==site_id).\
        filter(Hardware.hw_tag==Server.hw_tag).first()
    
        print "host|\t%s.%s.%s" % (host, realm, site_id)
    
        # display the interface and associated mac address
        for n in cfg.dbsess.query(Network).\
        filter(Server.id==Network.server_id).\
        filter(Server.hostname==s.hostname).\
        order_by(Network.interface).all():
          print "%s|\tip: %s" % (n.interface, n.mac)
    
