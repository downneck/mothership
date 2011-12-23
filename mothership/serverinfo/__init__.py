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
import mothership.validate
from mothership.mothership_models import *
from sqlalchemy import or_, desc, MetaData

class ServerInfoError(Exception):
    pass

class serverinfo:

    def __init__(self, cfg):
        self.cfg = cfg
        self.version = 1 # the version of this module
        self.name = 'serverinfo' # class name
        self.namespace = 'serverinfo' # class' namespace
        self.metadata = { # the metadata dict, communicates to the outside world what we're capable of
            'config': { # some basic module-wide config data
                'module_dependencies': { # what other modules do we depend on?
                    'kv': 1, # a module, and its minimum accepted version
                    'mothership_models': 1, # another module, and its minimum accepted version
                },
            },
            'methods': { # a dict of methods we're presenting to the outside world
                'get_host': { # a method identifier
                    'description': 'retrieve server info for a server identified by hostname.realm.site_id', # for generating help
                    'call': 'get_host', # the function call, stripped of () and args
                    'required_args': { # dict of info about arguments we just can't live without
                    },
                    'optional_args': { # dict holding optional argument info
                        'min': 1, # minimum number of optional args we'll accept
                        'max': 1, # maximum number of optional args we'll accept
                        'args': { # the argument definitions themselves
                            'hw_tag': { # an arg
                                'vartype': 'string', # its type
                                'desc': 'search for a hw_tag (hardware tag)', # its description
                            },
                            'ip': { # an arg
                                'vartype': 'string', # its type
                                'desc': 'search for an ip (public or private)', # its description
                            },
                            'mac': { # an arg
                                'vartype': 'string', # its type
                                'desc': 'search for a MAC address', # its description
                            },
                            'hostname': { # an arg
                                'vartype': 'string', # its type
                                'desc': 'search for a hostname', # its description
                            },
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
            },
        }


    def get_host(self, query):
        """
        [description]
        search for a host based on info supplied

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        returns a dict of ORMobjects if successful, "None" if unsuccessful
        """

        cfg = self.cfg
        ret = {}

        if len(query) > self.metadata['methods']['get_host']['optional_args']['max']:
            retval = "serverinfo: too many queries! max number of queries is: %s\n" % self.metadata['methods']['get_host']['optional_args']['max']
            retval += "serverinfo: you tried to pass %s queries\n" % len(query)
            if cfg.debug:
                print retval
            raise ServerInfoError(retval)
        elif len(query) < self.metadata['methods']['get_host']['optional_args']['min']:
            retval = "serverinfo: not enough queries! min number of queries is: %s\n" % self.metadata['methods']['get_host']['optional_args']['min']
            retval += "serverinfo: you tried to pass %s queries\n" % len(query)
            if cfg.debug:
                print retval
            raise ServerInfoError(retval)
        elif cfg.debug:
            print "serverinfo: num queries: %s" % len(query)
            print "serverinfo: max num queries: %s" % self.metadata['methods']['get_host']['optional_args']['max']

        if 'hw_tag' in query:
            try:
                s = cfg.dbsess.query(Server).\
                    filter(Server.hw_tag==query['hw_tag']).\
                    filter(Server.virtual==False).first()
                if s.hostname:
                    ret = self.__getserverinfo(s.hostname, s.realm, s.site_id)
            except TypeError:
                raise ServerInfoError("serverinfo/get_host: no host found with hw_tag: %s" % query['hw_tag'])
        if 'ip' in query:
            # try the private ip
            try:
                s, n = cfg.dbsess.query(Server, Network).\
                    filter(Server.id==Network.server_id).\
                    filter(Network.ip==query['ip']).first()
                if s.hostname:
                    ret = self.__getserverinfo(s.hostname, s.realm, s.site_id)
            except TypeError:
                pass
            # try the public ip
            try:
                s, n = cfg.dbsess.query(Server, Network).\
                    filter(Server.id==Network.server_id).\
                    filter(Network.public_ip==query['ip']).first()
                if s.hostname:
                    ret = self.__getserverinfo(s.hostname, s.realm, s.site_id)
            except TypeError:
                raise ServerInfoError("serverinfo/get_host: no host found with public or private ip: %s" % query['ip'])
        if 'mac' in query:
            try:
                h, s = cfg.dbsess.query(Network, Server).\
                    filter(Network.hw_tag==Server.hw_tag).\
                    filter(Network.mac==query['mac']).\
                    filter(Server.virtual==False).first()
                if s.hostname:
                    ret = self.__getserverinfo(s.hostname, s.realm, s.site_id, cfg.debug)
            except TypeError:
                raise ServerInfoError("serverinfo/get_host: no host found with MAC address: %s" % query['mac'])
        if 'hostname' in query:
            try:
                # this won't work with our RESTness
                #unqdn = mothership.validate.v_get_fqn(cfg, name=query['hostname'])
                #
                s = mothership.validate.v_get_host_obj(cfg, query['hostname'])
                if cfg.debug:
                    print s
                ret = self.__getserverinfo(s.hostname, s.realm, s.site_id)
            except:
                raise ServerInfoError("serverinfo/get_host: no host found with name: %s" % query['hostname'])

        if ret:
            return ret
        else:
            if cfg.debug:
                print "serverinfo/get_host: return value \"ret\" is empty!"
            raise ServerInfoError("serverinfo/get_host: return value\"ret\" is empty!")

    def __getserverinfo(self, host, realm, site_id):
        """
        [description]
        return all information for a server, identified by host.realm.site_id

        [parameter info]
        required:
            host: the hostname of the server we're displaying
            realm: the realm of the server we're displaying
            site_id: the site_id of the server we're displaying

        [return value]
        ret = a list of dicts related to the server entry
        """

        cfg = self.cfg
        kvs = [] # stores kv objects to return
        nets = [] # stores network objects to return
        ret = {} # dict of objects to return (except network and kv, which are lists of objects)

        # gather server info from mothership's db
        try:
          # hardware and server entries
          h, s = cfg.dbsess.query(Hardware, Server).\
          filter(Server.hostname==host).\
          filter(Server.realm==realm).\
          filter(Server.site_id==site_id).\
          filter(Hardware.hw_tag==Server.hw_tag).first()

          ret['server'] = s.to_dict() # add server object to return dict
          if cfg.debug:
              print s.to_dict()
          ret['hardware'] = h.to_dict() # add hardware object to return dict
          if cfg.debug:
              print h.to_dict()

          # kv entries
          for h2, s2 in cfg.dbsess.query(Hardware, Server).\
          filter(Server.hostname==host).\
          filter(Server.realm==realm).\
          filter(Server.site_id==site_id).\
          filter(Hardware.hw_tag==Server.hw_tag):
            fqdn = '.'.join([host,realm,site_id])
            kvs = mothership.kv.collect(cfg, fqdn, key='tag')
          ret['kv'] = kvs # add list of kv objects to return dict
          if cfg.debug:
              print kvs

          # network entries
          for n in cfg.dbsess.query(Network).\
          filter(Server.id==Network.server_id).\
          filter(Server.hostname==s.hostname).\
          order_by(Network.interface).all():
              nets.append(n.to_dict()) # add network objects to our list
              if cfg.debug:
                  print n.to_dict()
          ret['network'] = nets # add list of network objects to return dict

        except TypeError:
          raise ServerInfoError("host \"%s\" not found" % host)
        except:
          raise ServerInfoError("something horrible happened")

        return ret
