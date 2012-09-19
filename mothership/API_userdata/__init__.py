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
    mothership.API_userdata

    Package for interacting with user and group data in mothership
"""

from sqlalchemy import or_, desc, MetaData

import mothership
from mothership.mothership_models import *
from mothership.common import *
#from mothership.API_list_servers import *
#from mothership.API_kv import *
from mothership.validate import *

class UserdataError(Exception):
    pass

class API_userdata:

    def __init__(self, cfg):
        self.cfg = cfg
        self.version = 1
        self.namespace = 'API_userdata'
        self.metadata = {
            'config': {
                'shortname': 'ud',
                'description': 'allows for the creation and manipulation of users and groups within mothership',
                'module_dependencies': {
                    'common': 1,
                },
            },
            'methods': {
                'udisplay': {
                    'description': 'display a user\'s info',
                    'rest_type': 'GET',
                    'admin_only': False,
                    'required_args': {
                        'args': {
                            'unqun': {
                                'vartype': 'str',
                                'desc': 'username.realm.site_id of the user',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'user': 'ORMobject',
                        'groups': [
                            'group ORMobject',
                            'group ORMobject',
                        ],
                    },
                },
                'uadd': {
                    'description': 'create a user entry in the user table',
                    'rest_type': 'POST',
                    'admin_only': True,
                    'required_args': {
                        'args': {
                            'unqun': {
                                'vartype': 'str',
                                'desc': 'username.realm.site_id of the user to add to the database',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 8,
                        'args': {
                            'first_name': {
                                'vartype': 'str',
                                'desc': 'user\'s first name (default John)',
                                'ol': 'f',
                            },
                            'last_name': {
                                'vartype': 'str',
                                'desc': 'user\'s last name (default Doe)',
                                'ol': 'l',
                            },
                            'ssh_key': {
                                'vartype': 'file',
                                'desc': 'a file containing the user\'s ssh key(s)',
                                'ol': 'k',
                            },
                            'shell': {
                                'vartype': 'str',
                                'desc': "user's shell (default: %s)" % cfg.shell,
                                'ol': 's',
                            },
                            'email_address': {
                                'vartype': 'str',
                                'desc': "user's email address (default: username@%s)" % cfg.email_domain,
                                'ol': 'e',
                            },
                            'home_dir': {
                                'vartype': 'str',
                                'desc': "user's home directory (default: %s/username)" % cfg.hdir,
                                'ol': 'd',
                            },
                            'user_type': {
                                'vartype': 'str',
                                'desc': "user type, pick one of: %s (default: %s)" % (" ".join(cfg.user_types), cfg.def_user_type),
                                'ol': 't',
                            },
                            'uid': {
                                'vartype': 'str',
                                'desc': "user's uid (default will pick the next available uid)",
                                'ol': 'i',
                            },
                        },
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'udelete': {
                    'description': 'delete a user entry from the users table',
                    'rest_type': 'DELETE',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'unqun': {
                                'vartype': 'str',
                                'desc': 'username.realm.site_id of the user to delete from the database',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'umodify': {
                    'description': 'modify an existing user entry',
                    'rest_type': 'PUT',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'unqun': {
                                'vartype': 'str',
                                'desc': 'username.realm.site_id of the user to modify',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 9,
                        'args': {
                            'first_name': {
                                'vartype': 'str',
                                'desc': 'user\'s first name (default John)',
                                'ol': 'f',
                            },
                            'last_name': {
                                'vartype': 'str',
                                'desc': 'user\'s last name (default Doe)',
                                'ol': 'l',
                            },
                            'ssh_key': {
                                'vartype': 'file',
                                'desc': 'a file containing the user\'s ssh key(s)',
                                'ol': 'k',
                            },
                            'shell': {
                                'vartype': 'str',
                                'desc': "user's shell (default: %s)" % cfg.shell,
                                'ol': 's',
                            },
                            'email_address': {
                                'vartype': 'str',
                                'desc': "user's email address (default: username@%s)" % cfg.email_domain,
                                'ol': 'e',
                            },
                            'home_dir': {
                                'vartype': 'str',
                                'desc': "user's home directory (default: %s/username)" % cfg.hdir,
                                'ol': 'd',
                            },
                            'user_type': {
                                'vartype': 'str',
                                'desc': "user type, pick one of: %s (default: %s)" % (" ".join(cfg.user_types), cfg.def_user_type),
                                'ol': 't',
                            },
                            'uid': {
                                'vartype': 'str',
                                'desc': "user's uid (default will pick the next available uid)",
                                'ol': 'i',
                            },
                            'active': {
                                'vartype': 'str',
                                'desc': "true/false (or t/f), activate/deactivate. deactivate the user to disable without removing the user info from mothership",
                                'ol': 'a',
                            },
                        },
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'uclone': {
                    'description': 'clone a user from one realm.site_id to another',
                    'rest_type': 'POST',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'unqun': {
                                'vartype': 'str',
                                'desc': 'username.realm.site_id of the user to clone from',
                               'ol': 'u',
                            },
                            'newunqn': {
                                'vartype': 'str',
                                'desc': 'realm.site_id to clone the user into',
                                'ol': 'n',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'gdisplay': {
                    'description': 'display a group\'s info',
                    'rest_type': 'GET',
                    'admin_only': False,
                    'required_args': {
                        'args': {
                            'unqgn': {
                                'vartype': 'str',
                                'desc': 'name.realm.site_id of the group',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'group': 'ORMobject',
                        'users': [
                            'user ORMobject',
                            'user ORMobject',
                        ],
                    },
                },
                'gadd': {
                    'description': 'create a group entry in the group table',
                    'rest_type': 'POST',
                    'admin_only': True,
                    'required_args': {
                        'args': {
                            'unqgn': {
                                'vartype': 'str',
                                'desc': 'group.realm.site_id of the group to add to the database',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 3,
                        'args': {
                            'description': {
                                'vartype': 'str',
                                'desc': 'a description of the group',
                                'ol': 'd',
                            },
                            'sudo_cmds': {
                                'vartype': 'str',
                                'desc': 'commands users of this group are allowd to run as root',
                                'ol': 's',
                            },
                            'gid': {
                                'vartype': 'str',
                                'desc': 'group id number to assign to the group',
                                'ol': 'g',
                            },
                        },
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'gdelete': {
                    'description': 'delete a group entry from the groups table',
                    'rest_type': 'DELETE',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'unqgn': {
                                'vartype': 'str',
                                'desc': 'groupname.realm.site_id of the group to delete from the database',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'gmodify': {
                    'description': 'modify an existing group entry',
                    'rest_type': 'PUT',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'unqgn': {
                                'vartype': 'str',
                                'desc': 'groupname.realm.site_id of the group to modify',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 3,
                        'args': {
                            'description': {
                                'vartype': 'str',
                                'desc': 'a description of the group',
                                'ol': 'd',
                            },
                            'sudo_cmds': {
                                'vartype': 'str',
                                'desc': 'commands users of this group are allowd to run as root',
                                'ol': 's',
                            },
                            'gid': {
                                'vartype': 'str',
                                'desc': 'group id number to assign to the group',
                                'ol': 'g',
                            },
                        },
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'gclone': {
                    'description': 'clone a group from one realm.site_id to another',
                    'rest_type': 'POST',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'unqgn': {
                                'vartype': 'str',
                                'desc': 'groupname.realm.site_id of the group to clone from',
                               'ol': 'u',
                            },
                            'newunqn': {
                                'vartype': 'str',
                                'desc': 'realm.site_id to clone the group into',
                                'ol': 'n',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'utog': {
                    'description': 'map a username.realm.site_id to group in the same realm.site_id',
                    'rest_type': 'POST',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'unqun': {
                                'vartype': 'str',
                                'desc': 'username.realm.site_id of the user to map',
                               'ol': 'u',
                            },
                            'groupname': {
                                'vartype': 'str',
                                'desc': 'groupname (without the realm.site_id) to map the user to',
                                'ol': 'g',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'urmg': {
                    'description': 'remove a username.realm.site_id from a group in the same realm.site_id',
                    'rest_type': 'POST',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'unqun': {
                                'vartype': 'str',
                                'desc': 'username.realm.site_id of the user to unmap',
                               'ol': 'u',
                            },
                            'groupname': {
                                'vartype': 'str',
                                'desc': 'groupname (without the realm.site_id) to remove the user from',
                                'ol': 'g',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'string': 'success',
                    },
                },
            },
        }


    #############################
    # user manipulation methods #
    #############################

    def udisplay(self, query):
        """
        [description]
        display the information for a user 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns the user ORMobject and a list of group ORMobjects if successful, raises an error if unsuccessful 
        """
        try:
            # setting our valid query keys
            common = MothershipCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'udisplay')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/udisplay: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/udisplay: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # to make our conditionals easier
            if 'unqun' not in query.keys() or not query['unqun']:
                self.cfg.log.debug("API_useradata/udisplay: no username.realm.site_id provided!")
                raise UserdataError("API_useradata/udisplay: no username.realm.site_id provided!")
            else:
                unqun = query['unqun']
            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'udisplay')
            # find us a username to display, validation done in the __get_user_obj function
            try:
                u = self.__get_user_obj(unqun) 
            except:
                self.cfg.log.debug("API_userdata/udisplay: user %s not found." % unqun)
                raise UserdataError("API_userdata/udisplay: user %s not found" % unqun)
            # got a user, populate the return 
            ret = {}
            if u:
                ret['user'] = u.to_dict()
            else:
                self.cfg.log.debug("API_userdata/udisplay: user %s not found." % unqun)
                raise UserdataError("API_userdata/udisplay: user %s not found" % unqun)
            # user exists, find out what groups it's in 
            ret['groups'] = []
            glist = self.__get_groups_by_user(unqun)
            if glist:
                for g in glist:
                    ret['groups'].append(g.to_dict())        
            # return's populated, return it
            return ret
        except Exception, e:
            self.cfg.log.debug("API_userdata/udisplay: %s" % e) 
            raise UserdataError("API_userdata/udisplay: %s" % e) 


    def uadd(self, query, files=None):
        """
        [description]
        create a new Users entry

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns "success" if successful, raises an error if not
        """
        # setting our valid query keys
        common = MothershipCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'uadd')

        try:
            # to make our conditionals easier
            if 'unqun' not in query.keys() or not query['unqun']:
                self.cfg.log.debug("API_useradata/uadd: no username.realm.site_id provided!")
                raise UserdataError("API_useradata/uadd: no username.realm.site_id provided!")
            else:
                unqun = query['unqun']


            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/uadd: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/uadd: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'uadd')
            # first name, validate or default
            if 'first_name' in query.keys() and query['first_name']:
                first_name = query['first_name']
                v_name(first_name)
            else:
                first_name = "John"
            # last name, validate or default
            if 'last_name' in query.keys() and query['last_name']:
                last_name = query['last_name']
                v_name(last_name)
            else:
                last_name = "Doe"
            # user type, validate or default
            if 'user_type' in query.keys() and query['user_type']:
                user_type = query['user_type']
                if user_type not in self.cfg.user_types:
                    self.cfg.log.debug("API_userdata/uadd: Invalid user type, please use one of the following: " + ', '.join(self.cfg.user_types))
                    raise UserdataError("API_userdata/uadd: Invalid user type, please use one of the following: " + ', '.join(self.cfg.user_types))
            else:
                user_type = self.cfg.def_user_type
            # shell, assign or default
            if 'shell' in query.keys() and query['shell']:
                shell = query['shell']
            else:
                shell = self.cfg.shell
            # ssh_keys file, validate or assign empty string 
            if files:
                if len(files) > 1:
                    self.cfg.log.debug("API_userdata/uadd: too many files uploaded for ssh_keys, refusing to continue")
                    raise UserdataError("API_userdata/uadd: too many files uploaded for ssh_keys, refusing to continue")
                ssh_keys = []
                for key in files[0].readlines():
                    if v_ssh2_pubkey(key):
                        ssh_keys.append(key)
                ssh_public_key = ''.join(ssh_keys).rstrip()
            else:
                ssh_public_key = "" 

            # input validation for username
            username, realm, site_id = v_split_unqn(unqun)
            if username and realm and site_id:
                v_name(username)
                v_realm(self.cfg, realm)
                v_site_id(self.cfg, site_id)
            else:
                self.cfg.log.debug("API_userdata/uadd: unqun must be in the format username.realm.site_id. unqun: %s" % unqun)
                raise UserdataError("API_userdata/uadd: unqun must be in the format username.realm.site_id. unqun: %s" % unqun)

            # make sure we're not trying to add a duplicate, validation done in the __get_user_obj function
            u = self.__get_user_obj(unqun) 
            if u:
                self.cfg.log.debug("API_userdata/uadd: user exists already: %s" % unqun)
                raise UserdataError("API_userdata/uadd: user exists already: %s" % unqun)
           
            # this is down here instead of up above with its buddies because we need the
            # username to construct a home dir and email if they're not supplied 
            if 'home_dir' in query.keys() and query['home_dir']:
                home_dir = query['home_dir']
            else:
                home_dir = "%s/%s" % (self.cfg.hdir, username)
            if 'email_address' in query.keys() and query['email_address']:
                email_address = query['email_address']
            else:
                email_address = "%s@%s" % (username, self.cfg.email_domain) 
            # uid, validate or generate
            # this is down here instead of up above with its buddies because we need the
            # realm and site_id to query for existing uids
            if 'uid' in query.keys() and query['uid']:
                uid = int(query['uid'])
                v_uid(self.cfg, uid)
                if v_uid_in_db(self.cfg, uid, realm, site_id):
                    self.cfg.log.debug("API_userdata/uadd: uid exists already: %s" % uid)
                    raise UserdataError("API_userdata/uadd: uid exists already: %s" % uid)
            else:
                uid = self.__next_available_uid(realm, site_id)

            # deal with default groups
            dg = []
            if self.cfg.default_groups:
                for grp in self.cfg.default_groups:
                    try:
                        # see if our default group(s) exist
                        g = self.__get_group_obj("%s.%s.%s" % (grp, realm, site_id))
                        if g:
                            dg.append(g)
                        else:
                            # if not, explode
                            self.cfg.log.debug("API_userdata/uadd: default groups must exist before we can add users to them! missing group: %s.%s.%s" % (grp, realm, site_id))
                            raise UserdataError("API_userdata/uadd: default groups must exist before we can add users to them! missing group: %s.%s.%s" % (grp, realm, site_id))
                    except:
                        # if anything goes wrong, explode.
                        self.cfg.log.debug("API_userdata/uadd: default groups must exist before we can add users to them! missing group: %s.%s.%s" % (grp, realm, site_id))
                        raise UserdataError("API_userdata/uadd: default groups must exist before we can add users to them! missing group: %s.%s.%s" % (grp, realm, site_id))

            # create the user object, push it to the db, return status
            u = Users(first_name, last_name, ssh_public_key, username, site_id, realm, uid, user_type, home_dir, shell, email_address, active=True)
            self.cfg.dbsess.add(u)
            self.cfg.dbsess.commit()
            # if our default group(s) exist, shove the user into it/them
            if dg:
                for g in dg:
                    ugquery = {'unqun': unqun, 'groupname': g.groupname}
                    self.utog(ugquery)
                    self.cfg.log.debug("API_userdata/uadd: adding user %s to default group %s" % (unqun, g.groupname))
            return 'success'
        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/uadd: error: %s" % e)
            raise UserdataError("API_userdata/uadd: error: %s" % e)


    def udelete(self, query):
        """
        [description]
        delete a user from the users table

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns "success" if successful, None if unsuccessful 
        """
        try:
            # to make our conditionals easier
            if 'unqun' not in query.keys() or not query['unqun']:
                self.cfg.log.debug("API_useradata/udelete: no username.realm.site_id provided!")
                raise UserdataError("API_useradata/udelete: no username.realm.site_id provided!")
            else:
                unqun = query['unqun']

            # setting our valid query keys
            common = MothershipCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'udelete')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/udelete: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/udelete: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'udelete')
            # find us a username to delete, validation done in the __get_user_obj function
            u = self.__get_user_obj(unqun) 
            if u:
                if self.__get_groups_by_user(unqun):
                    self.cfg.log.debug("API_userdata/udelete: please remove user from all groups before deleting!")
                    raise UserdataError("API_userdata/udelete: please remove user from all groups before deleting!")
                self.cfg.dbsess.delete(u)
                self.cfg.dbsess.commit()
                self.cfg.log.debug("API_userdata/udelete: deleted user: %s" % unqun)
                return "success"
            else:
                self.cfg.log.debug("API_userdata/udelete: user not found: %s" % unqun)
                raise UserdataError("API_userdata/udelete: user not found: %s" % unqun)

        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/udelete: error: %s" % e)
            raise UserdataError("API_userdata/udelete: error: %s" % e)


    def umodify(self, query, files=None):
        """
        [description]
        create a new tags entry

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns true if successful, raises an error if not
        """
        # setting our valid query keys
        common = MothershipCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'umodify')

        try:
            # to make our conditionals easier
            if 'unqun' not in query.keys() or not query['unqun']:
                self.cfg.log.debug("API_useradata/umodify: no username.realm.site_id provided!")
                raise UserdataError("API_useradata/umodify: no username.realm.site_id provided!")
            else:
                unqun = query['unqun']

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/umodify: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/umodify: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'umodify')
            # find us a username to modify, validation done in the __get_user_obj function
            u = self.__get_user_obj(unqun) 
            if not u:
                self.cfg.log.debug("API_userdata/umodify: refusing to modify nonexistent user: %s" % unqun)
                raise UserdataError("API_userdata/umodify: refusing to modify nonexistent user: %s" % unqun)
           
            # first name, validate or leave alone 
            if 'first_name' in query.keys() and query['first_name']:
                v_name(query['first_name'])
                u.first_name = query['first_name']
            # last name, validate or leave alone 
            if 'last_name' in query.keys() and query['last_name']:
                v_name(query['last_name'])
                u.last_name = query['last_name']
            # user type, validate or leave alone 
            if 'user_type' in query.keys() and query['user_type']:
                if query['user_type'] not in self.cfg.user_types:
                    self.cfg.log.debug("API_userdata/umodify: Invalid user type, please use one of the following: " + ', '.join(self.cfg.user_types))
                    raise UserdataError("API_userdata/umodify: Invalid user type, please use one of the following: " + ', '.join(self.cfg.user_types))
                else:
                    u.user_type = query['user_type']
            # shell, assign or leave alone 
            if 'shell' in query.keys() and query['shell']:
                u.shell = query['shell']
            # ssh_keys file, validate or leave alone 
            if files:
                if len(files) > 1:
                    self.cfg.log.debug("API_userdata/umodify: too many files uploaded for ssh_keys, refusing to continue")
                    raise UserdataError("API_userdata/umodify: too many files uploaded for ssh_keys, refusing to continue")
                ssh_keys = []
                for key in files[0].readlines():
                    if v_ssh2_pubkey(key):
                        ssh_keys.append(key)
                u.ssh_public_key = ''.join(ssh_keys).rstrip()

            # this is down here instead of up above with its buddies because we need the
            # username to construct a home dir and email if they're not supplied 
            if 'home_dir' in query.keys() and query['home_dir']:
                u.hdir = query['home_dir']
            if 'email_address' in query.keys() and query['email_address']:
                u.email = query['email_address']
            # uid, validate or leave alone 
            if 'uid' in query.keys() and query['uid']:
                if u.uid != int(query['uid']) and v_uid_in_db(self.cfg, int(query['uid']), u.realm, u.site_id):
                    self.cfg.log.debug("API_userdata/umodify: uid exists already: %s" % query['uid'])
                    raise UserdataError("API_userdata/umodify: uid exists already: %s" % query['uid'])
                u.uid = int(query['uid'])

            # activate/deactivate the user
            if 'active' in query.keys() and query['active'] in ['F', 'f', 'False', 'false']:
                u.active = False
            elif 'active' in query.keys() and query['active'] in ['T', 't', 'True', 'true']:
                u.active = True

            # push the modified user object to the db, return status
            self.cfg.dbsess.add(u)
            self.cfg.dbsess.commit()
            return 'success'
        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/umodify: error: %s" % e)
            raise UserdataError("API_userdata/umodify: error: %s" % e)


    def uclone(self, query):
        """
        [description]
        delete a user from the users table

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns "success" if successful, None if unsuccessful 
        """
        try:
            # to make our conditionals easier
            if 'unqun' not in query.keys() or not query['unqun']:
                self.cfg.log.debug("API_useradata/uclone: no username.realm.site_id provided!")
                raise UserdataError("API_useradata/uclone: no username.realm.site_id provided!")
            else:
                unqun = query['unqun']
            if 'newunqn' not in query.keys() or not query['newunqn']:
                self.cfg.log.debug("API_useradata/uclone: no new realm.site_id provided!")
                raise UserdataError("API_useradata/uclone: no new realm.site_id provided!")
            else:
                newunqn = query['newunqn']

            # setting our valid query keys
            common = MothershipCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'uclone')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/uclone: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/uclone: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # input validation for new realm.site_id
            blank, nrealm, nsite_id = v_split_unqn(newunqn)
            if nrealm and nsite_id:
                v_realm(self.cfg, nrealm)
                v_site_id(self.cfg, nsite_id)
            else:
                self.cfg.log.debug("API_userdata/uclone: newunqn must be in the format realm.site_id. newunqn: %s" % newunqn)
                raise UserdataError("API_userdata/uclone: newunqn must be in the format realm.site_id. newunqn: %s" % newunqn)

            # find us a username to clone, validation done in the __get_user_obj function
            u = self.__get_user_obj(unqun) 
            if u:
                newunqun = "%s.%s.%s" % (u.username, nrealm, nsite_id)
                query = {
                    'unqun': newunqun,
                    'first_name': u.first_name,
                    'last_name': u.last_name,
                    'uid': u.uid,
                    'user_type': u.type,
                    'shell': u.shell,
                    'email_address': u.email,
                    'ssh_key': u.ssh_public_key,
                    'home_dir': u.hdir,
                }
                self.uadd(query)
                self.cfg.log.debug("API_userdata/uclone: created user: %s" % newunqun)
                return "success"
            else:
                self.cfg.log.debug("API_userdata/uclone: user not found: %s" % unqun)
                raise UserdataError("API_userdata/uclone: user not found: %s" % unqun)
        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/uclone: error: %s" % e)
            raise UserdataError("API_userdata/uclone: error: %s" % e)



    ##############################
    # group manipulation methods #
    ##############################

    def gdisplay(self, query):
        """
        [description]
        display the information for a group 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns the group ORMobject dict if successful, raises an error if unsuccessful
        """
        try:
            # setting our valid query keys
            common = MothershipCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'gdisplay')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/gdisplay: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/gidsplay: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # to make our conditionals easier
            if 'unqgn' not in query.keys() or not query['unqgn']:
                self.cfg.log.debug("API_useradata/gdisplay: no groupname.realm.site_id provided!")
                raise UserdataError("API_useradata/gdisplay: no groupname.realm.site_id provided!")
            else:
                unqgn = query['unqgn']
            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'gdisplay')
            # look for the group
            try:
                g = self.__get_group_obj(unqgn) 
            except Exception, e:
                self.cfg.log.debug("API_userdata/gdisplay: group %s not found." % unqgn)
                raise UserdataError("API_userdata/gdisplay: group %s not found" % unqgn)
            # group exists, populate return
            ret = {} 
            if g:
                ret['group'] = g.to_dict()
            else:
                self.cfg.log.debug("API_userdata/gdisplay: group %s not found." % unqgn)
                raise UserdataError("API_userdata/gdisplay: group %s not found" % unqgn)
            # now that we know the group exists, we can see if it's populated with users
            ret['users'] = []
            ulist = self.__get_users_by_group(unqgn)
            if ulist:
                for u in ulist:
                    ret['users'].append(u.to_dict())
            # return is populated, return it
            return ret
        except Exception, e:
            self.cfg.log.debug("API_userdata/gdisplay: %s" % e) 
            raise UserdataError("API_userdata/gdisplay: %s" % e) 


    def gadd(self, query, files=None):
        """
        [description]
        create a new tags entry

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns true if successful, raises an error if not
        """
        # setting our valid query keys
        common = MothershipCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'gadd')

        try:
            # to make our conditionals easier
            if 'unqgn' not in query.keys() or not query['unqgn']:
                self.cfg.log.debug("API_useradata/gadd: no groupname.realm.site_id provided!")
                raise UserdataError("API_useradata/gadd: no groupname.realm.site_id provided!")
            else:
                unqgn = query['unqgn']


            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/gadd: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/gadd: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'gadd')
            # description, assign or default
            if 'description' in query.keys() and query['description']:
                description = query['description']
            else:
                description = 'Please add a description for this group!' 

            # sudo commands. if "all" (case insensetive), translate to "ALL". if not and not blank, assign.  
            if 'sudo_cmds' in query.keys() and query['sudo_cmds']:
                sudo_cmds = query['sudo_cmds']
                if sudo_cmds.upper() == 'ALL':
                    sudo_cmds = 'ALL'
            else:
                sudo_cmds = None

            # input validation for groupname
            groupname, realm, site_id = v_split_unqn(unqgn)
            if groupname and realm and site_id:
                v_name(groupname)
                v_realm(self.cfg, realm)
                v_site_id(self.cfg, site_id)
            else:
                self.cfg.log.debug("API_userdata/gadd: unqgn must be in the format groupname.realm.site_id. unqun: %s" % unqgn)
                raise UserdataError("API_userdata/gadd: unqgn must be in the format groupname.realm.site_id. unqun: %s" % unqgn)

            # make sure we're not trying to add a duplicate
            g = self.__get_group_obj(unqgn) 
            if g:
                self.cfg.log.debug("API_userdata/gadd: group exists already: %s" % unqgn)
                raise UserdataError("API_userdata/gadd: group exists already: %s" % unqgn)
           
            # gid, validate or generate
            # this is down here instead of up above with its buddies because we need the
            # realm and site_id to query for existing uids
            if 'gid' in query.keys() and query['gid']:
                gid = int(query['gid'])
                v_gid(self.cfg, gid)
                if v_gid_in_db(self.cfg, gid, realm, site_id):
                    self.cfg.log.debug("API_userdata/gadd: gid exists already: %s" % gid)
                    raise UserdataError("API_userdata/gadd: gid exists already: %s" % gid)
            else:
                gid = self.__next_available_gid(realm, site_id)

            # create the group object, push it to the db, return status
            g = Groups(description, sudo_cmds, groupname, site_id, realm, gid)
            self.cfg.dbsess.add(g)
            self.cfg.dbsess.commit()
            return 'success'
        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/gadd: error: %s" % e)
            raise UserdataError("API_userdata/gadd: error: %s" % e)


    def gdelete(self, query):
        """
        [description]
        delete a group from the groups table

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns "success" if successful, None if unsuccessful 
        """
        try:
            # to make our conditionals easier
            if 'unqgn' not in query.keys() or not query['unqgn']:
                self.cfg.log.debug("API_userdata/gdelete: no groupname.realm.site_id provided!")
                raise UserdataError("API_userdata/gdelete: no groupname.realm.site_id provided!")
            else:
                unqgn = query['unqgn']

            # setting our valid query keys
            common = MothershipCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'gdelete')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/gdelete: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/gdelete: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'gdelete')
            # find us a groupname to delete, validation done in the __get_group_obj function
            g = self.__get_group_obj(unqgn) 
            if g:
                if self.__get_users_by_group(unqgn):
                    self.cfg.log.debug("API_userdata/gdelete: please remove all users from this group before deleting!")
                    raise UserdataError("API_userdata/gdelete: please remove all users from this group before deleting!")
                self.cfg.dbsess.delete(g)
                self.cfg.dbsess.commit()
                self.cfg.log.debug("API_userdata/gdelete: deleted group: %s" % unqgn)
                return "success"
            else:
                self.cfg.log.debug("API_userdata/gdelete: group not found: %s" % unqgn)
                raise UserdataError("API_userdata/gdelete: group not found: %s" % unqgn)

        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/gdelete: error: %s" % e)
            raise UserdataError("API_userdata/gdelete: error: %s" % e)


    def gmodify(self, query, files=None):
        """
        [description]
        create a new tags entry

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns true if successful, raises an error if not
        """
        # setting our valid query keys
        common = MothershipCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'gmodify')

        try:
            # to make our conditionals easier
            if 'unqgn' not in query.keys() or not query['unqgn']:
                self.cfg.log.debug("API_userdata/gmodify: no groupname.realm.site_id provided!")
                raise UserdataError("API_userdata/gmodify: no groupname.realm.site_id provided!")
            else:
                unqgn = query['unqgn']

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/gmodify: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/gmodify: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'gmodify')
            # find us a groupname to modify, validation done in the __get_group_obj function
            g = self.__get_group_obj(unqgn) 
            if not g:
                self.cfg.log.debug("API_userdata/gmodify: refusing to modify nonexistent group: %s" % unqgn)
                raise UserdataError("API_userdata/gmodify: refusing to modify nonexistent group: %s" % unqgn)
           
            # description, assign or leave alone
            if 'description' in query.keys() and query['description']:
                g.description = query['description']

            # sudo commands. if "all" (case insensetive), translate to "ALL". if not and not blank, assign
            if 'sudo_cmds' in query.keys() and query['sudo_cmds']:
                g.sudo_cmds = query['sudo_cmds']
                if g.sudo_cmds.upper() == 'ALL':
                    g.sudo_cmds = 'ALL'

            # gid, validate or leave alone 
            if 'gid' in query.keys() and query['gid']:
                if g.gid != int(query['gid']) and v_gid_in_db(self.cfg, int(query['gid']), g.realm, g.site_id):
                    self.cfg.log.debug("API_userdata/gmodify: gid exists already: %s" % query['gid'])
                    raise UserdataError("API_userdata/gmodify: gid exists already: %s" % query['gid'])
                g.gid = int(query['gid'])

            # push the modified group object to the db, return status
            self.cfg.dbsess.add(g)
            self.cfg.dbsess.commit()
            return 'success'
        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/gmodify: error: %s" % e)
            raise UserdataError("API_userdata/gmodify: error: %s" % e)


    def gclone(self, query):
        """
        [description]
        delete a group from the groups table

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns "success" if successful, None if unsuccessful 
        """
        try:
            # to make our conditionals easier
            if 'unqgn' not in query.keys() or not query['unqgn']:
                self.cfg.log.debug("API_userdata/gclone: no groupname.realm.site_id provided!")
                raise UserdataError("API_userdata/gclone: no groupname.realm.site_id provided!")
            else:
                unqgn = query['unqgn']
            if 'newunqn' not in query.keys() or not query['newunqn']:
                self.cfg.log.debug("API_userdata/gclone: no new realm.site_id provided!")
                raise UserdataError("API_userdata/gclone: no new realm.site_id provided!")
            else:
                newunqn = query['newunqn']

            # setting our valid query keys
            common = MothershipCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'gclone')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/gclone: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/gclone: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # input validation for new realm.site_id
            blank, nrealm, nsite_id = v_split_unqn(newunqn)
            if nrealm and nsite_id:
                v_realm(self.cfg, nrealm)
                v_site_id(self.cfg, nsite_id)
            else:
                self.cfg.log.debug("API_userdata/gclone: newunqn must be in the format realm.site_id. newunqn: %s" % newunqn)
                raise UserdataError("API_userdata/gclone: newunqn must be in the format realm.site_id. newunqn: %s" % newunqn)

            # find us a groupname to clone, validation done in the __get_group_obj function
            g = self.__get_group_obj(unqgn) 
            if g:
                newg = Groups(g.description, g.sudo_cmds, g.groupname, nsite_id, nrealm, g.gid)
                self.cfg.dbsess.add(newg)
                self.cfg.dbsess.commit()
                self.cfg.log.debug("API_userdata/gclone: created group: %s.%s" % (newg.groupname, newunqn))
                return "success"
            else:
                self.cfg.log.debug("API_userdata/gclone: group not found: %s" % unqgn)
                raise UserdataError("API_userdata/gclone: group not found: %s" % unqgn)
        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/gclone: error: %s" % e)
            raise UserdataError("API_userdata/gclone: error: %s" % e)


    ###################################
    # user-to-group mapping functions #
    ###################################

    
    def utog(self, query):
        """
        [description]
        map a user into a group

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns "success" if successful, raises an error if unsuccessful 
        """
        try:
            # to make our conditionals easier
            if 'unqun' not in query.keys() or not query['unqun']:
                self.cfg.log.debug("API_userdata/utog: no username.realm.site_id provided!")
                raise UserdataError("API_userdata/utog: no username.realm.site_id provided!")
            if 'groupname' not in query.keys() or not query['groupname']:
                self.cfg.log.debug("API_userdata/utog: no group provided!")
                raise UserdataError("API_userdata/utog: no group provided!")

            # setting our valid query keys
            common = MothershipCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'utog')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/utog: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/tog: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'utog')
            # fetch our user and group
            u = self.__get_user_obj(query['unqun'])
            g = self.__get_group_obj("%s.%s.%s" % (query['groupname'], u.realm, u.site_id))
            if not u:
                self.cfg.log.debug("API_userdata/utog: user not found: %s" % query['unqun'])
                raise UserdataError("API_userdata/utog: user not found: %s" % query['unqun'])
            elif not g:
                self.cfg.log.debug("API_userdata/utog: group not found: %s.%s.%s" % (query['groupname'], u.realm, u.site_id))
                raise UserdataError("API_userdata/utog: group not found: %s.%s.%s" % (query['groupname'], u.realm, u.site_id))
            else:
                if self.cfg.dbsess.query(UserGroupMapping).\
                filter(UserGroupMapping.users_id==u.id).\
                filter(UserGroupMapping.groups_id==g.id).first():
                    self.cfg.log.debug("API_userdata/utog: mapping exists! refusing to create duplicate mapping")
                    raise UserdataError("API_userdata/utog: mapping exists! refusing to create duplicate mapping")
                ugmap = UserGroupMapping(g.id, u.id)
                self.cfg.dbsess.add(ugmap)
                self.cfg.dbsess.commit()
                return 'success'
        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/utog: error: %s" % e)
            raise UserdataError("API_userdata/utog: error: %s" % e)


    def urmg(self, query):
        """
        [description]
        unmap a user from a group

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns "success" if successful, raises an error if unsuccessful 
        """
        try:
            # to make our conditionals easier
            if 'unqun' not in query.keys() or not query['unqun']:
                self.cfg.log.debug("API_userdata/utog: no username.realm.site_id provided!")
                raise UserdataError("API_userdata/utog: no username.realm.site_id provided!")
            if 'groupname' not in query.keys() or not query['groupname']:
                self.cfg.log.debug("API_userdata/utog: no group provided!")
                raise UserdataError("API_userdata/utog: no group provided!")

            # setting our valid query keys
            common = MothershipCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'urmg')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/utog: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/tog: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'urmg')
            # fetch our user and group
            u = self.__get_user_obj(query['unqun'])
            g = self.__get_group_obj("%s.%s.%s" % (query['groupname'], u.realm, u.site_id))
            if not u:
                self.cfg.log.debug("API_userdata/utog: user not found: %s" % query['unqun'])
                raise UserdataError("API_userdata/utog: user not found: %s" % query['unqun'])
            elif not g:
                self.cfg.log.debug("API_userdata/utog: group not found: %s.%s.%s" % (query['groupname'], u.realm, u.site_id))
                raise UserdataError("API_userdata/utog: group not found: %s.%s.%s" % (query['groupname'], u.realm, u.site_id))
            else:
                ugmap = self.cfg.dbsess.query(UserGroupMapping).\
                filter(UserGroupMapping.users_id==u.id).\
                filter(UserGroupMapping.groups_id==g.id).first()
                if not ugmap:
                    self.cfg.log.debug("API_userdata/utog: mapping does not exist")
                    raise UserdataError("API_userdata/utog: mapping does not exist")
                self.cfg.dbsess.delete(ugmap)
                self.cfg.dbsess.commit()
                return 'success'
        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/utog: error: %s" % e)
            raise UserdataError("API_userdata/utog: error: %s" % e)


    #################################
    # internal functions below here #
    #################################

    def __get_group_obj(self, unqgn):
        """
        [description]
        for a given unqgn, fetch the group object 
    
        [parameter info]
        required:
            unqgn: the groupname we want to parse
    
        [return value]
        returns a Groups ORM object or None
        """
        try: 
            groupname, realm, site_id = v_split_unqn(unqgn)
            v_name(groupname)
            v_realm(self.cfg, realm)
            v_site_id(self.cfg, site_id)
            g = self.cfg.dbsess.query(Groups).\
            filter(Groups.groupname==groupname).\
            filter(Groups.realm==realm).\
            filter(Groups.site_id==site_id).first()
    
            if g:
                return g
            else:
                return None 
        except Exception, e:
            raise UserdataError("API_userdata/__get_group_obj: error: %s" % e)


    def __get_user_obj(self, unqun):
        """
        [description]
        for a given unqun, fetch the user object 
    
        [parameter info]
        required:
            unqun: the groupname we want to parse
    
        [return value]
        returns a Users ORM object or None
        """
        try: 
            username, realm, site_id = v_split_unqn(unqun)
            v_name(username)
            v_realm(self.cfg, realm)
            v_site_id(self.cfg, site_id)
            u = self.cfg.dbsess.query(Users).\
            filter(Users.username==username).\
            filter(Users.realm==realm).\
            filter(Users.site_id==site_id).first()
    
            if u:
                return u
            else:
                return None 
        except Exception, e:
            raise UserdataError("API_userdata/__get_group_obj: error: %s" % e)


    # semi-local. might get promoted to nonlocal some day
    def _gen_sudoers_groups(self, unqdn):
        """
        [description]
        generates the group lines for sudoers
    
        [parameter info]
        required:
            unqdn: the unqualified domain name of the host we want to generate for
    
        [return value]
        returns list of sudoers lines or None 
        """
        try:
            kvobj = mothership.API_kv.API_kv(self.cfg)
            # get the server entry
            s = mothership.validate.v_get_server_obj(self.cfg, unqdn)
            if s:
                unqdn = '.'.join([s.hostname,s.realm,s.site_id])
                # probably don't need this any more
                #fqdn = '.'.join([unqdn,self.cfg.domain])
            else:
                raise UsersError("Host does not exist: %s" % unqdn)
        
            kquery = {'unqdn': unqdn}
            kquery['key'] = 'tag'
            kvs = kvobj.collect(kquery)
            groups = []
        
            # get sudo groups for all tags in kv
            if kvs:
                for kv in kvs:
                    unqgn = kv['value']+'_sudo.'+s.realm+'.'+s.site_id
                    g = self.__get_group_obj(unqgn)
                    if g:
                        groups.append(g)
                    else:
                        pass
        
            # get sudo group for primary tag
            g = self.__get_group_obj(s.tag+'_sudo.'+s.realm+'.'+s.site_id)
            if g:
                groups.append(g)
            else:
                pass
        
            # stitch it all together
            sudoers = []
            for g in groups:
                if self.cfg.sudo_nopass and g.sudo_cmds:
                    sudoers.append("%%%s ALL=(ALL) NOPASSWD:%s" % (g.groupname, g.sudo_cmds))
                elif g.sudo_cmds:
                    sudoers.append("%%%s ALL=(ALL) %s" % (g.groupname, g.sudo_cmds))
                else:
                    pass
            if sudoers:
                return sudoers
            else:
                return None
        except Exception, e:
            raise UserdataError("API_userdata/_gen_sudoers_groups: %s" % e)


    def __next_available_uid(self, realm, site_id):
        """
        [description]
        searches the db for existing UIDS and picks the next available UID within the parameters configured in mothership.yaml
    
        [parameter info]
        required:
            realm: the realm we're checking uids for
            site_id: the site_id we're checking uids for
    
        [return value]
        returns an integer representing the next available UID
        """
        try: 
            i = self.cfg.uid_start
            uidlist = []
            u = self.cfg.dbsess.query(Users).\
            filter(Users.realm==realm).\
            filter(Users.site_id==site_id).all()
            for userentry in u:
                uidlist.append(userentry.uid)
            uidlist.sort(key=int)
            if not uidlist:
                # if we don't have any users in the users table
                # return the default first uid as configured in the yaml
                return self.cfg.uid_start
            else:
                for uu in uidlist:
                    if uu < self.cfg.uid_start:
                        pass
                    elif not i == uu and i < self.cfg.uid_end:
                        return i
                    elif i < self.cfg.uid_end:
                        i += 1
                    else:
                        self.cfg.log.debug("API_userdata/__next_available_uid: No available UIDs!")
                        raise UserdataError("API_userdata/__next_available_uid: No available UIDs!")
                return i
        except Exception, e:
            raise UserdataError("API_userdata/__next_available_uid: %s" % e)


    def __next_available_gid(self, realm, site_id):
        """
        [description]
        searches the db for existing GIDS and picks the next available GID within the parameters configured in mothership.yaml
    
        [parameter info]
        required:
            realm: the realm we're checking gids for
            site_id: the site_id we're checking gids for
    
        [return value]
        returns an integer representing the next available GID
        """
        try: 
            i = self.cfg.gid_start
            gidlist = []
            g = self.cfg.dbsess.query(Groups).\
            filter(Groups.realm==realm).\
            filter(Groups.site_id==site_id).all()
            for groupentry in g:
                gidlist.append(groupentry.gid)
            gidlist.sort(key=int)
            if not gidlist:
                # if we don't have any groups in the groups table
                # return the default first gid as configured in the yaml
                return self.cfg.gid_start
            else:
                for gg in gidlist:
                    if gg < self.cfg.gid_start:
                        pass
                    elif not i == gg and i < self.cfg.gid_end:
                        return i
                    elif i < self.cfg.gid_end:
                        i += 1
                    else:
                        self.cfg.log.debug("API_userdata/__next_available_gid: No available GIDs!")
                        raise UserdataError("API_userdata/__next_available_gid: No available GIDs!")
                return i
        except Exception, e:
            raise UserdataError("API_userdata/__next_available_gid: %s" % e)

    def __get_groups_by_user(self, unqun):
        """
        [description]
        searches the db for user-group mappings by username 
    
        [parameter info]
        required:
            unqun: the username to search for 
    
        [return value]
        returns a list of Groups ORMobjects or nothing 
        """
        try:
            glist = []
            u = self.__get_user_obj(unqun)
            if not u:
                self.cfg.log.debug("API_userdata/__get_groups_by_user: user not found: %s" % unqun)
                raise UserdataError("API_userdata/__get_groups_by_user: user not found: %s" % unqun)
            maplist = []
            maplist = self.cfg.dbsess.query(UserGroupMapping).\
                filter(UserGroupMapping.users_id==u.id).all()
            if maplist:
                for map in maplist:
                    glist.append(self.cfg.dbsess.query(Groups).filter(Groups.id==map.groups_id).first())
            return glist
        except Exception, e:
            raise UserdataError("API_userdata/__get_groups_by_user: %s" % e)


    def __get_users_by_group(self, unqgn):
        """
        [description]
        searches the db for user-group mappings by groupname 
    
        [parameter info]
        required:
            unqgn: the groupname to search for 
    
        [return value]
        returns a list of Groups ORMobjects or nothing 
        """
        try:
            ulist = []
            g = self.__get_group_obj(unqgn)
            if not g:
                self.cfg.log.debug("API_userdata/__get_users_by_group: group not found: %s" % unqgn)
                raise UserdataError("API_userdata/__get_groups_by_user: group not found: %s" % unqgn)
            maplist = []
            maplist = self.cfg.dbsess.query(UserGroupMapping).\
                filter(UserGroupMapping.groups_id==g.id).all()
            if maplist:
                for map in maplist:
                    ulist.append(self.cfg.dbsess.query(Users).filter(Users.id==map.users_id).first())
            return ulist
        except Exception, e:
            raise UserdataError("API_userdata/__get_users_by_group: %s" % e)


