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
                'description': 'allows the creation and manipulation of tags',
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
        Returns the tag ORMobject if successful, None if unsuccessful 
        """
        try:
            # setting our valid query keys
            common = MothershipCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'udisplay')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/uadd: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/uadd: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # to make our conditionals easier
            if 'unqun' not in query.keys() or not query['unqun']:
                self.cfg.log.debug("API_useradata/udisplay: no username.realm.site_id provided!")
                raise UserdataError("API_useradata/udisplay: no username.realm.site_id provided!")
            else:
                unqun = query['unqun']

            username, realm, site_id = v_split_unqn(unqun)
            if username and realm and site_id:
                v_name(username)
                v_realm(self.cfg, realm)
                v_site_id(self.cfg, site_id)
            else:
                self.cfg.log.debug("API_userdata/udisplay: unqun must be in the format username.realm.site_id. unqun: %s" % unqun)
                raise UserdataError("API_userdata/udisplay: unqun must be in the format username.realm.site_id. unqun: %s" % unqun)
            try:
                u = self.cfg.dbsess.query(Users).\
                filter(Users.username==username).\
                filter(Users.realm==realm).\
                filter(Users.site_id==site_id).first()
            except:
                self.cfg.log.debug("API_userdata/udisplay: user %s not found." % unqun)
                raise UserdataError("API_userdata/udisplay: user %s not found" % unqun)
        
            if u:
                return u.to_dict()
            else:
                self.cfg.log.debug("API_userdata/udisplay: user %s not found." % unqun)
                raise UserdataError("API_userdata/udisplay: user %s not found" % unqun)
                

        except Exception, e:
            self.cfg.log.debug("API_userdata/udisplay: %s" % e) 
            raise UserdataError("API_userdata/udisplay: %s" % e) 


    def uadd(self, query, files=None):
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

            # make sure we're not trying to add a duplicate
            u = self.cfg.dbsess.query(Users).\
            filter(Users.username==username).\
            filter(Users.realm==realm).\
            filter(Users.site_id==site_id).first()
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
                uid = query['uid']
                v_uid(self.cfg, uid)
                if v_uid_in_db(self.cfg, uid, realm, site_id):
                    self.cfg.log.debug("API_userdata/uadd: uid exists already: %s" % uid)
                    raise UserdataError("API_userdata/uadd: uid exists already: %s" % uid)
            else:
                uid = self.__next_available_uid(realm, site_id)

            # create the user object, push it to the db, return status
            u = Users(first_name, last_name, ssh_public_key, username, site_id, realm, uid, user_type, home_dir, shell, email_address, active=True)
            self.cfg.dbsess.add(u)
            self.cfg.dbsess.commit()
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
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'uadd')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/udelete: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/udelete: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # input validation for username
            username, realm, site_id = v_split_unqn(unqun)
            if username and realm and site_id:
                v_name(username)
                v_realm(self.cfg, realm)
                v_site_id(self.cfg, site_id)
            else:
                self.cfg.log.debug("API_userdata/udelete: unqun must be in the format username.realm.site_id. unqun: %s" % unqun)
                raise UserdataError("API_userdata/udelete: unqun must be in the format username.realm.site_id. unqun: %s" % unqun)

            u = self.cfg.dbsess.query(Users).\
            filter(Users.username==username).\
            filter(Users.realm==realm).\
            filter(Users.site_id==site_id).first()
            if u:
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

            # input validation for username
            username, realm, site_id = v_split_unqn(unqun)
            if username and realm and site_id:
                v_name(username)
                v_realm(self.cfg, realm)
                v_site_id(self.cfg, site_id)
            else:
                self.cfg.log.debug("API_userdata/umodify: unqun must be in the format username.realm.site_id. unqun: %s" % unqun)
                raise UserdataError("API_userdata/umodify: unqun must be in the format username.realm.site_id. unqun: %s" % unqun)

            # make sure we're updating an existing user 
            u = self.cfg.dbsess.query(Users).\
            filter(Users.username==username).\
            filter(Users.realm==realm).\
            filter(Users.site_id==site_id).first()
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
                v_uid(self.cfg, query['uid'])
                if v_uid_in_db(self.cfg, query['uid'], realm, site_id):
                    self.cfg.log.debug("API_userdata/umodify: uid exists already: %s" % query['uid'])
                    raise UserdataError("API_userdata/umodify: uid exists already: %s" % query['uid'])
                else:
                    u.uid = query['uid']

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

            # input validation for username
            username, realm, site_id = v_split_unqn(unqun)
            if username and realm and site_id:
                v_name(username)
                v_realm(self.cfg, realm)
                v_site_id(self.cfg, site_id)
            else:
                self.cfg.log.debug("API_userdata/uclone: unqun must be in the format username.realm.site_id. unqun: %s" % unqun)
                raise UserdataError("API_userdata/uclone: unqun must be in the format username.realm.site_id. unqun: %s" % unqun)

            # input validation for new realm.site_id
            blank, nrealm, nsite_id = v_split_unqn(newunqn)
            if nrealm and nsite_id:
                v_realm(self.cfg, nrealm)
                v_site_id(self.cfg, nsite_id)
            else:
                self.cfg.log.debug("API_userdata/uclone: newunqn must be in the format realm.site_id. newunqn: %s" % newunqn)
                raise UserdataError("API_userdata/uclone: newunqn must be in the format realm.site_id. newunqn: %s" % newunqn)

            u = self.cfg.dbsess.query(Users).\
            filter(Users.username==username).\
            filter(Users.realm==realm).\
            filter(Users.site_id==site_id).first()
            if u:
                newu = Users(u.first_name, u.last_name, u.ssh_public_key, u.username, nsite_id, nrealm, u.uid, u.type, u.hdir, u.shell, u.email, active=True)
                self.cfg.dbsess.add(newu)
                self.cfg.dbsess.commit()
                self.cfg.log.debug("API_userdata/uclone: created user: %s.%s" % (newu.username, newunqn))
                return "success"
            else:
                self.cfg.log.debug("API_userdata/uclone: user not found: %s" % unqun)
                raise UserdataError("API_userdata/uclone: user not found: %s" % unqun)
        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/uclone: error: %s" % e)
            raise UserdataError("API_userdata/uclone: error: %s" % e)


############## good to here 

#    def update(self, query):
#        """
#        [description]
#        update/alter an existing tag entry
#
#        [parameter info]
#        required:
#            query: the query dict being passed to us from the called URI
#
#        [return]
#        Returns success if successful, raises an error if not
#        """
#        # setting variables
#        # config object. love this guy.
#        self.cfg.= self.cfg
#        # setting our valid query keys
#        common = MothershipCommon(self.cfg.
#        valid_qkeys = common.get_valid_qkeys(self.namespace, 'update')
#
#        try:
#            # this is a sanity clause...hey wait a minute! you can't fool me! there ain't no sanity clause
#            if 'name' not in query.keys():
#                self.cfg.log.debug("API_userdata/update: no name provided!")
#                raise UserdataError("API_userdata/update: no name provided!")
#            else:
#                name = query['name']
#
#            # check for wierd query keys, explode
#            for qk in query.keys():
#                if qk not in valid_qkeys:
#                    self.cfg.log.debug("API_userdata/update: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
#                    raise UserdataError("API_userdata/update: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
#
#            # to make everything just a bit more readable 
#            if 'start_port' in query.keys() and query['start_port'] and query['start_port'] != "None":
#                start_port = int(query['start_port'])
#            else:
#                start_port = None
#            if 'stop_port' in query.keys() and query['stop_port'] and query['stop_port'] != "None":
#                stop_port = int(query['stop_port'])
#            else:
#                stop_port = None
#            if 'security_level' in query.keys() and query['security_level'] and query['security_level'] != "None":
#                security_level = int(query['security_level'])
#            else:
#                security_level = None
#
#            if not security_level and not start_port and not stop_port:
#                self.cfg.log.debug("API_userdata/update: no updates specified!")
#                raise UserdataError("API_userdata/update: no updates specified!")
#
#            # because you know someone will try this...
#            if start_port and stop_port and (start_port > stop_port):
#                self.cfg.log.debug("API_userdata/update: start_port (%s) cannot be greater than stop_port (%s)!" % (start_port, stop_port))
#                raise UserdataError("API_userdata/update: start_port (%s) cannot be greater than stop_port (%s)!" % (start_port, stop_port))
#
#            # make sure the tag we've been asked to update actually exists
#            tag = self.__get_tag(self.cfg. name)
#            if tag:
#                # because you know someone will try this...
#                if start_port and not stop_port and tag.stop_port and (start_port > tag.stop_port):
#                    self.cfg.log.debug("API_userdata/update: start_port (%s) cannot be greater than tag.stop_port (%s)!" % (start_port, tag.stop_port))
#                    raise UserdataError("API_userdata/update: start_port (%s) cannot be greater than tag.stop_port (%s)!" % (start_port, tag.stop_port))
#                if not start_port and stop_port and tag.start_port and (tag.start_port > stop_port):
#                    self.cfg.log.debug("API_userdata/update: tag.start_port (%s) cannot be greater than stop_port (%s)!" % (tag.start_port, stop_port))
#                    raise UserdataError("API_userdata/update: tag.start_port (%s) cannot be greater than stop_port (%s)!" % (tag.start_port, stop_port))
#                if start_port:
#                    tag.start_port = start_port
#                if stop_port:
#                    tag.stop_port = stop_port
#                if security_level:
#                    tag.security_level = security_level 
#            else:
#                self.cfg.log.debug("API_userdata/update: no entry exists for name=%s. use API_userdata/uadd instead" % name)
#                raise UserdataError("API_userdata/update: no entry exists for name=%s. use API_userdata/uadd instead" % name )
#            self.cfg.log.debug("API_userdata/update: updating entry for name=%s with: start_port=%s stop_port=%s security_level=%s" % (tag.name, tag.start_port, tag.stop_port, tag.security_level))
#            self.cfg.dbsess.add(tag)
#            self.cfg.dbsess.commit()
#            return 'success'
#        except Exception, e:
#            # something odd happened, explode violently
#            self.cfg.dbsess.rollback()
#            self.cfg.log.debug("API_userdata/update: error: %s" % e)
#            raise UserdataError("API_userdata/update: error: %s" % e)
#
#
#    def tag(self, query):
#        """
#        [description]
#        map a tag to a server/realm/site/global 
#
#        [parameter info]
#        required:
#            query: the query dict being passed to us from the called URI
#
#        [return]
#        Returns success if successful, raises an error if not
#        """
#        # setting variables
#        # config object. love this guy.
#        self.cfg.= self.cfg
#        # setting our valid query keys
#        common = MothershipCommon(self.cfg.
#        valid_qkeys = common.get_valid_qkeys(self.namespace, 'tag')
#
#        try:
#            # this is a sanity clause...hey wait a minute! you can't fool me! there ain't no sanity clause
#            if 'name' not in query.keys():
#                self.cfg.log.debug("API_userdata/tag: no name provided!")
#                raise UserdataError("API_userdata/tag: no name provided!")
#            else:
#                name = query['name']
#            if 'unqdn' not in query.keys():
#                self.cfg.log.debug("API_userdata/tag: no unqdn provided!")
#                raise UserdataError("API_userdata/tag: no unqdn provided!")
#            else:
#                unqdn = query['unqdn']
#
#            # check for wierd query keys, explode
#            for qk in query.keys():
#                if qk not in valid_qkeys:
#                    self.cfg.log.debug("API_userdata/tag: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
#                    raise UserdataError("API_userdata/tag: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
#
#            # make sure the tag we've been asked to update actually exists
#            tag = self.__get_tag(self.cfg. name)
#            if tag:
#                self.cfg.log.debug("API_userdata/tag: mapping tag \"%s\" to unqdn\"%s\"" % (name, unqdn))
#            else:
#                self.cfg.log.debug("API_userdata/tag: no entry exists for name=%s. use API_userdata/uadd to add a tag first" % name)
#                raise UserdataError("API_userdata/tag: no entry exists for name=%s. use API_userdata/uadd to add a tag first" % name )
#            kv = API_kv(self.cfg.
#            kvquery = {'value': query['name'], 'key': 'tag', 'unqdn': query['unqdn']}
#            ret = kv.add(kvquery)
#            if ret == "success":
#                return ret
#            else:
#                self.cfg.dbsess.rollback()
#                raise UserdataError("API_userdata/tag: something has gone horribly wrong!") 
#        except Exception, e:
#            # something odd happened, explode violently
#            self.cfg.dbsess.rollback()
#            self.cfg.log.debug("API_userdata/tag: error: %s" % e)
#            raise UserdataError("API_userdata/tag: error: %s" % e)
#
#
#    def untag(self, query):
#        """
#        [description]
#        unmap a tag from a server/realm/site/global 
#
#        [parameter info]
#        required:
#            query: the query dict being passed to us from the called URI
#
#        [return]
#        Returns success if successful, raises an error if not
#        """
#        # setting variables
#        # config object. love this guy.
#        self.cfg.= self.cfg
#        # setting our valid query keys
#        common = MothershipCommon(self.cfg.
#        valid_qkeys = common.get_valid_qkeys(self.namespace, 'untag')
#
#        try:
#            # this is a sanity clause...hey wait a minute! you can't fool me! there ain't no sanity clause
#            if 'name' not in query.keys():
#                self.cfg.log.debug("API_userdata/untag: no name provided!")
#                raise UserdataError("API_userdata/untag: no name provided!")
#            else:
#                name = query['name']
#            if 'unqdn' not in query.keys():
#                self.cfg.log.debug("API_userdata/untag: no unqdn provided!")
#                raise UserdataError("API_userdata/untag: no unqdn provided!")
#            else:
#                unqdn = query['unqdn']
#
#            # check for wierd query keys, explode
#            for qk in query.keys():
#                if qk not in valid_qkeys:
#                    self.cfg.log.debug("API_userdata/untag: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
#                    raise UserdataError("API_userdata/untag: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
#
#            # make sure the tag mapping we've been asked to update actually exists
#            kv = API_kv(self.cfg.
#            kvquery = {'value': query['name'], 'key': 'tag', 'unqdn': query['unqdn']}
#            if kv.select(kvquery):
#                # mapping exists, remove it
#                kv.delete(kvquery)
#                return "success"
#            else:
#                # mapping does not exist, explode
#                self.cfg.dbsess.rollback()
#                raise UserdataError("API_userdata/untag: mapping not found for tag \"%s\" and unqdn \"%s\"" % (query['name'], query['unqdn']))
#        except Exception, e:
#            # something odd happened, explode violently
#            self.cfg.dbsess.rollback()
#            self.cfg.log.debug("API_userdata/untag: error: %s" % e)
#            raise UserdataError("API_userdata/untag: error: %s" % e)
#
#

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
        returns a Groups object or None
        """
        try: 
            groupname, realm, site_id = v_split_unqn(unqgn)
            v_name(groupname)
            v_realm(self.cfg, realm)
            v_site_id(self.cfg, site_id)
            g = list(self.cfg.dbsess.query(Groups).\
            filter(Groups.groupname==groupname).\
            filter(Groups.realm==realm).\
            filter(Groups.site_id==site_id))
    
            if g:
                return g
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
            for kv in kvs:
                unqgn = kv['value']+'_sudo.'+s.realm+'.'+s.site_id
                g = self.__get_group_obj(unqgn)
                if g:
                    groups.append(g[0])
                else:
                    pass
        
            # get sudo group for primary tag
            g = self.__get_group_obj(s.tag+'_sudo.'+s.realm+'.'+s.site_id)
            if g:
                groups.append(g[0])
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
