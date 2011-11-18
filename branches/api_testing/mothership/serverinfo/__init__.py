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
        self.version = '1' # the version of this module
        self.name = "ServerInfo" # class name
        self.namespace = "serverinfo" # class' namespace
        self.metadata = { # the metadata dict, communicates to the outside world what we're capable of
            'config': { # some basic module-wide config data
                'module_dependencies': { # what other modules do we depend on?
                    'kv': '1', # a module, and its minimum accepted version
                    'mothership_models': '1' # another module, and its minimum accepted version
                },
            },
            'functions': { # a dict of functions we're presenting to the outside world
                'getserverinfo': { # a function identifier
                    'description': 'retrieve server info for a server identified by hostname.realm.site_id', # for generating help
                    'url': '/'+self.namespace, # REST url we'd like to use
                    'class': self.name, # our class name
                    'namespace': self.namespace, # our desired namespace
                    'version': self.version, # our version
                    'call': 'getserverinfo', # the function call, stripped of () and args
                    'required_args': { # dict of info about arguments we just can't live without
                        'host': 'string', # an arg, and its type
                        'realm': 'string', # another arg, and its type
                        'site_id': 'string' # yet another arg, and its type
                    },
                    'optional_args': { # dict holding optional argument info
                        'min': '0', # minimum number of optional args we'll accept
                        'max': '2', # maximum number of optional args we'll accept
                        'args': { # the argument definitions themselves
                            'test': 'int', # an arg and its type
                            'test2': 'ip', # another arg and its type
                        },
                    },
                    'cmdln_aliases': [ # list of desired subcommand aliases for our command line
                        'si', # alias
                        'server_info', # another alias
                        'serverinfo', # yet another alias
                    ],
                    'return': { # a dict defining what our return value looks like
                        'server': 'ORMobject', # a server table object
                        'hardware': 'ORMobject', # a hardware table object
                        'network': [ # a list of network objects, may be 1 to N objects
                            'ORMobject', # a network table object
                            'ORMobject', # a second network table object
                            ],
                        'kv': [ # a list of kv objects describing tags that apply to the machine, may be 0 to N objects
                            'ORMobject', # a kv table object
                            'ORMobject', # a second kv table object
                        ],
                    },
                },
                'search': {
                    'description': 'retrieve server info, identified by one of: hw_tag (hardware tag), ip (ip address), mac (mac address)',
                    'url': '/'+self.namespace+'/search',
                    'class': self.name,
                    'namespace': self.namespace,
                    'version': self.version,
                    'call': 'get_host',
                    'required_args': {},
                    'optional_args': {
                        'min': '1',
                        'max': '1',
                        'args': {
                            'hw_tag': 'string',
                            'ip': 'string',
                            'mac': 'string',
                        },
                    },
                    'cmdln_aliases': [
                        'si_search',
                    ],
                    'return': {
                        'server': 'ORMobject',
                        'hardware': 'ORMobject',
                        'network': [
                            'ORMobject',
                            'ORMobject',
                            ],
                        'kv': [
                            'ORMobject',
                            'ORMobject',
                        ],
                    },
                },
            },
        }


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
        kvs = [] # stores kv objects to return
        nets = [] # stores network objects to return
        ret = {} # order: [0]=server, [1]=hardware, [2]=kv, [3]=network, [4]=network, (+more network objects if there are more)

        # gather server info from mothership's db
        try:
          # hardware and server entries
          h, s = cfg.dbsess.query(Hardware, Server).\
          filter(Server.hostname==host).\
          filter(Server.realm==realm).\
          filter(Server.site_id==site_id).\
          filter(Hardware.hw_tag==Server.hw_tag).first()

          ret['server'] = s # add server object to return dict
          ret['hardware'] = h # add hardware object to return dict

          # kv entries
          for h2, s2 in cfg.dbsess.query(Hardware, Server).\
          filter(Server.hostname==host).\
          filter(Server.realm==realm).\
          filter(Server.site_id==site_id).\
          filter(Hardware.hw_tag==Server.hw_tag):
            fqdn = '.'.join([host,realm,site_id])
            kvs = mothership.kv.collect(cfg, fqdn, key='tag')
          ret['kv'] = kvs # add list of kv objects to return dict

          # network entries
          for n in cfg.dbsess.query(Network).\
          filter(Server.id==Network.server_id).\
          filter(Server.hostname==s.hostname).\
          order_by(Network.interface).all():
              nets.append(n) # add network objects to our list
          ret['network'] = nets # add list of network objects to return dict

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
    
