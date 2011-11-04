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
from mothership.mothership_models import *

def list_all_values(cfg, listing, quiet=False, sort=False):
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

    avail = [ 'ip', 'ips', 'vlan', 'vlans', 'tag', 'tags', 'group', 'groups', 'user', 'users' ]
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
        return vlist
        # print '\n'.join(map(str, vlist))
    elif listing == 'ip' or listing == 'ips':
        for net in cfg.dbsess.query(Network).order_by(Network.ip):
            ips = []
            if net.ip != '0.0.0.0' and net.ip != None:
                ips.append(net.ip)
            return ips
                # print net.ip
    elif listing == 'tag' or listing == 'tags':
        tags = []
        for tag in cfg.dbsess.query(Tag):
          tags.append(tag.name)
	tags = sorted(tags)
        return tags
        # for tag in tags:
	#   print tag
    elif listing == 'group' or listing == 'groups':
        groups = []
	for g in cfg.dbsess.query(Groups):
            groupid = []
            groupid.append(g.gid)
            groupid.append(g.groupname)
            groupid.append(g.realm)
            groupid.append(g.site_id)
	    groups.append(groupid)
        return groups
	# if sort == 'id':
	#   groups = sorted(groups, key=lambda group:group[0])
        # elif sort == 'name':
	#   groups = sorted(groups, key=lambda group:group[1])
	# if not quiet:
        #     print "GID, Group Name, Location"
        #     print "--------------------------------------------------"
        # for g in groups:
    	#     print "%-5s\t%-26s\t%s.%s" % (g[0], g[1], g[2], g[3]) 
    elif listing == 'user' or listing == 'users':
        users = []
        for u in cfg.dbsess.query(Users):
            user = []
            user.append(u.uid)
            user.append(u.username)
            user.append(u.realm)
            user.append(u.site_id)
            users.append(user)
        return users
        # if not quiet:
        #     print "UID, User Name, Location"
        #     print "--------------------------------------------------"
        # if sort == 'id':
	#     users = sorted(users, key=lambda user:user[0])
	# elif sort == 'name':
	#     users = sorted(users, key=lambda user:user[1])
        # for u in users:    
	#     print "%-5s\t%-26s\t%s.%s" % (u[0], u[1], u[2], u[3])
