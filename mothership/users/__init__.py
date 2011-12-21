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
mothership.users

this module manipulates user data within mothership.
it does nothing interesting on its own and should
be paired with a system-level user management system
such as LDAP or /etc/passwd
"""

# system imports
import ldap

# mothership imports
import mothership
import mothership.ssh
import mothership.ldap

# All of the models and sqlalchemy are brought in
# to simplify referencing
from mothership.mothership_models import *

class UsersError(Exception):
    pass

def uadd(cfg, username, first_name, last_name, copy_from=None, keyfile=None, uid=None, hdir=None, shell=None, email=None, user_type=None):
    """
    [description]
    for the adding of users.

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the username we're adding
        first_name: user's first name (make something up if it's not a real person)
        last_name: user's last name (see above)
    optional:
        copy_from: the user to clone type, shell, and groups from
        keyfile: path to a file containing a valid ssh2 public key
        uid: the uid we want to assign this user
        hdir: user's home dir, if different from default
        shell: user's shell, if different from default
        email: user's email, if different from default
        user_type: optional type assignment, totally arbitrary (stuff like: employee, consultant, system account, etc.)

    [return value]
    nothing explicitly returned
    """


    # validate/construct/get the realm.site_id.domain data
    fqun = mothership.validate.v_get_fqn(cfg, name=username)
    username, realm, site_id, domain = mothership.validate.v_split_fqn(fqun)
    fqn = realm+'.'+site_id+'.'+domain
    fqun = username+'.'+fqn

    if get_uid(cfg, username=fqun):
        raise UsersError("User exists, exiting!")
    else:
        pass

    if copy_from:
        copy_user = mothership.validate.v_get_user_obj(cfg, copy_from)
    else:
        copy_user = None
 
    # debugging
    #print username, realm, site_id, first_name, last_name, keyfile, uid, hdir, shell, email, user_type

    # validate our input, not terribly rigorously...just enough to
    # ensure it's not empty or obviously incorrect
    if not first_name or not last_name:
        raise UsersError("You must specify both a first and last name when adding a new user")
    if not mothership.validate.v_validate_name(cfg, name=username):
        raise UsersError("invalid name, exiting!")
    # read in the ssh2 public key from a file and stuff it into the users
    # table entry object if it's (somewhat) valid
    if keyfile:
        ssh_public_key_array = mothership.ssh.unpack_ssh_public_key_file(cfg, keyfile)
        if ssh_public_key_array:
            # stitch the keys back together into a single string for
            # embedding in the DB or writing to a file
            # keep newlines in all but the final key
            ssh_public_key = ''.join(ssh_public_key_array).rstrip()
        else:
            raise UsersError("a problem occurred in unpacking the ssh public key, aborting")
    else:
        ssh_public_key = None

    # if we're supplied a uid, validate and use it, otherwise find the
    # next available uid and use that
    if uid:
        if mothership.validate.v_uid(cfg, uid):
            if mothership.validate.v_uid_in_db(cfg, uid, realm, site_id):
                raise UsersError("Duplicate UID detected, exiting.")
        else:
            raise UsersError("Invalid UID.")
    else:
        uid = next_available_uid(cfg, realm, site_id)
        print "No uid supplied, selecting the next available: %s" % uid

    # quick type validation. should probably move this to the validate module
    if user_type:
        if user_type not in cfg.user_types:
            raise UsersError("Invalid user type, please use one of the following: " + ', '.join(cfg.user_types))
    else:
        if copy_user:
            user_type = copy_user.type
        else:
            print 'No type supplied, using default: ' + cfg.def_user_type
            user_type = cfg.def_user_type

    # make sure the user's home dir is set correctly
    if not hdir:
        hdir = cfg.hdir + '/' + username
    else:
        pass

    # make sure the user's shell is set correctly
    if not shell:
        if copy_user:
            shell = copy_user.shell
        else:
            shell = cfg.shell
    else:
        pass 

    # make sure the user's email is set correctly
    if not email:
        email = username + '@' + cfg.email_domain
    else:
        pass

    # create a new Users object, populate it, ram it into the db
    u = Users(first_name, last_name, ssh_public_key, username, site_id, realm, uid, user_type, hdir, shell, email, active=True)
    cfg.dbsess.add(u)
    cfg.dbsess.commit()
    # debugging
    #print u

    # clone groups from a user to our new user
    if copy_user:
        # get group data associated with the user
        grouplist = []
        newgrouplist = []
        for g in cfg.dbsess.query(UserGroupMapping).\
        filter(UserGroupMapping.users_id==copy_user.id):
            group = cfg.dbsess.query(Groups).\
            filter(Groups.id==g.groups_id).first()
            grouplist.append(group.groupname)

            ng = None
            ng = cfg.dbsess.query(Groups).\
                 filter(Groups.groupname==group.groupname).\
                 filter(Groups.realm==u.realm).\
                 filter(Groups.site_id==u.site_id).first()

            # if the group does not exist in the new fqn, ask the user if we
            # should create it. if no, skip adding the new user to it
            if not ng:
                ans = raw_input("\"%s\" does not exist in \"%s.%s\", create it? (y/n): " % (group.groupname, realm, site_id))
                if ans == 'y' or ans == 'Y':
                    ng = gclone(cfg, group.groupname+'.'+group.realm+'.'+group.site_id, u.realm+'.'+u.site_id)
                    newgrouplist.append(ng.groupname)
                else:
                    print "aborted by user input, skipping group \"%s\"" % group.groupname
            else:
                newgrouplist.append(ng.groupname)

        for groupname in newgrouplist:
            print 'adding user "%s" to group "%s"' % (u.username+'.'+u.realm+'.'+u.site_id, groupname)
            try:
                utog(cfg, u.username+'.'+u.realm+'.'+u.site_id, groupname)
            except (mothership.validate.ValidationError, UsersError), e:
                print e
    else:
        # if we're not cloning groups from another user, just assign the defaults
        print "assigning default groups: %s" % (' '.join(cfg.default_groups))
        for i in cfg.default_groups:
            gid = get_gid(cfg, groupname=i+'.'+realm+'.'+site_id)
            if gid:
                utog(cfg, username=fqun, groupname=i)
            else:
                ans = raw_input('No group found for %s, would you like to create it? (y/n): ' % i)
                if ans != 'y' and ans != 'Y':
                    raise UsersError("unable to add user %s to default group %s because it doesn't exist" % (username, i))
                else:
                    gadd(cfg, groupname=i+'.'+realm+'.'+site_id)
                    utog(cfg, username=fqun, groupname=i)

    # update ldap data
    ldap_master = mothership.ldap.get_master(cfg, realm+'.'+site_id)
    if cfg.ldap_active and ldap_master:
        ans = raw_input('Do you want to add this user to LDAP as well? (y/n): ')
        if ans == 'y' or ans == 'Y':
            try:
                print "adding \"%s\" to LDAP" % fqun
                mothership.ldap.uadd(cfg, username=fqun)
                for i in cfg.default_groups:
                    print "updating \"%s\" in LDAP" % (i+'.'+realm+'.'+site_id)
                    mothership.ldap.gupdate(cfg, groupname=i+'.'+realm+'.'+site_id)
            except mothership.ldap.LDAPError, e:
                print 'mothership encountered an error, skipping LDAP update'
                print "Error: %s" % e

        else:
            print "LDAP update aborted by user input, skipping." 
    elif not cfg.ldap_active:
        print "LDAP not active, skipping"
    else:
        print "No LDAP master found for %s.%s, skipping" % (realm, site_id)

    return u


def uclone(cfg, username, newfqn):
    """
    [description]
    clones a user from one realm.site_id to another

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the existing user we're cloning
        newfqn: the new realm.site_id we're cloning to

    [return value]
    returns the new user object
    """
    u = mothership.validate.v_get_user_obj(cfg, username)
    newrealm, newsite_id, domain = mothership.validate.v_split_fqn(newfqn+'.'+cfg.domain)

    if not u:
        raise UsersError("User not found: %s" % username)

    # we may still want to clone inactive users
    # keep in mind, this will clone their inactive status as well
    if not u.active:
        ans = raw_input("User is marked inactive, do you really want to clone them? (y/n): ")
        if ans != "Y" and ans != "y":
            raise UsersError("Aborted by user input")

    baduser = cfg.dbsess.query(Users).\
              filter(Users.username==u.username).\
              filter(Users.realm==newrealm).\
              filter(Users.site_id==newsite_id).first()

    # if the user already exists in the target fqn, blow up
    if baduser:
        raise UsersError("User \"%s\" exists in the target fqn \"%s.%s\", Aborting" % (u.username, newrealm, newsite_id))

    # create the new user object and commit it to the db
    newu = uadd(cfg, u.username+'.'+newrealm+'.'+newsite_id, u.first_name, u.last_name, uid=u.uid, hdir=u.hdir, shell=u.shell, email=u.email, user_type=u.type)
    newu.ssh_public_key = u.ssh_public_key
    cfg.dbsess.add(newu)
    cfg.dbsess.commit()

    # get group data associated with the user
    grouplist = []
    newgrouplist = []
    for g in cfg.dbsess.query(UserGroupMapping).\
    filter(UserGroupMapping.users_id==u.id):
        group = cfg.dbsess.query(Groups).\
        filter(Groups.id==g.groups_id).first()
        if g not in cfg.default_groups:
            grouplist.append(group.groupname)

        ng = None
        ng = cfg.dbsess.query(Groups).\
             filter(Groups.groupname==group.groupname).\
             filter(Groups.realm==newrealm).\
             filter(Groups.site_id==newsite_id).first()

        # if the group does not exist in the new fqn, ask the user if we
        # should create it. if no, skip adding the new user to it
        if not ng:
            ans = raw_input("\"%s\" does not exist in \"%s.%s\", create it? (y/n): " % (group.groupname, newrealm, newsite_id))
            if ans == 'y' or ans == 'Y':
                ng = gclone(cfg, group.groupname+'.'+group.realm+'.'+group.site_id, newrealm+'.'+newsite_id)
                newgrouplist.append(ng.groupname)
            else:
                print "aborted by user input, skipping group \"%s\"" % group.groupname
        else:
            newgrouplist.append(ng.groupname)

    for groupname in newgrouplist:
        print 'adding user "%s" to group "%s"' % (newu.username+'.'+newu.realm+'.'+newu.site_id, groupname)
        try:
            utog(cfg, newu.username+'.'+newfqn, groupname)
        except (mothership.validate.ValidationError, UsersError), e:
            print e

    # update ldap data
    ldap_master = mothership.ldap.get_master(cfg, newu.realm+'.'+newu.site_id)
    dn = "uid=%s,ou=%s,dc=%s,dc=%s,dc=" % (newu.username, cfg.ldap_users_ou, newu.realm, newu.site_id)
    d = cfg.domain.split('.')
    dn += ',dc='.join(d)
    ldcon = mothership.ldap.ld_connect(cfg, ldap_master, newu.realm, newu.site_id)
    ldap_user_entry = ldcon.search_s(dn, ldap.SCOPE_BASE)
    if cfg.ldap_active and ldap_master and not ldap_user_entry:
        ans = raw_input('Do you want to add this user to LDAP as well? (y/n): ')
        if ans == 'y' or ans == 'Y':
            try:
                print "adding user \"%s\" in LDAP" % (newu.username+'.'+newfqn)
                mothership.ldap.uadd(cfg, username=newu.username+'.'+newfqn)
                for i in newgrouplist:
                    print "updating group \"%s\" in LDAP" % (i+'.'+newu.realm+'.'+newu.site_id)
                    mothership.ldap.gupdate(cfg, groupname=i+'.'+realm+'.'+site_id)
            except mothership.ldap.LDAPError, e:
                print 'mothership encountered an error, skipping LDAP user update'
                print "Error: %s" % e
        else:
            print "LDAP update aborted by user input, skipping LDAP user update"
    elif not cfg.ldap_active:
        print "LDAP not active, skipping LDAP user update"
    elif ldap_user_entry:
        mothership.ldap.uupdate(cfg, newu.username+'.'+newfqn) 
    else:
        print "No LDAP master found for %s.%s, skipping LDAP user update" % (newu.realm, newu.site_id)

    # return the new user object
    return newu


def next_available_uid(cfg, realm, site_id):
    """
    [description]
    searches the db for existing UIDS and picks the next available UID within the parameters configured in mothership.yaml

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        realm: the realm we're checking uids for
        site_id: the site_id we're checking uids for

    [return value]
    returns an integer representing the next available UID
    """

    i = cfg.uid_start
    uidlist = []
    u = cfg.dbsess.query(Users).\
    filter(Users.realm==realm).\
    filter(Users.site_id==site_id).all()
    for userentry in u:
        uidlist.append(userentry.uid)
    uidlist.sort(key=int)
    if not uidlist:
        # if we don't have any users in the users table
        # return the default first uid as configured in the yaml
        return cfg.uid_start
    else:
        for uu in uidlist:
            if uu < cfg.uid_start:
                pass
            elif not i == uu and i < cfg.uid_end:
                return i
            elif i < cfg.uid_end:
                i += 1
            else:
                raise UsersError("No available UIDs!")
        return i


def next_available_gid(cfg, realm, site_id):
    """
    [description]
    searches the db for existing GIDS and picks the next available GID within the parameters configured in mothership.yaml

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        realm: the realm we're checking gids for
        site_id: the site_id we're checking gids for

    [return value]
    returns an integer representing the next available GID
    """

    i = cfg.gid_start
    gidlist = []
    g = cfg.dbsess.query(Groups).\
    filter(Groups.realm==realm).\
    filter(Groups.site_id==site_id).all()
    for groupentry in g:
        gidlist.append(groupentry.gid)
    gidlist.sort(key=int)
    if not gidlist:
        # if we don't have any groups in the groups table
        # return the default first gid as configured in the yaml
        return cfg.gid_start
    else:
        for gg in gidlist:
            if gg < cfg.gid_start:
                pass
            elif not i == gg and i < cfg.gid_end:
                return i
            elif i < cfg.gid_end:
                i += 1
            else:
                raise UsersError("No available GIDs!")
        return i


def uwrite_pubkey(cfg, username, keyfile=None):
    """
    [description]
    retrieves a user's ssh2 key and sends it to the ssh module for writing to a file

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the username whose key we're writing
    optional:
        keyfile: the file to write to, defaults to "u.hdir/.ssh/authorized_keys"

    [return value]
    no explicit return
    """
    u = mothership.validate.v_get_user_obj(cfg, username)

    if not u:
        raise UsersError("User not found: %s" % username)

    if not u.active:
        ans = raw_input("User is marked inactive, do you really want their ssh key? (y/n): ")
        if ans != "Y" and ans != "y":
            raise UsersError("Aborted by user input")

    if not u.ssh_public_key:
        raise UsersError("User does not have any ssh2 public keys associated with it")

    if not keyfile:
        keyfile = u.hdir+'/.ssh/authorized_keys'
        print "keyfile not supplied, defaulting to: %s" % keyfile

    mothership.ssh.write_key_to_file(cfg, u.ssh_public_key, keyfile)


def uremove(cfg, username):
    """
    [description]
    removes a user from the database, first removing it from any groups

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the username we want to remove

    [return value]
    no explicit return
    """

    u = mothership.validate.v_get_user_obj(cfg, username)
    fqun = u.username+'.'+u.realm+'.'+u.site_id+'.'+cfg.domain

    if u:
        # get group data associated with the user
        grouplist = []
        for g in cfg.dbsess.query(UserGroupMapping).\
        filter(UserGroupMapping.users_id==u.id):
            group = cfg.dbsess.query(Groups).\
            filter(Groups.id==g.groups_id).first()
            grouplist.append(group.groupname)

        # first, tear the user out of any groups it's in
        for groupname in grouplist:
            print 'Removing user "%s" from group "%s"' % (username, groupname)
            # we don't ask for confirmation because urmg() does
            urmg(cfg, username=fqun, groupname=groupname)
        # ask for verification before deletion
        print "\nACHTUNG! ACHTUNG! ACHTUNG! ACHTUNG! ACHTUNG! ACHTUNG! ACHTUNG! ACHTUNG!\n"
        print "This will remove the user from mothership, allowing their UID to be re-used!"
        print "If this is not the behavior you want, you probably need to use deactivate"
        ans = raw_input('to delete user \"%s\", please type "delete_%s": ' % (username, username))
        if ans != 'delete_%s' % username:
            # d'oh! we've already removed the user from it's groups
            # need to stuff it back in before bailing out
            # thankfully, we still know what groups it was in
            for groupname in grouplist:
                print 'restoring user "%s" to group "%s"' % (username, groupname)
                utog(cfg, username=fqun, groupname=groupname)
            raise UsersError('Delete aborted by user input')
        # if we're running ldap, remove the user from ldap
        ldap_master = mothership.ldap.get_master(cfg, u.realm+'.'+u.site_id)
        if cfg.ldap_active and ldap_master:
            ans = raw_input('Do you want to remove this user from LDAP as well? (y/n): ')
            if ans == 'y' or ans == 'Y':
                try:
                    for groupname in grouplist:
                        print "removing \"%s\" from LDAP group \"%s\"" % (username, groupname)
                        mothership.ldap.gupdate(cfg, groupname+'.'+u.realm+'.'+u.site_id)
                    print "removing \"%s\" user entry from LDAP" % username
                    mothership.ldap.uremove(cfg, username=u.username+'.'+u.realm+'.'+u.site_id)
                except mothership.ldap.LDAPError, e:
                    print 'mothership encountered an error, skipping LDAP update'
                    print "Error: %s" % e
            else:
                print "LDAP update aborted by user input, skipping."
        elif not cfg.ldap_active:
            print "LDAP not active, skipping"
        else:
            print "No LDAP master found for %s.%s, skipping" % (u.realm, u.site_id)
        cfg.dbsess.delete(u)
        cfg.dbsess.commit()
        print 'Removing user "%s" from location "%s.%s"' % (u.username, u.realm, u.site_id)
    else:
        print "User \"%s\" not found" % username


def udeactivate(cfg, username):
    """
    [description]
    sets a user inactive, first removing it from any groups

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the username we want to remove

    [return value]
    no explicit return
    """

    u = mothership.validate.v_get_user_obj(cfg, username)
    fqun = u.username+'.'+u.realm+'.'+u.site_id+'.'+cfg.domain
    fqn = u.realm+'.'+u.site_id+'.'+cfg.domain

    if u:
        if not u.active:
            raise UsersError("User is already inactive")
        # get group data associated with the user
        grouplist = []
        for g in cfg.dbsess.query(UserGroupMapping).\
        filter(UserGroupMapping.users_id==u.id):
            group = cfg.dbsess.query(Groups).\
            filter(Groups.id==g.groups_id).first()
            grouplist.append(group.groupname)

        # first, tear the user out of any groups it's in
        for groupname in grouplist:
            print "Removing user \"%s\" from group \"%s\"" % (username, groupname)
            # we don't ask for confirmation because urmg() does
            urmg(cfg, username=fqun, groupname=groupname)
        # ask for verification before deletion
        ans = raw_input('to deactivate user \"%s\", please type "deactivate_%s": ' % (username, username))
        if ans != 'deactivate_%s' % username:
            print 'Deactivation aborted by user input'
            # d'oh! we've already removed the user from it's groups
            # need to stuff it back in before bailing out
            # thankfully, we still know what groups it was in
            for groupname in grouplist:
                print 'restoring user "%s" to group "%s"' % (username, groupname)
                utog(cfg, username=fqun, groupname=groupname)
            raise UsersError('aborting user modification!')
        u.active = False
        cfg.dbsess.add(u)
        cfg.dbsess.commit()
        # if we're running ldap, remove the user from ldap
        ldap_master = mothership.ldap.get_master(cfg, u.realm+'.'+u.site_id)
        if cfg.ldap_active and ldap_master:
            ans = raw_input('Do you want to remove this user from LDAP as well? (y/n): ')
            if ans == 'y' or ans == 'Y':
                try:
                    for groupname in grouplist:
                        print "removing \"%s\" from LDAP group \"%s\"" % (username, groupname)
                        mothership.ldap.gupdate(cfg, groupname+"."+fqn)
                    print "removing \"%s\" user entry from LDAP" % username
                    mothership.ldap.uremove(cfg, username=fqun)
                except mothership.ldap.LDAPError, e:
                    print 'mothership encountered an error, skipping LDAP update'
                    print "Error: %s" % e
            else:
                print "LDAP update aborted by user input, skipping."
        elif not cfg.ldap_active:
            print "LDAP not active, skipping"
        else:
            print "No LDAP master found for %s.%s, skipping" % (u.realm, u.site_id)
        print 'Deactivating user "%s" in location "%s.%s"' % (u.username, u.realm, u.site_id)
    else:
        print "User \"%s\" not found" % username


def uactivate(cfg, username):
    """
    [description]
    sets a user active, will add user to any groups in LDAP currently assigned to it
    but will NOT add user to default groups. (if 'ship du' shows no groups, this will not
    add any.)

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the username we want to remove

    [return value]
    no explicit return
    """

    u = mothership.validate.v_get_user_obj(cfg, username)
    fqun = u.username+'.'+u.realm+'.'+u.site_id+'.'+cfg.domain
    fqn = u.realm+'.'+u.site_id+'.'+cfg.domain

    if u:
        if u.active:
            raise UsersError("User is already active")
        # get group data associated with the user
        grouplist = []
        for g in cfg.dbsess.query(UserGroupMapping).\
        filter(UserGroupMapping.users_id==u.id):
            group = cfg.dbsess.query(Groups).\
            filter(Groups.id==g.groups_id).first()
            grouplist.append(group.groupname)

        # This is where me make the user active again
        u.active = True
        cfg.dbsess.add(u)
        cfg.dbsess.commit()
        # if we're running ldap, remove the user from ldap
        ldap_master = mothership.ldap.get_master(cfg, u.realm+'.'+u.site_id)
        if cfg.ldap_active and ldap_master:
            print "Activating user to LDAP..."
            print "Adding \"%s\" user entry from LDAP" % username
            mothership.ldap.uadd(cfg, username=fqun)
            try:
                for groupname in grouplist:
                    print "adding \"%s\" to LDAP group \"%s\"" % (username, groupname)
                    mothership.ldap.gupdate(cfg, groupname+"."+fqn)
            except mothership.ldap.LDAPError, e:
                print 'mothership encountered an error, skipping LDAP update'
                print "Error: %s" % e
        elif not cfg.ldap_active:
            print "LDAP not active, skipping"
        else:
            print "No LDAP master found for %s.%s, skipping" % (u.realm, u.site_id)
        print 'Activating user "%s" in location "%s.%s"' % (u.username, u.realm, u.site_id)
    else:
        print "User \"%s\" not found" % username

def umodify(cfg, username, first_name=None, last_name=None, keyfile=None, uid=None, hdir=None, shell=None, email=None, user_type=None):
    """
    [description]
    modifies user data in the database

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the username we want to modify 
    optional:
        first_name: the first name of the user
        last_name: the last name of the user
        keyfile: path to a file containing a valid ssh2 public key
        uid: the uid we want to assign this user
        hdir: user's home dir, if different from default
        shell: user's shell, if different from default
        email: user's email, if different from default
        user_type: optional type assignment, totally arbitrary (stuff like: employee, consultant, system account, etc.)

    [return value]
    no explicit return
    """

    u = mothership.validate.v_get_user_obj(cfg, username)

    if u:
        # if the user exists, modify its data
        if first_name:
            u.first_name = first_name
        else:
            pass
        if last_name:
            u.last_name = last_name
        else:
            pass
        if keyfile:
            ssh_public_key_array = mothership.ssh.unpack_ssh_public_key_file(cfg, keyfile)
            if ssh_public_key_array:
                # stitch the keys back together into a single string for
                # embedding in the DB or writing to a file
                # keep newlines in all but the final key
                u.ssh_public_key = ''.join(ssh_public_key_array).rstrip()
            else:
                raise UsersError("a problem occurred unpacking the ssh public key file, aborting")
        else:
            pass
        if uid:
            # look around for the target uid, just in case
            baduid = cfg.dbsess.query(Users).\
            filter(Users.uid==uid).\
            filter(Users.site_id==u.site_id).\
            filter(Users.realm==u.realm).first()
            # if the target uid exists, let's not stomp on it
            if baduid:
                raise UsersError("target uid \"%s\" exists in %s.%s, aborting!" % (uid, u.realm, u.site_id))
            else:
                u.uid = uid
        else:
            pass
        if hdir:
            u.hdir = hdir
        else:
            pass
        if shell:
            u.shell = shell
        else:
            pass
        if email:
            u.email = email
        else:
            pass
        if user_type:
            u.type = user_type
        else:
            pass
        # ask for verification before modification
        ans = raw_input('to modify this user please type "modify_%s": ' % username)
        if ans != 'modify_%s' % username:
            raise UsersError('aborting user modification!')
        else:
            cfg.dbsess.add(u)
            cfg.dbsess.commit()
            print "updated user info:"
            udisplay(cfg, username=u.username+'.'+u.realm+'.'+u.site_id)
    else:
        raise UsersError("User \"%s\" not found." % username)
    # update ldap
    ldap_master = mothership.ldap.get_master(cfg, u.realm+'.'+u.site_id)
    if cfg.ldap_active and ldap_master:
        ans = raw_input('Do you want to update this user in LDAP as well? (y/n): ')
        if ans == 'y' or ans == 'Y':
            try:
                print "updating \"%s\" in LDAP" % (u.username+'.'+u.realm+'.'+u.site_id)
                mothership.ldap.uupdate(cfg, username=u.username+'.'+u.realm+'.'+u.site_id)
            except mothership.ldap.LDAPError, e:
                print 'mothership encountered an error, skipping LDAP update'
                print "Error: %s" % e
        else:
            print "LDAP update aborted by user input, skipping."
    elif not cfg.ldap_active:
        print "LDAP not active, skipping"
    else:
        print "No LDAP master found for %s.%s, skipping" % (u.realm, u.site_id)

def utog(cfg, username, groupname):
    """
    [description]
    adds a user to a group

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the fully-qualified username we want to add to groupname
        groupname: the group we want to add username to

    [return value]
    no explicit return
    """
    skip_ldap = False
    u = mothership.validate.v_get_user_obj(cfg, username)
    if not u:
        raise UsersError("user \"%s\" not found" % username)
    fqn = u.realm+'.'+u.site_id+'.'+cfg.domain
    if not u.active:
        raise UsersError("User %s is set inactive. Please activate the user before adding to groups" % u.username)
    g = mothership.validate.v_get_group_obj(cfg, groupname=groupname+'.'+fqn)
    if not g:
        raise UsersError("group \"%s\" not found" % groupname)

    if get_utog_map(cfg, username=u.username+'.'+fqn, groupname=g.groupname):
        skip_ldap = "user \"%s\" is already in group \"%s\", skipping!" % (username, groupname)
    else:
        # create a new map object
        newmap = UserGroupMapping(g.id, u.id)
        # debugging
        #print umap, newmap
        cfg.dbsess.add(newmap)
        cfg.dbsess.commit()
    # update ldap data
    ldap_master = mothership.ldap.get_master(cfg, u.realm+'.'+u.site_id)
    if cfg.ldap_active and ldap_master and not skip_ldap:
        ans = raw_input('Do you want to update this group in LDAP as well? (y/n): ')
        if ans == 'y' or ans == 'Y':
            try:
                print "updating \"%s\" in LDAP" % (g.groupname+'.'+fqn)
                mothership.ldap.gupdate(cfg, groupname=g.groupname+'.'+fqn)
            except mothership.ldap.LDAPError, e:
                print 'mothership encountered an error, skipping LDAP update'
                print "Error: %s" % e
        else:
            print "LDAP update aborted by user input, skipping."
    elif not cfg.ldap_active:
        print "LDAP not active, skipping"
    elif skip_ldap:
        print skip_ldap 
    else:
        print "No LDAP master found for %s.%s, skipping" % (g.realm, g.site_id)


def urmg(cfg, username, groupname):
    """
    [description]
    removes a user from a group

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the username we want to remove from groupname
        groupname: the group we want to remove username from

    [return value]
    no explicit return
    """
    u = mothership.validate.v_get_user_obj(cfg, username)
    if not u:
        raise UsersError("user \"%s\" not found" % username)
    fqn = u.realm+'.'+u.site_id+'.'+cfg.domain
    g = mothership.validate.v_get_group_obj(cfg, groupname+'.'+fqn)
    if not g:
        raise UsersError("group \"%s\" not found" % groupname)

    # get user-to-group mapping
    umap = get_utog_map(cfg, username=u.username+'.'+fqn, groupname=g.groupname)

    if umap:
        utogmap = cfg.dbsess.query(UserGroupMapping).\
        filter(UserGroupMapping.id==umap).first()

        # ask for verification before deletion
        ans = raw_input('to delete user "%s" from group "%s" please type "delete_%s_%s": ' % (u.username, g.groupname, u.username, g.groupname))
        if ans != 'delete_%s_%s' % (u.username, g.groupname):
            raise UsersError("Aborting removal of user \"%s\" from group \"%s\"" % (u.username, g.groupname))
        else:
            # ka-blooey!
            cfg.dbsess.delete(utogmap)
            cfg.dbsess.commit()
    else:
        raise UsersError("user \"%s\" not found in group \"%s\" for %s.%s" % (u.username, g.groupname, u.realm, u.site_id))
    # update ldap data
    ldap_master = mothership.ldap.get_master(cfg, u.realm+'.'+u.site_id)
    if cfg.ldap_active and ldap_master:
        ans = raw_input('Do you want to update this group in LDAP as well? (y/n): ')
        if ans == 'y' or ans == 'Y':
            try:
                print "updating \"%s\" in LDAP" % (g.groupname+'.'+fqn)
                mothership.ldap.gupdate(cfg, groupname=g.groupname+'.'+fqn)
            except mothership.ldap.LDAPError, e:
                print 'mothership encountered an error, skipping LDAP update'
                print "Error: %s" % e
        else:
            print "LDAP update aborted by user input, skipping."
    elif not cfg.ldap_active:
        print "LDAP not active, skipping"
    else:
        print "No LDAP master found for %s.%s, skipping" % (g.realm, g.site_id)



def udisplay(cfg, username, pubkey=False, compact=False, list=False):
    """
    [description]
    displays user information

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the username we want to display
    optional:
        pubkey: boolean. if true, display the user's public key

    [return value]
    no explicit return
    """

    u = mothership.validate.v_get_user_obj(cfg, username)

    if u and not compact:
        # get group data
        grouplist = []
        for g in cfg.dbsess.query(UserGroupMapping).\
        filter(UserGroupMapping.users_id==u.id):
            group = cfg.dbsess.query(Groups).\
            filter(Groups.id==g.groups_id).first()
            grouplist.append(group.groupname)
        print "\nusername, uid, type: %s, %s, %s" % (u.username, u.uid, u.type)
        if u.active:
            print "user is marked: ACTIVE"
        else:
            print "user is marked: INACTIVE"
        print "location: %s.%s" % (u.realm, u.site_id)
        print "first name, last name: %s %s" % (u.first_name, u.last_name)
        if u.hdir:
            print "home directory: "+u.hdir
        else:
            print "home directory: NOT SET"
        if u.shell:
            print "shell: "+u.shell
        else:
            print "shell: NOT SET"
        if u.email:
            print "email: "+u.email
        else:
            print "email: NOT SET"
        if not list:
            print "groups: "+' '.join(grouplist)
        else:
            print "groups: "
            for group in grouplist:
                print group
        if pubkey:
            print "ssh public key(s): "+u.ssh_public_key
        else:
            pass
    elif u and compact:
        print "%s:%s:%s %s   # %s" % (u.username, u.uid, u.first_name, u.last_name, u.type)
    else:
        print "User \"%s\" not found." % (username)


def gadd(cfg, groupname, gid=None, description=None, sudo_cmds=None):
    """
    [description]
    adds a group to the db

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        groupname: the name of the group we want to add
    optional:
        gid: the gid we want to assign the group
        description: a short description of the group
        sudo_cmds: commands to pass into sudoers entries

    [return value]
    no explicit return
    """

    # validate/construct/get the realm.site_id.domain data
    fqgn = mothership.validate.v_get_fqn(cfg, name=groupname)
    groupname, realm, site_id, domain = mothership.validate.v_split_fqn(fqgn)
    fqn = realm+'.'+site_id
    fqgn = groupname+'.'+fqn

    if not description:
        description = "No description given"
    else:
        pass
    if not mothership.validate.v_realm(cfg, realm):
        raise UsersError("Invalid realm, exiting!")
    else:
        pass
    if not mothership.validate.v_site_id(cfg, site_id):
        raise UsersError("Invalid site_id, exiting!")
    if not mothership.validate.v_validate_name(cfg, name=groupname):
        raise UsersError("Invalid group name, exiting!")
    if get_gid(cfg, groupname=fqgn):
        raise UsersError("Duplicate group, exiting!")
    else:
        if not gid:
            gid = next_available_gid(cfg, realm, site_id)
        else:
            pass
    if sudo_cmds == 'all' or sudo_cmds == 'All':
        sudo_cmds = 'ALL'

    # create a new group object, jam it into the db
    g = Groups(description, sudo_cmds, groupname, site_id, realm, gid)
    cfg.dbsess.add(g)
    cfg.dbsess.commit()
    # debugging
    #print newgroup
    print 'group "%s" added successfully\n' % groupname
    gdisplay(cfg, groupname=fqgn)
    # update ldap data
    ldap_master = mothership.ldap.get_master(cfg, g.realm+'.'+g.site_id)
    if cfg.ldap_active and ldap_master:
        ans = raw_input('Do you want to add this group to LDAP as well? (y/n): ')
        if ans == 'y' or ans == 'Y':
            try:
                print "adding \"%s\" to LDAP" % (g.groupname+'.'+fqn)
                mothership.ldap.gadd(cfg, groupname=g.groupname+'.'+fqn)
            except mothership.ldap.LDAPError, e:
                print 'mothership encountered an error, skipping LDAP update'
                print "Error: %s" % e
        else:
            print "LDAP update aborted by user input, skipping."
    elif not cfg.ldap_active:
        print "LDAP not active, skipping"
    else:
        print "No LDAP master found for %s.%s, skipping" % (realm, site_id)
    return g


def gremove(cfg, groupname):
    """
    [description]
    removes a group to from db, emptying it of users first

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        groupname: the name of the group we want to remove

    [return value]
    no explicit return
    """

    g = mothership.validate.v_get_group_obj(cfg, groupname)

    # get a list of users in that group
    userlist = []
    if not g:
        raise UsersError("group \"%s\" does not exist" % groupname)
    else:
        fqn = g.realm+'.'+g.site_id+'.'+cfg.domain
        for m in cfg.dbsess.query(UserGroupMapping).\
        filter(UserGroupMapping.groups_id==g.id):
            user = cfg.dbsess.query(Users).\
            filter(Users.id==m.users_id).first()
            userlist.append(user.username)

    # if there are users, we must remove them from the group first
    if userlist:
        print 'the following users will be removed from group "%s": %s' % (groupname, ' '.join(userlist))
        for username in userlist:
            # we don't ask for confirmation because urmg() does
            urmg(cfg, username=username+'.'+fqn, groupname=g.groupname)
        # we do ask for verification before deletion of the group itself
        ans = raw_input('to remove this group please type "delete_%s": ' % groupname)
        if ans != 'delete_%s' % groupname:
            # d'oh! we've already removed the users from the group
            # need to stuff 'em back in before bailing out
            # thankfully, we still know who they are
            for username in userlist:
                urmg(cfg, username=username+'.'+fqn, groupname=g.groupname)
            raise UsersError("group \"%s\" delete aborted, restoring users: %s" % (groupname, ' '.join(userlist)))
        else:
            # update ldap data
            ldap_master = mothership.ldap.get_master(cfg, g.realm+'.'+g.site_id)
            if cfg.ldap_active and ldap_master:
                ans = raw_input('Do you want to remove this group from LDAP as well? (y/n): ')
                if ans == 'y' or ans == 'Y':
                    try:
                        print "removing \"%s\" from LDAP" % (g.groupname+'.'+fqn)
                        mothership.ldap.gremove(cfg, groupname=g.groupname+'.'+fqn)
                    except mothership.ldap.LDAPError, e:
                        print 'mothership encountered an error, skipping LDAP update'
                        print "Error: %s" % e
                else:
                    print "LDAP update aborted by user input, skipping."
            elif not cfg.ldap_active:
                print "LDAP not active, skipping"
            else:
                print "No LDAP master found for %s.%s, skipping" % (g.realm, g.site_id)
            cfg.dbsess.delete(g)
            cfg.dbsess.commit()
    # if there are no users, go ahead and rm the group
    else:
        print 'group "%s" is empty' % groupname
        # ask for verification before deletion
        ans = raw_input('to remove this group please type "delete_%s": ' % groupname)
        if ans != 'delete_%s' % groupname:
            raise UsersError('group delete aborted!')
        else:
            # update ldap data
            ldap_master = mothership.ldap.get_master(cfg, g.realm+'.'+g.site_id)
            if cfg.ldap_active and ldap_master:
                ans = raw_input('Do you want to remove this group from LDAP as well? (y/n): ')
                if ans == 'y' or ans == 'Y':
                    try:
                        print "removing \"%s\" from LDAP" % (g.groupname+'.'+fqn)
                        mothership.ldap.gremove(cfg, groupname=g.groupname+'.'+fqn)
                    except mothership.ldap.LDAPError, e:
                        print 'mothership encountered an error, skipping LDAP update'
                        print "Error: %s" % e
                else:
                    print "LDAP update aborted by user input, skipping."
            elif not cfg.ldap_active:
                print "LDAP not active, skipping"
            else:
                print "No LDAP master found for %s.%s, skipping" % (g.realm, g.site_id)
            cfg.dbsess.delete(g)
            cfg.dbsess.commit()


def gdisplay(cfg, groupname, list=False):
    """
    [description]
    display group information

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        groupname: the name of the group we want to display

    [return value]
    no explicit return
    """

    g = mothership.validate.v_get_group_obj(cfg, groupname)

    if g:
        # get a list of users in that group
        userlist = []
        for m in cfg.dbsess.query(UserGroupMapping).\
        filter(UserGroupMapping.groups_id==g.id):
            user = cfg.dbsess.query(Users).\
            filter(Users.id==m.users_id).first()
            userlist.append(user.username)
        # print out our info
        print "groupname, gid: %s, %s" % (g.groupname, g.gid)
        print "location: %s.%s" % (g.realm, g.site_id)
        print "description: "+g.description
        print "allowed sudo commands: %s" % g.sudo_cmds
        if not list:
            print "users: "+' '.join(userlist)
        else:
            print "users:"
            for user in userlist:
                print user
    else:
        print "group \"%s\" not found" % (groupname)


def gclone(cfg, groupname, newfqn):
    """
    [description]
    clones a user from one realm.site_id to another

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        groupname: the existing user we're cloning
        newfqn: the new realm.site_id we're cloning to

    [return value]
    returns the new group object
    """
    g = mothership.validate.v_get_group_obj(cfg, groupname)
    newrealm, newsite_id, domain = mothership.validate.v_split_fqn(newfqn+'.'+cfg.domain)

    if not g:
        raise UsersError("Group not found: %s" % groupname)

    badgroup = cfg.dbsess.query(Groups).\
               filter(Groups.groupname==g.groupname).\
               filter(Groups.realm==newrealm).\
               filter(Groups.site_id==newsite_id).first()

    # target group already exists, blow up
    if badgroup:
        raise UsersError("Group \"%s\" exists in the target fqn\"%s.%s\", Aborting" % (g.groupname, newrealm, newsite_id))

    # create a new group in the new realm
    newg = gadd(cfg, g.groupname+'.'+newrealm+'.'+newsite_id, g.gid, g.description, g.sudo_cmds)

    # get the list of users in the source group
    userlist = []
    for m in cfg.dbsess.query(UserGroupMapping).\
    filter(UserGroupMapping.groups_id==g.id):
        user = cfg.dbsess.query(Users).\
        filter(Users.id==m.users_id).first()
        userlist.append(user.username)

    # if there are users in the source group, find out if we should
    # copy them to the target group.
    if userlist:
        print "the source group \"%s\" has users in it, should we copy the list?" % (g.groupname+'.'+g.realm+'.'+g.site_id)
        print "YES: all users that exist in the target fqn will be copied"
        print "NO: no users will be copied"
        print "nonexistent users will be cloned"
        print "user list to be copied is: %s" % userlist
        ans = raw_input("copy user list? (y/n): ")
        if ans == 'Y' or ans == 'y':
            newuserlist = []
            for user in userlist:
                newu = cfg.dbsess.query(Users).\
                       filter(Users.username==user).\
                       filter(Users.realm==newrealm).\
                       filter(Users.site_id==newsite_id).first()
                if newu:
                    newuserlist.append(newu.username)
                else:
                    try:
                         uclone(cfg, user, newrealm+'.'+newsite_id)
                    except:
                        print "Clone failed! Help!"
                        raise UsersError("Error: %s" % e)
        else:
            print "no users will be copied"
    # update ldap data
    ldap_master = mothership.ldap.get_master(cfg, newu.realm+'.'+newu.site_id)
    dn = "uid=%s,ou=%s,dc=%s,dc=%s,dc=" % (newg.groupname, cfg.ldap_groups_ou, newg.realm, newg.site_id)
    d = cfg.domain.split('.')
    dn += ',dc='.join(d)
    ldcon = mothership.ldap.ld_connect(cfg, ldap_master, newg.realm, newg.site_id)
    try:
        ldap_group_entry = ldcon.search_s(dn, ldap.SCOPE_BASE)
    except:
        ldap_group_entry = None
    if cfg.ldap_active and ldap_master and not ldap_group_entry:
        ans = raw_input('Do you want to add this group in LDAP as well? (y/n): ')
        if ans == 'y' or ans == 'Y':
            try:
                print "adding \"%s\" to LDAP" % (newg.groupname+'.'+newfqn)
                mothership.ldap.gadd(cfg, groupname=newg.groupname+'.'+newfqn)
            except mothership.ldap.LDAPError, e:
                print 'mothership encountered an error, skipping LDAP update'
                print "Error: %s" % e
                print ldap_group_entry
        else:
            print "LDAP update aborted by user input, skipping LDAP group update"
    elif not cfg.ldap_active:
        print "LDAP not active, skipping LDAP group update"
    elif ldap_group_entry:
        mothership.ldap.gupdate(cfg, newg.groupname+'.'+newfqn)
    else:
        print "No LDAP master found for %s.%s, skipping LDAP group update" % (newg.realm, newg.site_id)


    # return the new group object
    return newg


def gmodify(cfg, groupname, gid=None, description=None, sudo_cmds=None):
    """
    [description]
    modify group information

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        groupname: the name of the group we want to display
    optional:
        gid: the gid we want to assign the group
        description: short description for the group

    [return value]
    no explicit return
    """

    g = mothership.validate.v_get_group_obj(cfg, groupname)

    # if the group exists, modify its data
    if g:
        if gid:
            # check to see if the target gid exists
            badgid = cfg.dbsess.query(Groups).\
            filter(Groups.gid==gid).\
            filter(Groups.site_id==g.site_id).\
            filter(Groups.realm==g.realm).first()
            if badgid:
                # if it exists, let's not stomp all over it
                raise UsersError("target gid \"%s\" exists in %s.%s, aborting!" % (gid, g.realm, g.site_id))
            else:
                g.gid = gid
        else:
            pass
        if description:
            g.description = description
        else:
            pass
        if sudo_cmds:
            g.sudo_cmds = sudo_cmds
        else:
            g.sudo_cmds = None
        # ask for verification before modification
        ans = raw_input("to modify this group please type \"modify_%s\": " % groupname)
        if ans != "modify_%s" % groupname:
            raise UsersError("aborting modify!")
        else:
            # update the db with the new info
            cfg.dbsess.add(g)
            cfg.dbsess.commit()
            print "updated info:"
            gdisplay(cfg, groupname=g.groupname+'.'+g.realm+'.'+g.site_id)
    else:
        raise UsersError("group \"%s\" not found, aborting" % groupname)
    # update ldap data
    ldap_master = mothership.ldap.get_master(cfg, g.realm+'.'+g.site_id)
    if cfg.ldap_active and ldap_master:
        ans = raw_input('Do you want to update this group in LDAP as well? (y/n): ')
        if ans == 'y' or ans == 'Y':
            try:
                print "updating \"%s\" in LDAP" % (g.groupname+'.'+g.realm+'.'+g.site_id)
                mothership.ldap.gupdate(cfg, groupname=g.groupname+'.'+g.realm+'.'+g.site_id)
            except mothership.ldap.LDAPError, e:
                print 'mothership encountered an error, skipping LDAP update'
                print "Error: %s" % e
        else:
            print "LDAP update aborted by user input, skipping."
    elif not cfg.ldap_active:
        print "LDAP not active, skipping"
    else:
        print "No LDAP master found for %s.%s, skipping" % (g.realm, g.site_id)


def get_gid(cfg, groupname):
    """
    [description]
    gets and returns the GID for a given groupname 

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        groupname: the name of the group we want to find the GID for 

    [return value]
    returns an integer representing the GID of the group if successful
    returns False if unsuccessful
    """

    # validate/construct/get the realm.site_id.domain data
    fqgn = mothership.validate.v_get_fqn(cfg, name=groupname)
    groupname, realm, site_id, domain = mothership.validate.v_split_fqn(fqgn)
    # gather group data
    g = cfg.dbsess.query(Groups).\
    filter(Groups.groupname==groupname).\
    filter(Groups.site_id==site_id).\
    filter(Groups.realm==realm).first()
    if g:
        return g.gid
    else:
        return False


def get_uid(cfg, username):
    """
    [description]
    gets and returns the UID for a given username 

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the name of the user we want to find the UID for 

    [return value]
    returns an integer representing the UID of the group if successful
    returns False if unsuccessful
    """

    # validate/construct/get the realm.site_id.domain data
    fqun = mothership.validate.v_get_fqn(cfg, name=username)
    username, realm, site_id, domain = mothership.validate.v_split_fqn(fqun)

    # gather user data
    u = cfg.dbsess.query(Users).\
    filter(Users.username==username).\
    filter(Users.site_id==site_id).\
    filter(Users.realm==realm).first()
    if u:
        return u.uid
    else:
        return False


def get_utog_map(cfg, username, groupname):
    """
    [description]
    gets and returns the ID for a given username to groupname mapping

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        username: the name of the user we want to find the mapping for
        groupname: the name of the group we want to find the mapping for

    [return value]
    returns an integer representing the row ID for the user-to-group mapping in the user_group_mapping table
    returns False if unsuccessful
    """

    # validate/construct/get the realm.site_id.domain data
    fqun = mothership.validate.v_get_fqn(cfg, name=username)
    username, realm, site_id, domain = mothership.validate.v_split_fqn(fqun)
    # get user
    u = cfg.dbsess.query(Users).\
    filter(Users.username==username).\
    filter(Users.site_id==site_id).\
    filter(Users.realm==realm).first()

    # get group
    g = cfg.dbsess.query(Groups).\
    filter(Groups.groupname==groupname).\
    filter(Groups.site_id==site_id).\
    filter(Groups.realm==realm).first()

    if u and g:
        # get mapping
        m = cfg.dbsess.query(UserGroupMapping).\
        filter(UserGroupMapping.users_id==u.id).\
        filter(UserGroupMapping.groups_id==g.id).first()
        if m:
            return m.id
        else:
            return False
    elif u and not g:
        "group not found in get_utog_map()"
        return False
    elif g and not u:
        "user not found in get_utog_map()"
        return False
    else:
        print 'neither group nor user found in get_utog_map()'
        return False

def gen_sudoers_groups(cfg, unqdn):
    """
    [description]
    generates the group lines for sudoers

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        unqdn: the unqualified domain name of the host we want to generate for

    [return value]
    no configured return (standard success/fail)
    """

    # get the server entry
    s = mothership.validate.v_get_host_obj(cfg, unqdn)
    if s:
        unqdn = '.'.join([s.hostname,s.realm,s.site_id])
        fqdn = '.'.join([unqdn,cfg.domain])
    else:
        raise UsersError("Host does not exist: %s" % unqdn)

    kvs = mothership.kv.collect(cfg, fqdn, key='tag')
    groups = []

    # get sudo groups for all tags in kv
    for kv in kvs:
        unqgn = kv.value+'_sudo.'+s.realm+'.'+s.site_id
        g = mothership.validate.v_get_group_obj(cfg, unqgn)
        if g:
            groups.append(g)
        else:
            pass

    # get sudo group for primary tag
    g = mothership.validate.v_get_group_obj(cfg, s.tag+'_sudo.'+s.realm+'.'+s.site_id)
    if g:
        groups.append(g)
    else:
        pass

    # stitch it all together
    sudoers = []
    for g in groups:
        if cfg.sudo_nopass and g.sudo_cmds:
            sudoers.append("%%%s ALL=(ALL) NOPASSWD:%s" % (g.groupname, g.sudo_cmds))
        elif g.sudo_cmds:
            sudoers.append("%%%s ALL=(ALL) %s" % (g.groupname, g.sudo_cmds))
        else:
            pass
    if sudoers:
        return sudoers
    else:
        return None
