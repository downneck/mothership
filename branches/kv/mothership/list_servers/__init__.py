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
import mothership
import sys
import mothership.kv
from mothership.mothership_models import *
from sqlalchemy import or_, desc, MetaData

# list_servers takes a parameter to search by and, optionally a tag
# then prints all servers it finds in the db
def list_servers(cfg, listby=None, lookfor=None):
    """
    [description]
    prints a list of all servers found for a given parameter 

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        listby: what parameter to list by (vlan, site_id, etc.)
        lookfor: filter to apply to the parameter 
        (ie. to look in vlan 105, listby=vlan lookfor=105) 

    [return value]
    no explicit return 
    """

    # list servers by vlan
    if listby == 'vlan':
      if lookfor == None:
        print "you must supply a name with the -n flag"
        sys.exit(1)
      else:
        for serv, net in cfg.dbsess.query(Server, Network).\
        filter(Network.ip!=None).\
        filter(Network.vlan==lookfor).\
        filter(Server.id==Network.server_id).\
        order_by(Server.hostname):
          print "%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id)

    # list servers by site_id
    elif listby == 'site_id':
      if lookfor == None:
        print "you must supply a name with the -n flag"
        sys.exit(1)
      else:
        for serv in cfg.dbsess.query(Server).\
        filter(Server.site_id==lookfor).\
        order_by(Server.hostname):
            print "%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id)

    # list servers by tag
    elif listby == 'tag':
      if lookfor == None:
        print "you must supply a tag with the -r flag"
        sys.exit(1)
      else:
        servers_primary = []
        for server in cfg.dbsess.query(Server).\
        filter(Server.tag==lookfor).\
        order_by(Server.hostname):
          servers_primary.append(server)
        servers_kv = []
        kvs = mothership.kv.collect(cfg, None, key='tag')
        for i in kvs:
           namespace,key = str(i).split(' ')
           if key == "tag="+lookfor:
             servers_kv.append(i.hostname+"."+i.realm+"."+i.site_id)
           else:
             pass
        if servers_primary:
          for serv in servers_primary:
            print "%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id)
        elif servers_kv:
          for serv in servers_kv:
            print serv
        else:
          pass

    # list servers by realm 
    elif listby == 'realm':
      if lookfor == None:
        print "you must supply a realm with the -R flag"
        sys.exit(1)
      else:
        for serv in cfg.dbsess.query(Server).\
        filter(Server.realm==lookfor).\
        order_by(Server.hostname):
          print "%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id)


    # list servers by manufacturer
    elif listby == 'manufacturer': 
      if lookfor == None:
        print "you must supply a manufacturer with the -m flag"
        sys.exit(1)
      else:
        search_string = '%' + lookfor + '%'
        for serv, hw in cfg.dbsess.query(Server, Hardware).\
        filter(Hardware.manufacturer.like(search_string)).\
        filter(Server.hw_tag==Hardware.hw_tag).\
        order_by(Server.hostname):
            print "%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id)

    # list servers by model name
    elif listby == 'model':
      if lookfor == None:
        print "you must supply a model with the -M flag"
        sys.exit(1)
      else:
        search_string = '%' + lookfor + '%'
        for serv, hw in cfg.dbsess.query(Server, Hardware).\
        filter(Hardware.model.like(search_string)).\
        filter(Server.hw_tag==Hardware.hw_tag).\
        order_by(Server.hostname):
            print "%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id)

    # list servers by cores
    elif listby == 'cores':
      if lookfor.isdigit():
        print "you must supply a number with the -C flag"
        sys.exit(1)
      else:
        for serv in cfg.dbsess.query(Server).\
        filter(Server.cores==lookfor).\
        order_by(Server.hostname):
            print "%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id)

    # list servers by ram
    elif listby == 'ram':
      if lookfor.isdigit():
        print "you must supply a number with the -a flag"
        sys.exit(1)
      else:
        for serv in cfg.dbsess.query(Server).\
        filter(Server.ram==lookfor).\
        order_by(Server.hostname):
            print "%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id)

    # list servers by disk
    elif listby == 'disk':
      if lookfor.isdigit():
        print "you must supply a number with the -d flag"
        sys.exit(1)
      else:
        for serv in cfg.dbsess.query(Server).\
        filter(Server.disk==lookfor).\
        order_by(Server.hostname):
            print "%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id)

    # list servers by hw_tag
    elif listby == 'hw_tag':
      if lookfor == None:
        print "you must supply a hardware tag with the -H flag"
        sys.exit(1)
      else:
        for serv in cfg.dbsess.query(Server).\
        filter(Server.hw_tag==lookfor):
          print "%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id)


    # list servers by virtual
    elif listby == 'virtual':
      for serv in cfg.dbsess.query(Server).\
      filter(Server.virtual==True).\
      order_by(Server.hostname):
          print "%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id)

    # list servers by physical
    elif listby == 'physical':
      for serv in cfg.dbsess.query(Server).\
      filter(Server.virtual==False).\
      order_by(Server.hostname):
          print "%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id)

    # list servers by name 
    elif listby == 'name':
      if lookfor == None:
        print "you must supply a name with the -n flag"
        sys.exit(1) 
      else:
        search_string = '%' + lookfor + '%'
        for serv in cfg.dbsess.query(Server).\
        filter(Server.hostname.like(search_string)).\
        order_by(Server.hostname):
            print "%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id)

    # list all servers by default
    else:
      for serv in cfg.dbsess.query(Server).order_by(Server.hostname):
          print "%s.%s.%s" % (serv.hostname, serv.realm, serv.site_id)

