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
mothership.zeus_cluster

This module allows us to track information for and interact
with zeus zxtm clusters
"""

# imports
import mothership
import mothership.network_mapper
from sqlalchemy import or_, desc, MetaData
from mothership.mothership_models import *

def list_zeus_cluster_records_via_ip(cfg, ip, port=False):
    """
    [description]
    lists zeus cluster records for a given ip

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        ip: the ip we're interested in
    optional:
        port: restrict the search to particular port

    [return value]
    returns a list of db row ids if successful, false if unsuccessful
    """

    idlist = {}
    q = cfg.dbsess.query(ZeusCluster).\
        filter(or_(ZeusCluster.ip==ip,
        ZeusCluster.public_ip==ip))
    if port:
        q = q.filter(ZeusCluster.port==port)
    for d in q.all():
        rec = mothership.remove_method_keys(d.__dict__)
        idlist[str(rec['id'])] = rec
        print '%d)' % rec['id'],
        for key in sorted(rec):
            if key != 'id':
                print '%s=%s' % (key, rec[key]),
        print
    return idlist

def manage(cfg, opts, args):
    if mothership.count_nonempty_args(opts.__dict__, boolean=True) != 1:
        print 'zeus_cluster can/must specify only ONE action: add, delete, update.  Action aborted'
        return
    if opts.add:
        if mothership.count_nonempty_args(args) < 5:
            print 'zeus_cluster add MUST at least specify the first 5 arguments'
            return
        # make sure the cluster_name is valid
        zc_members = [ z.value for z in cfg.dbsess.query(KV.value).\
            filter(KV.key=='zc_member').order_by(KV.value).distinct().all() ]
        if args[0] not in zc_members:
            print '%s is not a valid zeus_cluster entry' % args[0]
            print 'The cluster_name should be one of the following:\n\t%s' \
                % '\n\t'.join(zc_members)
            return
        # Test that the new entry has no conflicts before adding
        data = manage_conflicts(cfg, args)
        if data:
            print 'Adding zeus_cluster entry for: %s' % ' '.join(args)
            cfg.dbconn.execute(ZeusCluster.__table__.insert(), [ data ])
        else:
            print 'zeus_cluster add aborted!'
        return
    if opts.delete:
        if mothership.count_nonempty_args(args) != 2:
            print 'zeus_cluster delete MUST specify TWO arguments'
            return
        idlist = list_zeus_cluster_records_via_ip(cfg, *tuple(args[0:2]))
        if len(idlist.keys()) == 0:
            print 'No entries in zeus_cluster matching ip address %s port %s' \
                % tuple(args[0:2])
            return
        elif len(idlist.keys()) == 1:
            ans = idlist.keys()[0]
            print 'Only one entry matches ip %s' % args[0]
        else:
            ans = raw_input('Which ID do you wish to delete? ')
            if ans not in idlist.keys():
                print 'Delete zeus_cluster entry aborted.'
                return
        # Confirm with user before acting
        choice = ans
        print '\nTo confirm the deletion of zeus_cluster id %s' % choice
        ans = raw_input('Please type "delete_%s": ' % choice)
        if ans != 'delete_%s' % choice:
            print 'Delete zeus_cluster id %s aborted.' % choice
            return
        print 'Deleting zeus_cluster entry %d' % int(choice)
        cfg.dbconn.execute(ZeusCluster.__table__.delete().\
             where(ZeusCluster.id==int(choice)))
    if opts.update:
        if mothership.count_nonempty_args(opts.__dict__) < 2:
            print 'zeus_cluster update requires as least one option'
            return
        idlist = list_zeus_cluster_records_via_ip(cfg, args[0])
        if len(idlist.keys()) == 0:
            print 'No entries in zeus_cluster matching ip address %s' % args[0]
            return
        elif len(idlist.keys()) == 1:
            ans = idlist.keys()[0]
            print 'Only one entry matches ip %s' % args[0]
        else:
            ans = raw_input('Which ID do you wish to modify? ')
            if ans not in idlist.keys():
                print 'Modify zeus_cluster entry aborted.'
                return
        choice = ans
        # update the specified keys
        change = False
        for key in idlist[choice].keys():
            if key in opts.__dict__ and opts.__dict__[key]:
                if idlist[choice][key] != opts.__dict__[key]:
                    idlist[choice][key] = opts.__dict__[key]
                    change = True
        if not change:
            print 'Changes are identical to current id %s entry' % choice
            print 'Modify zeus_cluster entry aborted.'
            return
        # Confirm with user before acting
        print '\nModifying id %s to the following:' % choice
        # then display them all again
        print '%d)' % idlist[choice]['id'],
        for key in sorted(idlist[choice]):
            if key != 'id':
                print '%s=%s' % (key, idlist[choice][key]),
        print
        ans = raw_input('Please type "modify_%s": ' % choice)
        if ans != 'modify_%s' % choice:
            print 'Modify zeus_cluster id %s aborted.' % choice
            return
        print 'Modifying zeus_cluster entry %d' % int(choice)
        del idlist[choice]['id']
        cfg.dbconn.execute(ZeusCluster.__table__.update().\
            where(ZeusCluster.id==choice), [ idlist[choice] ])

def manage_conflicts(cfg, args):
    # To avoid having to manually create a dict, use a keylist
    # to keep the args in a certain index order
    data = {}
    keylist = [ 'cluster_name', 'vhost', 'port', 'tg_name', 'ip', 'public_ip' ]
    for a in args:
        data[keylist[args.index(a)]] = a

    # Ensure that all values are unique
    for d in cfg.dbsess.query(ZeusCluster).\
        filter(ZeusCluster.cluster_name==args[0]).all():
        match = 0
        for k in keylist:
            if keylist.index(k) > 4: continue  # do not compare fields after 'ip'
            if str(data[k]) == str(d.__dict__[k]):
                match += 1
        if match >= 5:
            print 'An entry matching (%s) already exists' % ' '.join(args[0:5])
            return False

    # Ensure that the public_ip, if specified, does not match multiple
    # ips
    if len(args) > 5:
        if mothership.network_mapper.remap(cfg, 'ip', ip=args[5]):
            print 'Invalid RFC1918 public_ip specified: %s' % args[5]
            return False
        for d in cfg.dbsess.query(ZeusCluster).\
            filter(ZeusCluster.public_ip==data['public_ip']).\
            filter(ZeusCluster.ip!=data['ip']).all():
                print 'public_ip %s already exists, associated with a different ip: %s' \
                    % (d.public_ip, d.ip)
                return False

    # Ensure that the cluster does not contain more than one ip/port
    # pair
    for d in cfg.dbsess.query(ZeusCluster).\
        filter(ZeusCluster.cluster_name==data['cluster_name']).\
        filter(ZeusCluster.port==data['port']).\
        filter(ZeusCluster.ip==data['ip']).all():
            print 'ip:port %s:%s already exists in cluster: %s' % \
                (d.ip, d.port, d.cluster_name)
            return False

    # Ensure that the ip does not span multiple clusters or tg_names
    for d in cfg.dbsess.query(ZeusCluster).\
        filter(or_(ZeusCluster.tg_name!=data['tg_name'],
        ZeusCluster.cluster_name!=data['cluster_name'])).\
        filter(ZeusCluster.ip==data['ip']).all():
            print 'ip cannot exist in more than one cluster_name or tg_name'
            print 'Currently, cluster "%s" contains a "%s" traffic group on ip %s' \
                % (d.cluster_name, d.tg_name, d.ip)
            return False

    # If all is kosher, return the dict to be manipulated
    return data
