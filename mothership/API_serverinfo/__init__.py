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
    mothership.API_serverinfo

    Collects and displays information about servers
"""

# import some modules
import sys
import yaml
import mothership
import mothership.kv
import mothership.validate
from mothership.common import *
from mothership.mothership_models import *
from sqlalchemy import or_, desc, MetaData

class ServerInfoError(Exception):
    pass


class API_serverinfo:

    def __init__(self, cfg):
        self.common = MothershipCommon()
        self.cfg = cfg
        self.log = MothershipLogger(self.cfg)
        self.version = 1 # the version of this module
        self.namespace = 'API_serverinfo' # class' namespace
        self.metadata = { # the metadata dict, communicates to the outside world what we're capable of
            'config': { # some basic module-wide config data
                'shortname': 'si', # shortened class name (for CLI)
                'description': 'retrieves critical information about a server',
                'module_dependencies': { # what other modules do we depend on?
                    'kv': 1, # a module, and its minimum accepted version
                    'mothership_models': 1, # another module, and its minimum accepted version
                },
            },
            'methods': { # a dict of methods we're presenting to the outside world (public only!)
                'si': { # a method identifier
                    'description': 'retrieve server info for a server identified by hostname.realm.site_id', # duh
                    'rest_type': 'GET', # the REST method we want to use for this call: GET, POST, PUT, DELETE
                    'required_args': { # dict of info about arguments we just can't live without
                    },
                    'optional_args': { # dict holding optional argument info
                        'min': 1, # minimum number of optional args we'll accept
                        'max': 1, # maximum number of optional args we'll accept
                        'args': { # the argument definitions themselves
                            'hw_tag': { # an arg
                                'vartype': 'string', # its type
                                'desc': 'search for a hw_tag (hardware tag)', # its description
                                'ol': 'w', # the one-letter designation for this option (ie -w)
                            },
                            'ip': { # an arg
                                'vartype': 'string', # its type
                                'desc': 'search for an ip (public or private)', # its description
                                'ol': 'i', # the one-letter designation for this option (ie -w)
                            },
                            'mac': { # an arg
                                'vartype': 'string', # its type
                                'desc': 'search for a MAC address', # its description
                                'ol': 'm', # the one-letter designation for this option (ie -w)
                            },
                            'hostname': { # an arg
                                'vartype': 'string', # its type
                                'desc': 'search for a hostname', # its description
                                'ol': 'n', # the one-letter designation for this option (ie -w)
                            },
                        },
                    },
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

    def __get_host_from_hwtag(self, key):
        try:
            s = self.cfg.dbsess.query(Server).\
                filter(Server.hw_tag==key).\
                filter(Server.virtual==False).first()
            if s.hostname:
                ret = self.__get_serverinfo(s.hostname, s.realm, s.site_id)
            return ret
        except TypeError:
            raise ServerInfoError("API_serverinfo/get_host: no host found with hw_tag: %s" % key)

    def __get_host_from_ip(self, key):
        # try the private ip
        try:
            s, n = self.cfg.dbsess.query(Server, Network).\
                   filter(Server.id==Network.server_id).\
                   filter(Network.ip==key).first()
            if s.hostname:
                ret = self.__get_serverinfo(s.hostname, s.realm, s.site_id)
            return ret
        except TypeError:
            pass
        # try the public ip
        try:
            s, n = cfg.dbsess.query(Server, Network).\
                   filter(Server.id==Network.server_id).\
                   filter(Network.public_ip==key).first()
            if s.hostname:
                ret = self.__get_serverinfo(s.hostname, s.realm, s.site_id)
        except TypeError:
            raise ServerInfoError("API_serverinfo/get_host: no host found with public or private ip: %s" % key)

    def __get_host_from_mac(self, key):
        try:
            h, s = self.cfg.dbsess.query(Network, Server).\
                   filter(Network.hw_tag==Server.hw_tag).\
                   filter(Network.mac==key).\
                   filter(Server.virtual==False).first()
            if s.hostname:
                ret = self.__get_serverinfo(s.hostname, s.realm, s.site_id, cfg.debug)
            return ret
        except TypeError:
            raise ServerInfoError("API_serverinfo/get_host: no host found with MAC address: %s" % key)

    def __get_host_from_hostname(self, key):
        try:
            # this won't work with our RESTness
            #unqdn = mothership.validate.v_get_fqn(cfg, name=query['hostname'])
            #
            s = mothership.validate.v_get_host_obj(self.cfg, key)
            if self.cfg.debug:
                self.log.debug(s)
            ret = self.__get_serverinfo(s.hostname, s.realm, s.site_id)
            return ret
        except Exception, e:
            raise ServerInfoError("API_serverinfo/get_host: no host found with name: %s. Error: %s" % (key, e))

    def si(self, query):
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
        cm = self.common
        metadata = self.metadata
        ret = None

        maxargs = metadata['methods']['si']['optional_args']['max']
        minargs = metadata['methods']['si']['optional_args']['min']

        if not cm.check_max_num_args(len(query), metadata['methods']['si']['optional_args']['max']):
            if cfg.debug:
                retval = "API_serverinfo: too many queries! max number of queries is: %s. You passed: %s" % (maxargs, len(query))
                self.log.debug(retval)
            raise ServerInfoError(retval)

        if not cm.check_min_num_args(len(query), metadata['methods']['si']['optional_args']['min']):
            if cfg.debug:
                retval = "API_serverinfo: not enough queries! min number of queries is: %s. You passed: %s" % (self.metadata['methods']['si']['optional_args']['min'], len(query))
                self.log.debug(retval )
            raise ServerInfoError(retval)

        if cfg.debug:
            retval = "API_serverinfo: num queries: %s " % len(query)
            retval += "API_serverinfo: max num queries: %s" % metadata['methods']['si']['optional_args']['max']
            self.log.debug(retval)

        keys = query.keys()
        for key  in keys:
            if key == 'hw_tag':
                ret = self.__get_host_from_hwtag(query[key])
                break
            if key == 'ip':
                ret = __get_host_from_ip(query[key])
                break
            if key == 'hostname':
                ret = self.__get_host_from_hostname(query['hostname'])
                break
            if key == 'mac':
                ret =__get_host_from_mac(query[key])
                break

        if ret:
            return ret
        else:
            if cfg.debug:
                self.log.debug("API_serverinfo/si: return value \"ret\" is empty!")
            raise ServerInfoError("API_serverinfo/si: return value\"ret\" is empty!")

    def __get_serverinfo(self, host, realm, site_id):
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
        except Exception, e:
          raise ServerInfoError("something horrible happened. Error: %s" % e)

        return dict(ret)
