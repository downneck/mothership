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
supports the listing of various types of DB data
"""

# imports 

from sqlalchemy import or_, desc, MetaData
from mothership_models import *

def list_all_values(cfg, listing, quiet=False):
    """
    [description]
    lists all values of a given type 

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        listing: the type of data to search for and display
    optional:
        quiet: suppress the printing of the info header and just dump data 

    [return value]
    returns an integer representing the next available UID
    """

    avail = [ 'ip', 'ips', 'vlan', 'vlans', 'role', 'roles', 'group', 'groups', 'user', 'users' ]
    if listing not in avail:
        print 'Unsupported listing for: %s' % listing
        print 'Please specify one of the following:\n\t%s' % '\n\t'.join(avail)
        return
    if listing == 'vlan' or listing == 'vlans':
        vlist = []
        for result in cfg.dbsess.query(Network.vlan).\
            filter(Network.vlan!=0).\
            order_by(Network.vlan).\
            distinct().all():
                vlist.append(result.vlan)
        print '\n'.join(map(str, vlist))
    elif listing == 'ip' or listing == 'ips':
        for net in cfg.dbsess.query(Network).order_by(Network.ip):
            if net.ip != '0.0.0.0' and net.ip != None:
                print net.ip
    elif listing == 'role' or listing == 'roles':
        for role in cfg.dbsess.query(Role):
          print role.name
    elif listing == 'group' or listing == 'groups':
        if not quiet:
            print "GID, Group Name, Location"
            print "--------------------------------------------------"
        for g in cfg.dbsess.query(Groups):
            print "%s %s %s.%s" % (g.gid, g.groupname, g.realm, g.site_id)
    elif listing == 'user' or listing == 'users':
        if not quiet:
            print "UID, User Name, Location"
            print "--------------------------------------------------"
        for u in cfg.dbsess.query(Users):
            print "%s %s %s.%s" % (u.uid, u.username, u.realm, u.site_id)
