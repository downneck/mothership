#!/usr/bin/env python

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

# imports
import os
import sys
import ldap
import mothership
import mothership.validate
import mothership.users
import mothership.kv
from mothership_models import *
from configure import Configure

# the global config. useful everywhere
cfgfile = 'mothership.yaml'
cfg = Configure(cfgfile)

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

    serv = list(cfg.dbsess.query(Server).\
    filter(Server.role=='ldap').\
    filter(Server.realm==realm).\
    filter(Server.site_id==site_id).\
    filter(Server.role_index=='1').all())

    if len(serv) > 1:
        raise LDAPError("more than one master ldap server found for \"%s\", aborting.\nPlease fix your ldap role indexes" % realm_path)
    elif not serv:
        raise LDAPError("no ldap servers with role index \"1\" found for \"%s\", aborting\nPlease elect an LDAP master server by giving it role index \"1\"" % realm_path)

    # i hate this so much...
    serv = serv[0]
    return serv.hostname+'.'+realm_path


# open a connection to the ldap master
def ld_connect(cfg, ldap_master):
    d = cfg.domain.split('.')

    admin_cn = str(mothership.kv.select(cfg, ldap_master, key="ldap_admin_cn")).split('=')[1]
    admin_pass = str(mothership.kv.select(cfg, ldap_master, key="ldap_admin_pass")).split('=')[1]
    admin_dn = "cn=%s,dc=" % admin_cn
    admin_dn += ',dc='.join(d)
    ld_server_string = "ldap://"+ldap_master

    # init the connection to the ldap server
    try:
        ldcon = ldap.initialize(ld_server_string)
        ldcon.simple_bind_s(admin_dn, admin_pass)
    except ldap.LDAPError, e:
        print "error connecting to ldap server: %s" % ldap_master
        print "INFO DUMP:\n"
        print "admin_dn: %s\nadmin_pass: %s\nld_server_string: %s" % (admin_dn, admin_pass, ld_server_string)
        print "\nLDAP Messages:\n"
        # for debugging
        #print e

    return ldcon


# display a group's ldap info
def gdisplay(cfg, groupname):
    # get group object
    g = mothership.validate.v_get_group_obj(cfg, groupname)
    # an array made of the domain parts.
    d = cfg.domain.split('.')

    if g:
        # get ldap master info, stitch together some dn info
        ldap_master = get_master(cfg, g.realm+'.'+g.site_id)
        dn = "cn=%s,ou=%s,dc=" % (g.groupname, cfg.ldap_groups_ou)
        dn += ',dc='.join(d)
    else:
        raise LDAPError("group \"%s\" not found, aborting" % groupname)

    ldcon = ld_connect(cfg, ldap_master)

    try:
        raw_res = ldcon.search_s(dn, ldap.SCOPE_BASE)
        print raw_res
        ldcon.unbind()
    except ldap.LDAPError, e:
        raise LDAPError(e)


# display a user's ldap info
def udisplay(cfg, username):
    # get user object
    u = mothership.validate.v_get_user_obj(cfg, username)
    # an array made of the domain parts.
    d = cfg.domain.split('.')

    if u:
        # get ldap master info, stitch together some dn info
        ldap_master = get_master(cfg, u.realm+'.'+u.site_id)
        dn = "uid=%s,ou=%s,dc=" % (u.username, cfg.ldap_users_ou)
        dn += ',dc='.join(d)
    else:
        raise LDAPError("user \"%s\" not found, aborting" % username)

    ldcon = ld_connect(cfg, ldap_master)

    try:
        raw_res = ldcon.search_s(dn, ldap.SCOPE_BASE)
        print raw_res 
        ldcon.unbind()
    except ldap.LDAPError, e:
        #print "User \"%s\" not found in the directory on %s" % (u.username, ldap_master)
        raise LDAPError(e)


# update a user entry
def uupdate(cfg, username):
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
    ldcon = ld_connect(cfg, ldap_master)

    dn = "uid=%s,ou=%s,dc=" % (u.username, cfg.ldap_users_ou)
    dn += ',dc='.join(d)
    # stitch together the LDAP, fire it into the ldap master server 
    try:
        full_name = u.first_name + " " + u.last_name
        mod_record = [(ldap.MOD_REPLACE, 'sn', u.last_name),
                      (ldap.MOD_REPLACE, 'gecos', full_name),
                      (ldap.MOD_REPLACE, 'uidNumber', str(u.uid)),
                      (ldap.MOD_REPLACE, 'homeDirectory', u.hdir),
                      (ldap.MOD_REPLACE, 'loginShell', u.shell),
                      (ldap.MOD_REPLACE, 'sshPublicKey', u.ssh_public_key),
                     ]
        ldcon.modify_s(dn, mod_record)
    except ldap.LDAPError, e:
        raise LDAPError(e)

    # close the LDAP connection
    ldcon.unbind()


##### Only change in main in ldap module would be to add email:
#                      (ldap.MOD_REPLACE, 'mail', u.email),
##### password function as follows:

def password_prompt(minchars, enctype):
    import getpass
    import hashlib
    from base64 import encodestring as encode
    ans1 = getpass.getpass("Enter new passwd:")
    if len(ans1) < minchars:
        print 'Password is too short!  Must be at least %d char(s)' % minchars
        sys.exit(1)
    ans2 = getpass.getpass("Re-type new passwd:")
    if ans1 != ans2:
        print 'Passwords do not match!'
        sys.exit(1)
    salt = os.urandom(4)
    h = eval('hashlib.%s(ans1)' % enctype)
    h.update(salt)
    return '{SSHA}' + encode(h.digest() + salt)[:-1]

def update_ldap_passwd(cfg, username):
    u = mothership.validate.v_get_user_obj(cfg, username)
    d = cfg.domain.split('.')
    if u:
        ldap_master = get_master(cfg, u.realm+'.'+u.site_id)
        dn = "uid=%s,ou=%s,dc=" % (u.username, cfg.ldap_users_ou)
        dn += ',dc='.join(d)
    else:
        raise LDAPError("user \"%s\" not found, aborting" % username)

    ldcon = ld_connect(cfg, ldap_master)
    try:
        raw_res = ldcon.search_s(dn, ldap.SCOPE_BASE)
        #print raw_res 

        if 'userPassword' in raw_res[0][1].keys():
            print 'User %s ALREADY has LDAP password set' % u.username
            #print raw_res[0][1]['userPassword'][0]
        else:
            print 'User %s does NOT have LDAP password set' % u.username
        newpass = password_prompt(8,'sha1')
        #print newpass
        try:
            ldcon.modify_s(dn, [(ldap.MOD_REPLACE, 'userPassword', newpass)])
        except ldap.LDAPError, e:
            raise LDAPError(e)
        ldcon.unbind()
    except ldap.LDAPError, e:
        raise LDAPError(e)


    # close the LDAP connection

if __name__ == "__main__":
    try:
        cfgfile = 'mothership.yaml'
        cfg = Configure(cfgfile)
    except IOError:
        print "Missing file named %s" % cfgfile
        sys.exit(1)

    update_ldap_passwd(cfg, sys.argv[1])    

