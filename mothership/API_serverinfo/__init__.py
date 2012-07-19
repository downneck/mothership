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

import mothership.API_kv
import mothership.validate
from mothership.common import *
from mothership.mothership_models import *

from sqlalchemy import or_, desc, MetaData


class ServerInfoError(Exception):
    pass


class API_serverinfo:

    def __init__(self, cfg):
        self.common = MothershipCommon(cfg)
        self.cfg = cfg
        self.version = 1 # the version of this module
        self.namespace = 'API_serverinfo' # class' namespace
        self.metadata = { # the metadata dict, communicates to the outside world what we're capable of
            'config': { # some basic module-wide config data
                'shortname': 'si', # shortened class name (for CLI)
                'description': 'retrieves critical information about a server',
                'module_dependencies': { # what other modules do we depend on?
                    'API_kv': 1, # a module, and its minimum accepted version
                    'mothership_models': 1, # another module, and its minimum accepted version
                    'common': 1, # another module, and its minimum accepted version
                    'validate': 1, # another module, and its minimum accepted version
                },
            },
            'methods': { # a dict of methods we're presenting to the outside world (public only!)
                'si': { # a method identifier
                    'description': 'retrieve server info for a server identified by hostname.realm.site_id', # duh
                    'rest_type': 'GET', # the REST method we want to use for this call: GET, POST, PUT, DELETE
                    'admin_only': False, # if True, you must authenticate with the admin user/pass defined in the yaml
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
                            'unqdn': { # an arg
                                'vartype': 'string', # its type
                                'desc': 'search for an unqdn (hostname.realm.site_id)', # its description
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

    def _get_host_from_hwtag(self, key):
        try:
            s = self.cfg.dbsess.query(Server).\
                filter(Server.hw_tag==key).\
                filter(Server.virtual==False).first()
            if s:
                return self._get_serverinfo(s.hostname, s.realm, s.site_id)
        except TypeError:
            self.cfg.log.debug("Something wrong happened in _get_host_from_hwtag. please re-run test")
            self.cfg.dbsess.rollback()
            raise ServerInfoError("API_serverinfo/_get_host_from_hwtag: no host found with hw_tag: %s" % key)

    def _get_host_from_ip(self, key):
        # try the private ip
        try:
            s, n = self.cfg.dbsess.query(Server, Network).\
                   filter(Server.id==Network.server_id).\
                   filter(Network.ip==key).first()
            if s.hostname:
                return self._get_serverinfo(s.hostname, s.realm, s.site_id)
        except TypeError:
            self.cfg.log.debug("_get_host_from_ip couldn't find host via private ip")
        # try the public ip
        try:
            s, n = self.cfg.dbsess.query(Server, Network).\
                   filter(Server.id==Network.server_id).\
                   filter(Network.public_ip==key).first()
            if s.hostname:
                return self._get_serverinfo(s.hostname, s.realm, s.site_id)
        except TypeError:
            self.cfg.log.debug("_get_host_from_ip was not able to find the host via the public ip")
        # if we've made it this far without finding anyone...
        self.cfg.dbsess.rollback()
        raise ServerInfoError("API_serverinfo/_get_host_from_ip: no host found with public or private ip: %s" % key)

    def _get_host_from_mac(self, key):
        try:
            h, s = self.cfg.dbsess.query(Network, Server).\
                   filter(Network.hw_tag==Server.hw_tag).\
                   filter(Network.mac==key).\
                   filter(Server.virtual==False).first()
            if s.hostname:
                return self._get_serverinfo(s.hostname, s.realm, s.site_id)
        except TypeError:
            self.cfg.log.debug("_get_host_from_mac was not able to find an hostname")
            self.cfg.dbsess.rollback()
            raise ServerInfoError("API_serverinfo/_get_host_from_mac: no host found with MAC address: %s" % key)

    def _get_host_from_unqdn(self, key):
        try:
            s = mothership.validate.v_get_server_obj(self.cfg, key)
            if s:
                if type(s) == list:
                    self.cfg.log.debug("API_serverinfo/_get_host_from_unqdn: hostname not unique enough")
                    raise ServerInfoError("API_serverinfo/_get_host_from_unqdn: hostname not unique enough")
                self.cfg.log.debug("API_serverinfo/_get_host_from hostname (validate): %s.%s.%s" % (s.hostname, s.realm, s.site_id))
                return self._get_serverinfo(s.hostname, s.realm, s.site_id)
        except Exception, e:
            self.cfg.log.debug("API_serverinfo/_get_host_from_unqdn was not able to find a hostname")
            self.cfg.dbsess.rollback()
            raise ServerInfoError("API_serverinfo/_get_host_from_unqdn: no host found with name: %s. Error: %s" % (key, e))

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
        metadata = self.metadata
        ret = None

        maxargs = metadata['methods']['si']['optional_args']['max']
        minargs = metadata['methods']['si']['optional_args']['min']

        if not self.common.check_max_num_args(len(query), metadata['methods']['si']['optional_args']['max']):
            retval = "API_serverinfo: too many queries! max number of queries is: %s. You passed: %s" % (maxargs, len(query))
            cfg.log.debug(retval)
            raise ServerInfoError(retval)

        if not self.common.check_min_num_args(len(query), metadata['methods']['si']['optional_args']['min']):
            retval = "API_serverinfo: not enough queries! min number of queries is: %s. You passed: %s" % (self.metadata['methods']['si']['optional_args']['min'], len(query))
            cfg.log.debug(retval )
            raise ServerInfoError(retval)

        retval = "API_serverinfo: num queries: %s " % len(query)
        retval += "API_serverinfo: max num queries: %s" % metadata['methods']['si']['optional_args']['max']
        cfg.log.debug(retval)

        keys = query.keys()
        for key  in keys:
            if key == 'hw_tag':
                ret = self._get_host_from_hwtag(query[key])
                break
            if key == 'ip':
                ret = self._get_host_from_ip(query[key])
                break
            if key == 'unqdn':
                ret = self._get_host_from_unqdn(query[key])
                break
            if key == 'mac':
                ret = self._get_host_from_mac(query[key])
                break

        if ret:
            return ret
        else:
            cfg.log.debug("API_serverinfo/si: no host found!") 
            raise ServerInfoError("API_serverinfo/si: no host found!")

    def _get_serverinfo(self, host, realm, site_id):
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
          cfg.log.debug("_get_serverinfo(): %s" % s.to_dict())
          ret['hardware'] = h.to_dict() # add hardware object to return dict
          cfg.log.debug("_get_serverinfo(): %s " % h.to_dict())

          # kv entries
          for h2, s2 in cfg.dbsess.query(Hardware, Server).\
          filter(Server.hostname==host).\
          filter(Server.realm==realm).\
          filter(Server.site_id==site_id).\
          filter(Hardware.hw_tag==Server.hw_tag):
            fqdn = '.'.join([host,realm,site_id])

          ret['kv'] = []
          kvobj = mothership.API_kv.API_kv(cfg)
          kquery = {'unqdn': fqdn, 'key': 'tag',}
          for kv in kvobj.collect(kquery):
              ret['kv'].append(kv)
              cfg.log.debug("_get_serviceinfo(): %s " % kv)

          # network entries
          for n in cfg.dbsess.query(Network).\
                  filter(Server.id==Network.server_id).\
                  filter(Server.hostname==s.hostname).\
                  order_by(Network.interface).all():
              nets.append(n.to_dict()) # add network objects to our list
              cfg.log.debug("_get_serverinof(): %s " %  n.to_dict())
          ret['network'] = nets # add list of network objects to return dict

        except TypeError:
            self.cfg.dbsess.rollback()
            raise ServerInfoError("host \"%s\" not found" % host)
        except Exception, e:
            self.cfg.dbsess.rollback()
            raise ServerInfoError("something horrible happened. Error: %s" % e)

        return dict(ret)
