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
mothership.validate

a library of validation methods
for various types of data
"""

# imports
import base64
import struct
import types
import re

# All of the models and sqlalchemy are brought in
# to simplify referencing
from mothership.mothership_models import *

class ValidationError(Exception):
    pass

# Validates domain input data
def v_domain(cfg, domain):
    """
    [description]
    validates domain input data (probably not necessary)

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        domain: the domain we're trying to validate

    [return value]
    True/False based on success of validation
    """

    if domain == cfg.domain:
        return True
    else:
        raise ValidationError("validate/v_domain: invalid domain: %s" % domain) 


# Validates ssh2 pubkeys
def v_ssh2_pubkey(key):
    """
    [description]
    validates ssh2 public keys

    [parameter info]
    required:
        key: the ssh2 public key we're trying to validate

    [return value]
    True/Exception based on success of validation
    """
    try:
        DSA_KEY_ID="ssh-dss"
        RSA_KEY_ID="ssh-rsa"
    
        if re.match(DSA_KEY_ID+'|'+RSA_KEY_ID, key):
            k = key.split(' ')
        else:
            raise ValidationError("validate/v_ssh2_pubkey: invalid ssh2 key: %s" % key)
    
        if k:
            try:
                data = base64.decodestring(k[1])
            except IndexError:
                raise ValidationError("validate/v_ssh2_pubkey: invalid ssh2 key: %s" % key)
            int_len = 4
            str_len = struct.unpack('>I', data[:int_len])[0] # this should return 7
            if DSA_KEY_ID in key:
              if data[int_len:int_len+str_len] == DSA_KEY_ID:
                  return True
              else:
                  raise ValidationError("validate/v_ssh2_pubkey: invalid ssh2 key: %s" % key) 
            else:
                if data[int_len:int_len+str_len] == RSA_KEY_ID:
                  return True
                else:
                  raise ValidationError("validate/v_ssh2_pubkey: invalid ssh2 key: %s" % key)
        else:
           raise ValidationError("validate/v_ssh2_pubkey: invalid ssh2 key: %s" % key) 
    except Exception, e:
        raise ValidationError("validate/v_ssh2_pubkey: invalid ssh2 key: %s" % key)

# Validates UNIX uids
def v_uid(cfg, uid):
    """
    [description]
    validates UNIX UIDs

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        uid: the UID we're trying to validate

    [return value]
    True/False based on success of validation
    """

    if type(uid) == types.IntType:
        if uid >= cfg.uid_start and uid <= cfg.uid_end:
            return True
        else:
            cfg.log.debug("UID is outside the allowed range (%s to %s)" % (cfg.uid_start, cfg.uid_end))
            raise ValidationError("UID is outside the allowed range (%s to %s)" % (cfg.uid_start, cfg.uid_end))
    elif uid == None:
        cfg.log.debug("UID is empty!")
        raise ValidationError("UID is empty!")
    else:
        cfg.log.debug("UID must be an integer!")
        raise ValidationError("UID must be an integer!")

# Looks for a UID in the db and returns true if present, false if absent
def v_uid_in_db(cfg, uid, realm, site_id):
    """
    [description]
    looks for a UID in the db

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        uid: the UID we're trying to find
        realm: the realm we're trying to find it in
        site_id: the site_id we're trying to find it in

    [return value]
    True/False based on success of validation
    """

    uidlist = []
    u = cfg.dbsess.query(Users).\
        filter(Users.realm==realm).\
        filter(Users.site_id==site_id).all()
    for userentry in u:
        uidlist.append(userentry.uid)
    uid_set = set(uidlist)
    if uid in uid_set:
        return True
    else:
        return False

# Looks for a GID in the db and returns true if present, false if absent
def v_gid_in_db(cfg, gid, realm, site_id):
    """
    [description]
    looks for a GID in the db

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        gid: the GID we're looking for
        realm: the realm we're trying to find it in
        site_id: the site_id we're trying to find it in

    [return value]
    returns an integer representing the GID if the GID is in the db
    returns False if the GID is not in the db
    """

    gidlist = []
    g = cfg.dbsess.query(Groups).\
        filter(Groups.realm==realm).\
        filter(Groups.site_id==site_id).all()
    for groupentry in g:
        gidlist.append(groupentry.gid)
    gid_set = set(gidlist)
    if gid in gid_set:
        return True
    else:
        return False

# Validates UNIX gids
def v_gid(cfg, gid):
    """
    [description]
    validates UNIX GIDs

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        gid: the GID we're trying to validate

    [return value]
    True/False based on success of validation
    """

    if type(gid) == types.IntType:
        if gid >= cfg.gid_start and gid <= cfg.gid_end:
            return True
        else:
            print "GID is outside the allowed range (%s to %s)" % (cfg.gid_start, cfg.gid_end)
            return False
    elif gid == None:
        return False
    else:
        print "GID must be an integer!"
        return False


# deprecated in API rewrite
#
# get an unqualified or fully-qualified name (host or user)
# for either servers or users
#def v_get_fqn(cfg, name):
#    """
#    [description]
#    get an unqualified or fully-qualified name (host or user) for either servers or users. depending on what we're supplied with it will either return a fqn or present the user with a menu to pick the unqn and then return a fqn
#
#    [parameter info]
#    required:
#        cfg: the config object. useful everywhere
#        name: the user/group name we're fetching the fqn for OR part of an unqualified name
#
#    [return value]
#    returns a fully-qualified user/group name if we're supplied with a name
#    returns an un-qualified name if we're not supplied with a name
#    """
#
#    count = 1
#    select = {}
#    sub = name.split('.')
#    # if we got a fully-qualified name/hostname
#    if len(sub) == 5:
#        n = sub[0]
#        r = sub[1]
#        s = sub[2]
#        d = sub[3]+'.'+sub[4]
#        # check to see if the domain is valid
#        if not v_domain(cfg, d):
#            raise ValidationError("invalid domain \"%s\", aborting" % d)
#        # check to see if the site_id is valid
#        if not v_site_id(cfg, s):
#            raise ValidationError("invalid site_id \"%s\", aborting" % s)
#        # check to see if the realm is valid
#        if not v_realm(cfg, r):
#            raise ValidationError("invalid realm \"%s\", aborting" % r)
#        # if everything is valid, fire back name.realm.site_id.domain
#        return n+'.'+r+'.'+s+'.'+d
#    # if we got everything but the name
#    elif len(sub) == 4:
#        r = sub[0]
#        s = sub[1]
#        d = sub[2]+'.'+sub[3]
#        # check to see if the domain is valid
#        if not v_domain(cfg, d):
#            raise ValidationError("invalid domain \"%s\", aborting" % d)
#        # check to see if the site_id is valid
#        if not v_site_id(cfg, s):
#            raise ValidationError("invalid site_id \"%s\", aborting" % s)
#        # check to see if the realm is valid
#        if not v_realm(cfg, r):
#            raise ValidationError("invalid realm \"%s\", aborting" % r)
#        # if everything is valid, fire back realm.site_id.domain
#        return r+'.'+s+'.'+d
#    # 3 items could be either site_id.domain.tld or name.realm.site_id
#    # let's figure out which it is...
#    elif len(sub) == 3:
#        s = sub[0]
#        d = sub[1]+'.'+sub[2]
#        n = sub[0]
#        r = sub[1]
#        sid = sub[2]
#        # validate the domain
#        if not v_domain(cfg, d):
#            # if the domain is invalid, maybe it's a realm.site_id
#            if not v_realm(cfg, r) and not v_site_id(cfg, sid):
#                raise ValidationError("invalid domain \"%s\" or realm.site_id \"%s.%s\", aborting" % (d, r, s))
#            # check both again to make sure both are valid
#            elif v_realm(cfg, r) and v_site_id(cfg, sid):
#                # we only have one domain configured, tack it on and
#                # fire back name.realm.site_id.domain
#                return n+'.'+r+'.'+sid+'.'+cfg.domain
#            # both domain and one of either realm or site_id is bad
#            else:
#                raise ValidationError("site_id \"%s\" or realm \"%s\" info is bad, aborting" % (s, r))
#        # if we got site_id.domain.tld, and the domain checks out
#        # validate the site_id
#        elif not v_site_id(cfg, s):
#            raise ValidationError("invalid site_id \"%s\", aborting" % s)
#        # if the site_id and domain check out, present the user with a
#        # menu to pick the realm 
#        else:
#            menu = ''
#            for realm in cfg.realms:
#                menu += str(count)+') '+realm+'.'+s+'.'+d+'\n'
#                select[count] = realm+'.'+s+'.'+d
#                count += 1
#            menu += "Please select the one you would like to use: "
#            ans = raw_input(menu)
#            if not ans or int(ans) < 1 or int(ans) > count:
#                raise ValidationError("selection aborted")
#            else:
#                # return the fqn without the name 
#                return select[int(ans)]
#    # if we got two items, it could be either domain.tld or
#    # realm.site_id, let's find out which...
#    elif len(sub) == 2:
#        d = sub[0]+'.'+sub[1]
#        r = sub[0]
#        s = sub[1]
#        # validate the domain
#        if not v_domain(cfg, d):
#            # if it's not a domain, validate the realm and site_id
#            if not v_realm(cfg, r) and not v_site_id(cfg, s):
#                raise ValidationError("entry was not a realm.site_id or domain.tld, aborting")
#            # we only have one domain configured, tack it on
#            else:
#                return r+'.'+s+'.'+cfg.domain
#        # if we got a valid domain, present the user with a menu
#        # to pick the realm and site_id
#        else:
#            menu = "\nMultiple options found for %s:\n-----------------------\n" % name
#            for realm in cfg.realms:
#                for site_id in cfg.site_ids:
#                    menu += str(count)+') '+realm+'.'+site_id+'.'+d+'\n'
#                    select[count] = realm+'.'+site_id+'.'+d
#                    count += 1
#            menu += "Please select the one you would like to use: "
#            ans = raw_input(menu)
#            if not ans or int(ans) < 1 or int(ans) > count:
#                raise ValidationError("selection aborted")
#            else:
#                return select[int(ans)]
#    # if we only got one item, it's gotta be a name/hostname.
#    # present the user with a menu to pick everything
#    elif len(sub) == 1:
#        menu = "\nMultiple options found for \"%s\":\n-----------------------\n" % name
#        for realm in cfg.realms:
#            for site_id in cfg.site_ids:
#                menu += str(count)+') '+realm+'.'+site_id+'.'+cfg.domain+'\n'
#                select[count] = realm+'.'+site_id+'.'+cfg.domain
#                count += 1
#        menu += "Please select the one you would like to use: "
#        ans = raw_input(menu)
#        if not ans or int(ans) < 1 or int(ans) > count:
#            raise ValidationError("selection aborted")
#        else:
#            # return the fully-qualified name, only if we were supplied
#            # a name to begin with
#            return sub[0]+'.'+select[int(ans)]
#    # if we got input that's too long, let the user know then bail
#    elif len(sub) > 5:
#        print sub
#        raise ValidationError("name.realm.site_id.domain.tld is the maximum length of a name")
#    # if we got some sort of wierd (zero-length, probably) input, blow up.
#    else:
#        raise ValidationError("get_fqn() called incorrectly!")


def v_split_unqn(unqn):
    """
    [description]
    split a unqn into realm, site_id, domain
    this assumes you've validated the unqn first

    [parameter info]
    required:
        unqn: the fully-qualified or unqualified name we're splitting

    [return value]
    returns three fields, populated or unpopulated, depending on what the unqdn had 
    """
    if not unqn:
        raise ValidationError("validate/v_split_unqn: refusing to split an empty unqn") 
    parts = unqn.split(".")
    return [None] * (3 - len(parts)) + parts[0:3]


# split a fqn into realm, site_id, domain
# this assumes you've validated the fqn first
def v_split_fqn(fqn):
    """
    [description]
    split a fqn into realm, site_id, domain
    this assumes you've validated the fqn first

    [parameter info]
    required:
        fqn: the fully-qualified or unqualified name we're splitting

    [return value]
    returns a fully-qualified user/group name if we're supplied with a name
    returns an un-qualified name if we're not supplied with a name
    """

    if not fqn:
        raise ValidationError("split_fqn() called with no fqn!")
    else:
        f = fqn.split('.')
        # if we got a fully-qualified name (5 items), return all items
        if len(f) == 5:
            return f[0], f[1], f[2], f[3]+'.'+f[4]
        # if we got just realm.site_id.domain
        elif len(f) == 4:
            return f[0], f[1], f[2]+'.'+f[3]
        # if we get anything else, blow up
        else:
            raise ValidationError("v_split_fqn() called incorrectly")


# find out if a realm.site_id is in the Server table 
def v_unqn_in_servers(cfg, realm, site_id):
    """
    [description]
    looks for realm and site_id in the Server table

    [parameter info]
    required:
        cfg: the almighty config object. useful everywhere
        realm: the realm we're looking for
        site_id: the site_id we're looking for

    [return value]
    True/False based on success/failure
    """

    v_site_id(cfg, site_id)
    v_realm(cfg, realm)

    # gather realm, site_id data
    d = cfg.dbsess.query(Server).\
    filter(Server.realm==realm).\
    filter(Server.site_id==site_id).first()

    if d:
        return True
    else:
        raise ValidationError("validate/v_unqn_in_servers: realm.site_id valid but not instantiated: %s.%s" % (realm, site_id)) 


# find out if a realm.site_id is in the Users table
def v_unqn_in_users(cfg, realm, site_id):
    """
    [description]
    looks for realm and site_id in the Users table

    [parameter info]
    required:
        cfg: the almighty config object. useful everywhere
        realm: the realm we're looking for
        site_id: the site_id we're looking for

    [return value]
    True/False based on success/failure
    """

    v_site_id(cfg, site_id)
    v_realm(cfg, realm)

    # gather realm, site_id data
    d = cfg.dbsess.query(Users).\
    filter(Users.realm==realm).\
    filter(Users.site_id==site_id).first()

    if d:
        return True
    else:
        raise ValidationError("validate/v_unqn_in_users: realm.site_id valid but not instantiated: %s.%s" % (realm, site_id)) 


# find out if a realm.site_id is in the Groups table
def v_unqn_in_groups(cfg, realm, site_id):
    """
    [description]
    looks for realm and site_id in the Groups table

    [parameter info]
    required:
        cfg: the almighty config object. useful everywhere
        realm: the realm we're looking for
        site_id: the site_id we're looking for

    [return value]
    True/False based on success/failure
    """

    v_site_id(cfg, site_id)
    v_realm(cfg, realm)

    # gather realm, site_id data
    d = cfg.dbsess.query(Groups).\
    filter(Groups.realm==realm).\
    filter(Groups.site_id==site_id).first()

    if d:
        return True
    else:
        raise ValidationError("validate/v_unqn_in_groups: realm.site_id valid but not instantiated: %s.%s" % (realm, site_id)) 


# find out if a realm.site_id is in the KV table
def v_unqn_in_kv(cfg, realm, site_id):
    """
    [description]
    looks for realm and site_id in the KV table

    [parameter info]
    required:
        cfg: the almighty config object. useful everywhere
        realm: the realm we're looking for
        site_id: the site_id we're looking for

    [return value]
    True/False based on success/failure
    """

    v_site_id(cfg, site_id)
    v_realm(cfg, realm)

    # gather realm, site_id data
    d = cfg.dbsess.query(KV).\
    filter(KV.realm==realm).\
    filter(KV.site_id==site_id).first()

    if d:
        return True
    else:
        raise ValidationError("validate/v_unqn_in_kv: realm.site_id valid but not instantiated: %s.%s" % (realm, site_id)) 


# find out if a realm.site_id is in the dns_addendum table
def v_unqn_in_dns_addendum(cfg, realm, site_id):
    """
    [description]
    looks for realm and site_id in the DnsAddendum table

    [parameter info]
    required:
        cfg: the almighty config object. useful everywhere
        realm: the realm we're looking for
        site_id: the site_id we're looking for

    [return value]
    True/False based on success/failure
    """

    v_site_id(cfg, site_id)
    v_realm(cfg, realm)

    # gather realm, site_id data
    d = cfg.dbsess.query(DnsAddendum).\
    filter(DnsAddendum.realm==realm).\
    filter(DnsAddendum.site_id==site_id).first()

    if d:
        return True
    else:
        raise ValidationError("validate/v_unqn_in_dns_addendum: realm.site_id valid but not instantiated: %s.%s" % (realm, site_id)) 


# will have to move this into the API_user/group module when it exists
#def v_get_user_obj(cfg, username):
#    """
#    [description]
#    user names can be passed to functions in several ways, sometimes containing realm and/or site_id information. this function takes arbitrary input and parses it, then calls v_user_picker() to select a user object from the database and returns it.
#
#    [parameter info]
#    required:
#        cfg: the config object. useful everywhere
#        username: the username we want to parse
#
#    [return value]
#    returns a Users object
#    """
#    # create a list of all the users with this name in the db
#    # we explicitly use the list function because the return behaves
#    # differently depending on the number of user instances in the db
#    # just one instance returns a user object, more than one returns a
#    # list of user objects so we force it to be a list in either case
#    f = username.split('.')
#    if len(f) == 1:
#        u = list(cfg.dbsess.query(Users).\
#        filter(Users.username==username))
#    elif len(f) > 1:
#        # validate/construct/get the realm.site_id.domain data
#        fqun = v_get_fqn(cfg, name=username)
#        username, realm, site_id, domain = v_split_fqn(fqun)
#        fqn = realm+'.'+site_id+'.'+domain
#        u = list(cfg.dbsess.query(Users).\
#        filter(Users.username==username).\
#        filter(Users.realm==realm).\
#        filter(Users.site_id==site_id))
#    else:
#        raise ValidationError("v_get_user_obj() called incorrectly")
#
#    if u:
#        u = v_user_picker(cfg, u)
#        if u:
#            return u
#        else:
#            raise ValidationError("something has gone terribly wrong in the v_get_user_obj() function")
#    else:
#        return None 


# will have to move this into the API_user/group module when it exists
#def v_get_group_obj(cfg, groupname):
#    """
#    [description]
#    group names can be passed to functions in several ways, sometimes containing realm and/or site_id information. this function takes arbitrary input and parses it, then calls v_group_picker() to select a group object from the database and returns it.
#
#    [parameter info]
#    required:
#        cfg: the config object. useful everywhere
#        groupname: the groupname we want to parse
#
#    [return value]
#    returns a Groups object
#    """
#    # create a list of all the groups with this name in the db
#    # we explicitly use the list function because the return behaves
#    # differently depending on the number of group instances in the db
#    # just one instance returns a group object, more than one returns a
#    # list of group objects
#    f = groupname.split('.')
#    if len(f) == 1:
#        g = list(cfg.dbsess.query(Groups).\
#        filter(Groups.groupname==groupname))
#    elif len(f) > 1:
#        # validate/construct/get the realm.site_id.domain data
#        fqgn = v_get_fqn(cfg, name=groupname)
#        groupname, realm, site_id, domain = v_split_fqn(fqgn)
#        fqn = realm+'.'+site_id+'.'+domain
#        g = list(cfg.dbsess.query(Groups).\
#        filter(Groups.groupname==groupname).\
#        filter(Groups.realm==realm).\
#        filter(Groups.site_id==site_id))
#    else:
#        raise ValidationError('v_get_group_obj() called incorrectly')
#
#    if g:
#        g = v_group_picker(cfg, g)
#        if g:
#            return g
#        else:
#            raise ValidationError('something has gone terribly wrong in the v_get_group_obj() function')
#    else:
#        return None 


# leaving this for now, will have to move this into the API_server module when it exists
def v_get_server_obj(cfg, unqdn):
    """
    [description]
    gets a server object from the server table based on unqdn 

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        unqdn: the unqdn of the server we want to fetch

    [return value]
    returns a Servers object or raises an error
    """
    # get the realm.site_id.domain data
    hostname, realm, site_id = v_split_unqn(unqdn)
    if hostname:
        v_name(hostname)
        v_realm(cfg, realm)
        v_site_id(cfg, site_id)
    else:
        raise ValidationError("validate/v_get_server_obj: incomplete unqdn (no hostname!): %s" % unqdn)
    h = cfg.dbsess.query(Server).\
    filter(Server.hostname==hostname).\
    filter(Server.realm==realm).\
    filter(Server.site_id==site_id).first()

    if h:
        return h
    else:
        raise ValidationError("validate/v_get_server_obj: no object found for: %s" % unqdn)


# deprecated completely in API rewrite
#
#def v_parse_name(cfg, username=None, groupname=None, hostname=None):
#    """
#    this function is deprecated. please stop using it 
#    """
#
#    raise ValidationError("v_parse_name() is deprecated. please use one of the following:\nv_get_user_obj()\nv_get_group_obj()\nv_get_host_obj()")


# deprecated in API rewrite
#
# User picker, used in the event we need to present the operator with a
# menu of multiple user entries. this takes a list of Users objects
# used mainly by parse_name() to pick user/group entries
#def v_user_picker(cfg, u):
#    """
#    [description]
#    used in the event we need to present the operator with a menu of multiple user entries. used mainly by parse_name() to pick user/group entries. returns a Users object
#
#    [parameter info]
#    required:
#        cfg: the config object. useful everywhere
#        u: list of Users objects to pick from
#
#    [return value]
#    returns a Users object
#    """
#
#    if len(u) == 1:
#        # if we only get one, return it
#        return u[0]
#    elif len(u) > 1:
#        count = 1
#        menu = "\nUser found in multiple areas"
#        if count <= len(u):
#            for user in u:
#                menu += '\n%s) %s.%s.%s' % (count, user.username, user.realm, user.site_id)
#                count += 1
#            menu += "\nPlease pick one: "
#            ans = raw_input(menu)
#            if not ans or int(ans) < 1 or int(ans) > count:
#                raise ValidationError('invalid selection, aborting')
#            else:
#                # set the user object...this creeps me out, but works -dk
#                u = u[int(ans)-1]
#        if u:
#            return u
#        else:
#            raise ValidationError('oops, something went wrong in user_picker()!')
#    else:
#        raise ValidationError('user_picker() called with zero-length user list')


# deprecated in API rewrite
#
# Group picker, used in the event we need to present the operator with a
# menu of multiple group entries. this takes a list of Groups objects
# used mainly by parse_name() to pick user/group entries
#def v_group_picker(cfg, g):
#    """
#    [description]
#    used in the event we need to present the operator with a menu of multiple group entries. used mainly by parse_name() to pick user/group entries. returns a Groups object
#
#    [parameter info]
#    required:
#        cfg: the config object. useful everywhere
#        g: list of Groups objects to pick from
#
#    [return value]
#    returns a Groups object
#    """
#
#    if len(g) == 1:
#        # if we only get one, return it
#        return g[0]
#    elif len(g) >1:
#        count = 1
#        menu = "\nGroup found in multiple areas"
#        if count <= len(g):
#            for group in g:
#                menu += '\n%s) %s.%s.%s' % (count, group.groupname, group.realm, group.site_id)
#                count += 1
#            menu += "\nPlease pick one: "
#            ans = raw_input(menu)
#            if not ans or int(ans) < 1 or int(ans) > count:
#                raise ValidationError('invalid selection, aborting')
#            else:
#                # set the group object...this creeps me out, but works -dk
#                g = g[int(ans)-1]
#        if g:
#            return g
#        else:
#            raise ValidationError('oops, something went wrong in v_group_picker()!')
#    else:
#        raise ValidationError('v_group_picker() called with zero-length group list')


# deprecated in API rewrite
#
# Host picker, used in the event we need to present the operator with a
# menu of multiple host entries. this takes a list of Server objects
# used mainly by parse_name() to pick host entries
#def v_host_picker(cfg, h):
#    """
#    [description]
#    used in the event we need to present the operator with a menu of multiple host entries. used mainly by parse_name() to pick user/host entries. returns a Server object
#
#    [parameter info]
#    required:
#        cfg: the config object. useful everywhere
#        g: list of Server objects to pick from
#
#    [return value]
#    returns a Server object
#    """
#
#    if len(h) == 1:
#        # if we only get one, return it
#        return h[0]
#    elif len(h) >1:
#        count = 1
#        menu = "\nHost found in multiple areas"
#        if count <= len(h):
#            for host in h:
#                menu += '\n%s) %s.%s.%s' % (count, host.hostname, host.realm, host.site_id)
#                count += 1
#            menu += "\nPlease pick one: "
#            ans = raw_input(menu)
#            if not ans or int(ans) < 1 or int(ans) > count:
#                raise ValidationError('invalid selection, aborting')
#            else:
#                # set the host object...this creeps me out, but works -dk
#                h = h[int(ans)-1]
#        if h:
#            return h
#        else:
#            raise ValidationError('oops, something went wrong in v_host_picker()!')
#    else:
#        raise ValidationError('v_host_picker() called with zero-length host list')


# VERY basic validation of user- group- or host-name input
def v_name(name):
    """
    [description]
    VERY basic validation of user- group- or host-name input
    """

    if not name:
        raise ValidationError('v_name() called without a name!')
    if re.search("[^A-Za-z0-9_\-.]", name):
        raise ValidationError('name contains illegal characters! allowed characters are: A-Z a-z 0-9 _ - .')
    if len(name) < 1:
        raise ValidationError('too short! name must have more than 1 character')
    return True

# very basic validation of site_id
def v_site_id(cfg, site_id):
    """
    [description]
    very basic validation of site_id

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        site_id: the site_id we're validating

    [return value]
    returns true if valid, raises an exception if not
    """

    if not site_id in cfg.site_ids:
        raise ValidationError("site_id is not valid: %s" % site_id)
    else:
        return True

# very basic validation of realm
def v_realm(cfg, realm):
    """
    [description]
    very basic validation of realm

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        realm: the realm we're validating

    [return value]
    returns true if valid, raises an exception if not
    """

    if not realm in cfg.realms:
        raise ValidationError("realm is not valid: %s" % realm)
    else:
        return True
