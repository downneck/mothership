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
this module holds methods for dealing with LDAP
this should only, generally speaking, be used to talk with an LDAP server
all user interaction should be done in the mothership.users module
"""

# imports
import os
import ldap
import mothership.validate
import mothership.users
import mothership.kv

# db imports
from mothership.mothership_models import *

class LDAPError(Exception):
    pass

# figure out what ldap server to talk to
def get_master(cfg, realm_path):
    """
    [description]
    looks up the ldap master for a given realm_path

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        realm_path: the realm path we need a server for. format is realm.site_id

    [return value]
    returns the fqdn for the ldap master server in this realm_path
    """

    fqn = mothership.validate.v_get_fqn(cfg, realm_path)
    realm, site_id, domain = mothership.validate.v_split_fqn(fqn)

    serv = None

    try:
        serv = str(mothership.kv.select(cfg, realm_path, key='ldap_master_server')).split('=')[1]
    except:
        pass 

    return serv


def ld_connect(cfg, ldap_master, realm, site_id):
    """
    [description]
    open a connection to the ldap master

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        ldap_master: the master ldap server to use 

    [return value]
    returns the open ldap connection object 
    """

    d = cfg.domain.split('.')

    admin_cn = str(mothership.kv.select(cfg, ldap_master, key="ldap_admin_cn")).split('=')[1]
    admin_pass = str(mothership.kv.select(cfg, ldap_master, key="ldap_admin_pass")).split('=')[1]
    admin_dn = "cn=%s,dc=%s,dc=%s,dc=" % (admin_cn, realm, site_id)
    admin_dn += ',dc='.join(d)
    ld_server_string = "ldap://"+ldap_master
    # init the connection to the ldap server
    try:
        ldcon = ldap.initialize(ld_server_string)
        ldcon.simple_bind_s(admin_dn, admin_pass)
    except ldap.LDAPError:
        print "error connecting to ldap server: %s" % ldap_master
        print "INFO DUMP:\n"
        print "admin_dn: %s\nadmin_pass: %s\nld_server_string: %s" % (admin_dn, admin_pass, ld_server_string)
        print "\nLDAP Messages:\n"

    return ldcon


def uadd(cfg, username):
    """
    [description]
    add a user to ldap

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the username to add

    [return value]
    no explicit return 
    """

    # get user object
    u = mothership.validate.v_get_user_obj(cfg, username)
    # an array made of the domain parts.
    d = cfg.domain.split('.')

    if u:
        if not u.active:
            raise LDAPError("user %s is not active. please set the user active, first." % u.username)
        # get ldap master info
        ldap_master = get_master(cfg, u.realm+'.'+u.site_id)
    else:
        raise LDAPError("user \"%s\" not found, aborting" % username)

    # create a connection to the ldap master
    ldcon = ld_connect(cfg, ldap_master, u.realm, u.site_id)

    dn = "uid=%s,ou=%s,dc=%s,dc=%s,dc=" % (u.username, cfg.ldap_users_ou, u.realm, u.site_id)
    dn += ',dc='.join(d)
    # stitch together the LDAP, fire it into the ldap master server 
    try:
        add_record = [('objectclass', ['inetOrgPerson','person','ldapPublicKey','posixAccount'])]
        full_name = u.first_name + " " + u.last_name
        if u.ssh_public_key:
            attributes = [('cn', u.username),
                          ('sn', u.last_name),
                          ('gecos', full_name),
                          ('uid', u.username),
                          ('uidNumber', str(u.uid)),
                          ('gidNumber', cfg.ldap_default_gid),
                          ('homeDirectory', u.hdir),
                          ('loginShell', u.shell),
                          ('mail', u.email),
                          ('sshPublicKey', u.ssh_public_key),
                         ]
        else:
            attributes = [('cn', u.username),
                          ('sn', u.last_name),
                          ('gecos', full_name),
                          ('uid', u.username),
                          ('uidNumber', str(u.uid)),
                          ('gidNumber', cfg.ldap_default_gid),
                          ('homeDirectory', u.hdir),
                          ('loginShell', u.shell),
                          ('mail', u.email),
                         ]
        add_record += attributes
        print "adding ldap user entry for %s" % (u.username+'.'+u.realm+'.'+u.site_id)
        ldcon.add_s(dn, add_record)
    except ldap.LDAPError, e:
        print dn
        print add_record
        print u.username+'.'+u.realm+'.'+u.site_id
        udisplay(cfg, u.username+'.'+u.realm+'.'+u.site_id) 
        raise LDAPError(e)

    # close the LDAP connection
    ldcon.unbind()


def uremove(cfg, username):
    """
    [description]
    remove a user

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the user to remove 

    [return value]
    no explicit return
    """

    # get user object
    u = mothership.validate.v_get_user_obj(cfg, username)
    # an array made of the domain parts.
    d = cfg.domain.split('.')

    if u:
        # get ldap master info, stitch together some dn info
        ldap_master = get_master(cfg, u.realm+'.'+u.site_id)
        dn = "uid=%s,ou=%s,dc=%s,dc=%s,dc=" % (u.username, cfg.ldap_users_ou, u.realm, u.site_id)
        dn += ',dc='.join(d)
    else:
        raise LDAPError("user \"%s\" not found, aborting" % username)

    ldcon = ld_connect(cfg, ldap_master, u.realm, u.site_id)

    try:
        ldcon.delete_s(dn)
        ldcon.unbind()
    except ldap.LDAPError, e:
        raise LDAPError(e)


def urefresh(cfg, realm_path):
    """
    [description]
    refresh the LDAP users database. drop all users, add them back in again

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        realm_path: realm.site_id to operate in

    [return value]
    no explicit return
    """

    fqn = mothership.validate.v_get_fqn(cfg, realm_path)
    realm, site_id, domain = mothership.validate.v_split_fqn(fqn)
    # an array made of the domain parts.
    d = cfg.domain.split('.')
    dnlist = []
    userlist = []
    ldap_master = get_master(cfg, realm+'.'+site_id)

    dn ="ou=%s,dc=%s,dc=%s,dc=" % (cfg.ldap_users_ou, realm, site_id)
    dn += ',dc='.join(d)
    ldcon = ld_connect(cfg, ldap_master, realm, site_id)
    search = '(objectClass=person)'
    try:
        for result in ldcon.search_s(dn, ldap.SCOPE_SUBTREE, search):
            dnlist.append(result[0])
    except:
        print "No existing user records found for dn: %s" % dn

    print "This command will completely wipe out all forms of life in the ldap database on %s" % ldap_master
    ans = raw_input("to completely refresh the ldap database type \"refresh_%s\": " % ldap_master)

    if ans != "refresh_%s" % ldap_master:
        raise LDAPError("aborted by user input")

    for user in cfg.dbsess.query(Users).\
    filter(Users.realm==realm).\
    filter(Users.site_id==site_id).\
    filter(Users.active==True).all():
        userlist.append(user.username+'.'+realm+'.'+site_id)

    if dnlist:
        for dn in dnlist:
            ldcon.delete_s(dn)
    for user in userlist:
        uadd(cfg, user)

    print "Users database has been dropped and refreshed using Mothership data."

def udisplay(cfg, username):
    """
    [description]
    display a user's ldap info

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the user to display

    [return value]
    no explicit return
    """

    # get user object
    u = mothership.validate.v_get_user_obj(cfg, username)
    # an array made of the domain parts.
    d = cfg.domain.split('.')

    if u:
        # get ldap master info, stitch together some dn info
        ldap_master = get_master(cfg, u.realm+'.'+u.site_id)
        dn = "uid=%s,ou=%s,dc=%s,dc=%s,dc=" % (u.username, cfg.ldap_users_ou, u.realm, u.site_id)
        dn += ',dc='.join(d)
    else:
        raise LDAPError("user \"%s\" not found, aborting" % username)

    ldcon = ld_connect(cfg, ldap_master, u.realm, u.site_id)

    try:
        raw_res = ldcon.search_s(dn, ldap.SCOPE_BASE)
        print raw_res 
        ldcon.unbind()
    except ldap.LDAPError, e:
        #print "User \"%s\" not found in the directory on %s" % (u.username, ldap_master)
        raise LDAPError(e)


def uupdate(cfg, username):
    """
    [description]
    update a user entry

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the user to update

    [return value]
    no explicit return 
    """

    # get user object
    u = mothership.validate.v_get_user_obj(cfg, username)
    # an array made of the domain parts.
    d = cfg.domain.split('.')

    if u:
        if not u.active:
            raise LDAPError("user %s is not active. please set the user active, first." % u.username)
        # get ldap master info
        ldap_master = get_master(cfg, u.realm+'.'+u.site_id)
    else:
        raise LDAPError("user \"%s\" not found, aborting" % username)

    # create a connection to the ldap master
    ldcon = ld_connect(cfg, ldap_master, u.realm, u.site_id)

    dn = "uid=%s,ou=%s,dc=%s,dc=%s,dc=" % (u.username, cfg.ldap_users_ou, u.realm, u.site_id)
    dn += ',dc='.join(d)
    # stitch together the LDAP, fire it into the ldap master server 
    try:
        full_name = u.first_name + " " + u.last_name
        mod_record = [(ldap.MOD_REPLACE, 'sn', u.last_name),
                      (ldap.MOD_REPLACE, 'gecos', full_name),
                      (ldap.MOD_REPLACE, 'uidNumber', str(u.uid)),
                      (ldap.MOD_REPLACE, 'homeDirectory', u.hdir),
                      (ldap.MOD_REPLACE, 'loginShell', u.shell),
                      (ldap.MOD_REPLACE, 'mail', u.email),
                      (ldap.MOD_REPLACE, 'sshPublicKey', u.ssh_public_key),
                     ]
        ldcon.modify_s(dn, mod_record)
    except ldap.LDAPError, e:
        raise LDAPError(e)

    # close the LDAP connection
    ldcon.unbind()


def gadd(cfg, groupname):
    """
    [description]
    add a group

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        groupname: the group to add

    [return value]
    no explicit return 
    """

    # get group object
    g = mothership.validate.v_get_group_obj(cfg, groupname)
    # an array made of the domain parts.
    d = cfg.domain.split('.')

    if g:
        # get ldap master info
        ldap_master = get_master(cfg, g.realm+'.'+g.site_id)
        # construct the list of users in this group
        userlist = []
        for ugmap in cfg.dbsess.query(UserGroupMapping).\
                filter(UserGroupMapping.groups_id==g.id):
            user = cfg.dbsess.query(Users).\
            filter(Users.id==ugmap.users_id).first()
            userlist.append(user.username)
    else:
        raise LDAPError("group \"%s\" not found, aborting" % groupname)

    # create a connection to the ldap_master server
    ldcon = ld_connect(cfg, ldap_master, g.realm, g.site_id)
    # stitch together the LDAP, fire it into the ldap master server 
    dn = "cn=%s,ou=%s,dc=%s,dc=%s,dc=" % (g.groupname, cfg.ldap_groups_ou, g.realm, g.site_id)
    dn += ',dc='.join(d)
    try:
        add_record = [('objectClass', ['top', 'posixGroup'])]
        if userlist:
            attributes = [('description', g.description),
                          ('cn', g.groupname),
                          ('gidNumber', str(g.gid)),
                          ('memberUid', userlist),
                         ]
        else:
            attributes = [('description', g.description),
                          ('cn', g.groupname),
                          ('gidNumber', str(g.gid)),
                         ]
        add_record += attributes
        print "adding ldap group record for %s" % (g.groupname+'.'+g.realm+'.'+g.site_id)
        ldcon.add_s(dn, add_record)
    except ldap.LDAPError, e:
        raise LDAPError(e)

    # close the LDAP connection
    ldcon.unbind()


def gupdate(cfg, groupname):
    """
    [description]
    update a group

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        groupname: the group to update 

    [return value]
    no explicit return 
    """

    # get group object
    g = mothership.validate.v_get_group_obj(cfg, groupname)
    # an array made of the domain parts.
    d = cfg.domain.split('.')

    if g:
        # get ldap master info
        ldap_master = get_master(cfg, g.realm+'.'+g.site_id)
        # construct the list of users in this group
        userlist = []
        for ugmap in cfg.dbsess.query(UserGroupMapping).\
        filter(UserGroupMapping.groups_id==g.id):
            user = cfg.dbsess.query(Users).\
            filter(Users.id==ugmap.users_id).first()
            userlist.append(user.username)
    else:
        raise LDAPError("group \"%s\" not found, aborting" % groupname)

    # create a connection to the ldap_master server
    ldcon = ld_connect(cfg, ldap_master, g.realm, g.site_id)

    # stitch together the LDAP, fire it into the ldap master server 
    dn = "cn=%s,ou=%s,dc=%s,dc=%s,dc=" % (g.groupname, cfg.ldap_groups_ou, g.realm, g.site_id)
    dn += ',dc='.join(d)
    try:
        mod_record = [(ldap.MOD_REPLACE, 'description', g.description),
                      (ldap.MOD_REPLACE, 'gidNumber', str(g.gid)),
                      (ldap.MOD_REPLACE, 'memberUid', userlist),
                     ]
        ldcon.modify_s(dn, mod_record)
    except ldap.LDAPError, e:
        raise LDAPError(e)

    # close the LDAP connection
    ldcon.unbind()


def gremove(cfg, groupname):
    """
    [description]
    remove a group

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        groupname: the group to remove 

    [return value]
    no explicit return 
    """

    # get group object
    g = mothership.validate.v_get_group_obj(cfg, groupname)
    # an array made of the domain parts.
    d = cfg.domain.split('.')

    if g:
        # get ldap master info, stitch together some dn info
        ldap_master = get_master(cfg, g.realm+'.'+g.site_id)
        dn = "cn=%s,ou=%s,dc=%s,dc=%s,dc=" % (g.groupname, cfg.ldap_groups_ou, g.realm, g.site_id)
        dn += ',dc='.join(d)
    else:
        raise LDAPError("group \"%s\" not found, aborting" % groupname)

    ldcon = ld_connect(cfg, ldap_master, g.realm, g.site_id)

    try:
        ldcon.delete_s(dn)
        ldcon.unbind()
    except ldap.LDAPError, e:
        raise LDAPError(e)


def grefresh(cfg, realm_path):
    """
    [description]
    refresh the LDAP groups database. drop all groups, add them back in again


    [parameter info]
    required:
        cfg: the config object. useful everywhere
        realm_path: the realm.site_id to refresh

    [return value]
    no explicit return 
    """

    fqn = mothership.validate.v_get_fqn(cfg, realm_path)
    realm, site_id, domain = mothership.validate.v_split_fqn(fqn)
    # an array made of the domain parts.
    d = cfg.domain.split('.')

    dnlist = []
    grouplist = []
    ldap_master = get_master(cfg, realm+'.'+site_id)
    dn ="ou=%s,dc=%s,dc=%s,dc=" % (cfg.ldap_groups_ou, realm, site_id)
    dn += ',dc='.join(d)
    ldcon = ld_connect(cfg, ldap_master, realm, site_id)
    search = '(objectClass=posixGroup)'

    try:
        for result in ldcon.search_s(dn, ldap.SCOPE_SUBTREE, search):
            dnlist.append(result[0])
    except:
        print "No existing group records found for dn: %s" % dn

    print "This command will completely wipe out all groups in the ldap database on %s" % ldap_master
    ans = raw_input("to completely refresh the groups in the ldap database type \"refresh_%s\": " % ldap_master)

    if ans != "refresh_%s" % ldap_master:
        raise LDAPError("aborted by user input")

    for group in cfg.dbsess.query(Groups).\
    filter(Groups.realm==realm).\
    filter(Groups.site_id==site_id).all():
        grouplist.append(group.groupname+'.'+realm+'.'+site_id)

    for dn in dnlist:
        ldcon.delete_s(dn)
    for group in grouplist:
        gadd(cfg, group)

    print "groups database has been dropped and refreshed using Mothership data."


def gdisplay(cfg, groupname):
    """
    [description]
    display a group's ldap info

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        groupname: the group to display 

    [return value]
    no explicit return 
    """

    # get group object
    g = mothership.validate.v_get_group_obj(cfg, groupname)
    # an array made of the domain parts.
    d = cfg.domain.split('.')

    if g:
        # get ldap master info, stitch together some dn info
        ldap_master = get_master(cfg, g.realm+'.'+g.site_id)
        dn = "cn=%s,ou=%s,dc=%s,dc=%s,dc=" % (g.groupname, cfg.ldap_groups_ou, g.realm, g.site_id)
        dn += ',dc='.join(d)
    else:
        raise LDAPError("group \"%s\" not found, aborting" % groupname)

    ldcon = ld_connect(cfg, ldap_master, g.realm, g.site_id)

    try:
        raw_res = ldcon.search_s(dn, ldap.SCOPE_BASE)
        print raw_res
        ldcon.unbind()
    except ldap.LDAPError, e:
        raise LDAPError(e)


def ldapimport(cfg, realm_path):
    """
    [description]
    import ldap data into mothership (DANGEROUS)
    in fact this is so dangerous, i'm leaving
    it unlinked in ship for the moment.

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        realm_path: the realm.site_id to import

    [return value]
    no explicit return 
    """

    fqn = mothership.validate.v_get_fqn(cfg, realm_path)
    realm, site_id, domain = mothership.validate.v_split_fqn(fqn)
    # an array made of the domain parts.
    d = cfg.domain.split('.')

    ldap_master = get_master(cfg, realm+'.'+site_id)
    dn ="ou=%s,dc=%s,dc=%s,dc=" % (cfg.ldap_groups_ou, realm, site_id)
    dn += ',dc='.join(d)
    ldcon = ld_connect(cfg, ldap_master, realm, site_id)
    search = '(objectClass=posixGroup)'
    attr = ['memberUid', 'gidNumber', 'description', 'cn']
    # fetch all groups from the ldap master db
    # we do groups first since they include member info which we can use
    # to create users from. user entries don't contain any group info
    for result in ldcon.search_s(dn, ldap.SCOPE_SUBTREE, search, attr):
        # for groups with members in them, pop the members in a userlist
        if result[1].has_key('memberUid'):
            userlist = result[1]['memberUid']
        else:
            userlist = None
        groupname = result[1]['cn'][0]+'.'+fqn
        # let's see if the group exists already in mothership
        g = mothership.validate.v_get_group_obj(cfg, groupname)
        if g:
            # if the group exists, update its info with what's in ldap
            print "group \"%s\" exists, updating with info from ldap" % (groupname)
            g.description = result[1]['description'][0]
            g.gid = int(result[1]['gidNumber'][0])
            cfg.dbsess.add(g)
            cfg.dbsess.commit()
            # now that the group is updated, let's map users to it
            # (if there are any users in the group)
            if userlist:
                for user in userlist:
                    username = user+'.'+fqn
                    u = mothership.validate.v_get_user_obj(cfg, username)
                    if u:
                        ugmap = cfg.dbsess.query(UserGroupMapping).\
                        filter(UserGroupMapping.groups_id==g.id).\
                        filter(UserGroupMapping.users_id==u.id).first()
                        if ugmap:
                            print "User-to-group mapping exists for %s in %s, skipping" % (u.username, g.groupname)
                        else:
                            print "mapping user \"%s\" into group \"%s\"" % (u.username+'.'+fqn, groupname+'.'+fqn)
                            ugmap = UserGroupMapping(g.id, u.id)
                            cfg.dbsess.add(ugmap)
                            cfg.dbsess.commit()
                    else:
                        # fetch user info from ldap, stuff into new
                        # user, map user into group
                        dn = "uid=%s,ou=%s,dc=%s,dc=%s,dc=" % (user, cfg.ldap_users_ou, realm, site_id)
                        dn += ',dc='.join(d)
                        search = '(objectClass=person)'
                        print "fetching user data for: %s" % dn
                        try:
                            result = ldcon.search_s(dn, ldap.SCOPE_BASE, search)
                        except ldap.LDAPError, e:
                            print "Entity not found, skipping."
                            print e
                            result = False
                        if result:
                            print "user \"%s\" does not exist, creating from ldap info and mapping into group \"%s\"" % (user+'.'+fqn, groupname+'.'+fqn)
                            # pull the user data out of the ldap schema
                            username = result[0][1]['uid'][0]
                            if result[0][1]['sshPublicKey']:
                                ssh_public_key = result[0][1]['sshPublicKey'][0]
                            else:
                                ssh_public_key = None
                            uid = result[0][1]['uidNumber'][0]
                            first_name, last_name = result[0][1]['gecos'][0].split(None, 1)
                            hdir = result[0][1]['homeDirectory'][0]
                            shell = result[0][1]['loginShell'][0]
                            email = result[0][1]['mail'][0]
                            # ldap doesn't store user type data so
                            # use the default type
                            user_type = cfg.def_user_type
                            # create a new user object and fire it into
                            # the db, face first.
                            u = Users(first_name, last_name, ssh_public_key, username, site_id, realm, uid, user_type, hdir, shell, email, True)
                            cfg.dbsess.add(u)
                            cfg.dbsess.commit()
                            # map the user we just created into the
                            # group we're currently operating on
                            ugmap = UserGroupMapping(g.id, u.id)
                            cfg.dbsess.add(ugmap)
                            cfg.dbsess.commit()
                        else:
                            print "User \"%s\" not created. The user is in a group in LDAP but does not actually exist in LDAP.\nMost likely this is a system user (such as \"nobody\" or \"apache\") that should not exist in LDAP." % user
        # if the group doesn't exist, create it then map any users it
        # may have into the mothership group definition
        else:
            groupname = result[1]['cn'][0]
            print "group \"%s\" does not exist, creating from ldap info" % (groupname+'.'+fqn)
            description = result[1]['description']
            gid = int(result[1]['gidNumber'][0])
            g = Groups(description, groupname, site_id, realm, gid)
            cfg.dbsess.add(g)
            cfg.dbsess.commit()
            if userlist:
                for user in userlist:
                    u = mothership.validate.v_get_user_obj(cfg, user+'.'+fqn)
                    if u:
                        print "mapping user \"%s\" into group \"%s\"" % (u.username+'.'+fqn, groupname+'.'+fqn)
                        ugmap = UserGroupMapping(g.id, u.id)
                        cfg.dbsess.add(ugmap)
                        cfg.dbsess.commit()
                    else:
                        # fetch user info from ldap, stuff into new
                        # user, map user into group
                        dn = "uid=%s,ou=%s,dc=%s,dc=%s,dc=" % (user, cfg.ldap_users_ou, realm, site_id)
                        dn += ',dc='.join(d)
                        search = '(objectClass=person)'
                        try:
                            result = ldcon.search_s(dn, ldap.SCOPE_BASE, search)
                        except ldap.LDAPError, e:
                            print "Entity not found, skipping."
                            print e
                            result = False
                        if result:
                            # pull the user data out of the ldap schema
                            username = result[0][1]['uid'][0]
                            print "user \"%s\" does not exist, creating from ldap info and mapping into group \"%s\"" % (username+'.'+fqn, groupname+'.'+fqn)
                            if result[0][1]['sshPublicKey']:
                                ssh_public_key = result[0][1]['sshPublicKey'][0]
                            else:
                                ssh_public_key = None
                            uid = result[0][1]['uidNumber'][0]
                            first_name, last_name = result[0][1]['gecos'][0].split(None, 1)
                            hdir = result[0][1]['homeDirectory'][0]
                            shell = result[0][1]['loginShell'][0]
                            email = result[0][1]['mail'][0]
                            # ldap doesn't store user type data so
                            # use the default type
                            user_type = cfg.def_user_type
                            # create a new user object and fire it into
                            # the db, face first.
                            u = Users(first_name, last_name, ssh_public_key, username, site_id, realm, uid, user_type, hdir, shell, email, True)
                            cfg.dbsess.add(u)
                            cfg.dbsess.commit()
                            # map the user we just created into the
                            # group we're currently operating on
                            ugmap = UserGroupMapping(g.id, u.id)
                            cfg.dbsess.add(ugmap)
                            cfg.dbsess.commit()
                        else:
                            print "User \"%s\" not created. The user is in a group in LDAP but does not actually exist in LDAP.\nMost likely this is a system user (such as \"nobody\" or \"apache\") that should not exist in LDAP." % user
    # now that we're done with the groups, let's go back in and make
    # sure we create any leftover users that weren't in a group
    dn = "ou=%s,dc=%s,dc=%s,dc=" % (cfg.ldap_users_ou, realm, site_id)
    dn += ',dc='.join(d)
    search = '(objectClass=person)'
    try:
        results = ldcon.search_s(dn, ldap.SCOPE_BASE, search)
    except ldap.LDAPError, e:
        print "Entity not found, skipping."
        print e
        results = False
    if results:
        for result in results:
            username = result[0][1]['uid'][0]
            u = mothership.validate.v_get_user_obj(cfg, username+'.'+fqn)
            if u:
                print "user exists, skipping"
            else:
                # create a new user object and fire it into
                # the db, face first.
                print "user \"%s\" does not exist, creating from ldap info" % (username+'.'+fqn)
                if result[0][1]['sshPublicKey']:
                    ssh_public_key = result[0][1]['sshPublicKey'][0]
                else:
                    ssh_public_key = None
                uid = result[0][1]['uidNumber'][0]
                first_name, last_name = result[0][1]['gecos'][0].split(None, 1)
                hdir = result[0][1]['homeDirectory'][0]
                shell = result[0][1]['loginShell'][0]
                email = result[0][1]['mail'][0]
                # ldap doesn't store user type data so
                # use the default type
                user_type = cfg.def_user_type
                u = Users(first_name, last_name, ssh_public_key, username, site_id, realm, uid, user_type, hdir, shell, email, True)
                cfg.dbsess.add(u)
                cfg.dbsess.commit()
                # map the user we just created into the
                # group we're currently operating on
                ugmap = UserGroupMapping(g.id, u.id)
                cfg.dbsess.add(ugmap)
                cfg.dbsess.commit()
    else:
        print "No users found!"

def password_prompt(minchars, enctype):
    import getpass
    import hashlib
    from base64 import encodestring as encode
    ans1 = getpass.getpass("Enter new passwd:")
    if len(ans1) < minchars:
        print 'Password is too short!  Must be at least %d char(s)' % minchars
        return
    ans2 = getpass.getpass("Re-type new passwd:")
    if ans1 != ans2:
        print 'Passwords do not match!'
        return
    salt = os.urandom(4)
    h = eval('hashlib.%s(ans1)' % enctype)
    h.update(salt)
    return '{SSHA}' + encode(h.digest() + salt)[:-1]

def update_ldap_passwd(cfg, username):
    u = mothership.validate.v_get_user_obj(cfg, username)
    d = cfg.domain.split('.')
    if u:
        ldap_master = get_master(cfg, u.realm+'.'+u.site_id)
        dn = "uid=%s,ou=%s,dc=%s,dc=%s,dc=" % (u.username, cfg.ldap_users_ou, u.realm, u.site_id)
        dn += ',dc='.join(d)
    else:
        raise LDAPError("user \"%s\" not found, aborting" % username)
    ldcon = ld_connect(cfg, ldap_master, u.realm, u.site_id)
    try:
        raw_res = ldcon.search_s(dn, ldap.SCOPE_BASE)
        if 'userPassword' in raw_res[0][1].keys():
            print 'User %s ALREADY has LDAP password set' % u.username
        else:
            print 'User %s does NOT have LDAP password set' % u.username
        newpass = password_prompt(8,'sha1')
        try:
            ldcon.modify_s(dn, [(ldap.MOD_REPLACE, 'userPassword', newpass)])
        except ldap.LDAPError, e:
            raise LDAPError(e)
        ldcon.unbind()
    except ldap.LDAPError, e:
        raise LDAPError(e)


