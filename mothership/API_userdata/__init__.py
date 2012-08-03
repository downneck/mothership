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

#import mothership
#from mothership.mothership_models import *
from mothership.common import *
#from mothership.API_list_servers import *
#from mothership.API_kv import *
#from mothership.validate import *

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
                                'vartype': 'string',
                                'desc': 'name.realm.site_id of the user',
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
                                'vartype': 'string',
                                'desc': 'username.realm.site_id of the user to add to the database',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 3,
                        'args': {
                            'first_name': {
                                'vartype': 'string',
                                'desc': 'user\'s first name (default John)',
                                'ol': 'f',
                            },
                            'last_name': {
                                'vartype': 'string',
                                'desc': 'user\'s last name (default Doe)',
                                'ol': 'l',
                            },
                            'ssh_key': {
                                'vartype': 'string',
                                'desc': 'a string containing the user\'s ssh key blob',
                                'ol': 'k',
                            },
                            'shell': {
                                'vartype': 'string',
                                'desc': "user's shell (default: %s)" % cfg.shell,
                                'ol': 's',
                            },
                            'email_address': {
                                'vartype': 'string',
                                'desc': "user's email address (default: username@%s)" % cfg.email_domain,
                                'ol': 'e',
                            },
                            'home_dir': {
                                'vartype': 'string',
                                'desc': "user's home directory (default: %s/username)" % cfg.hdir,
                                'ol': 'e',
                            },
                            'user_type': {
                                'vartype': 'string',
                                'desc': "user type, pick one of: %s (default: %s)" % (" ".join(cfg.user_types), cfg.def_user_type),
                                'ol': 't',
                            },
                            'uid': {
                                'vartype': 'string',
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
                                'vartype': 'string',
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
# # # # # # # # # # # #
# GOOD TO HERE
# # # # # # # # # # # #
                'update': {
                    'description': 'update a tag entry in the tags table. use "None" to clear a setting',
                    'rest_type': 'PUT',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'name': {
                                'vartype': 'string',
                                'desc': 'name of the tag to update in the database',
                                'ol': 'n',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 3,
                        'args': {
                            'start_port': {
                                'vartype': 'int',
                                'desc': 'start of port range',
                                'ol': 's',
                            },
                            'stop_port': {
                                'vartype': 'int',
                                'desc': 'end of port range',
                                'ol': 't',
                            },
                            'security_level': {
                                'vartype': 'int',
                                'desc': 'security level override',
                                'ol': 'e',
                            },
                        },
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'tag': {
                    'description': 'map a tag to a server (tag! you\'re it!)',
                    'rest_type': 'POST',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'name': {
                                'vartype': 'string',
                                'desc': 'name of the tag to map',
                                'ol': 'n',
                            },
                            'unqdn': {
                                'vartype': 'string',
                                'desc': 'unqdn of the server to map the tag onto (use the keyword "GLOBAL" to map a tag globally)',
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
                'untag': {
                    'description': 'unmap a tag from a server',
                    'rest_type': 'DELETE',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'name': {
                                'vartype': 'string',
                                'desc': 'name of the tag to unmap',
                                'ol': 'n',
                            },
                            'unqdn': {
                                'vartype': 'string',
                                'desc': 'unqdn of the server to unmap the tag from (use the keyword "GLOBAL" to unmap a globally mapped tag)',
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
            },
        }


    def display(self, query):
        """
        [description]
        display the information for a tag

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns the tag ORMobject if successful, None if unsuccessful 
        """
        # setting variables
        # config object. love this guy.
        cfg = self.cfg

        try:
            # to make our conditionals easier
            if 'name' not in query.keys():
                cfg.log.debug("API_tag/display: no name provided!")
                raise TagError("API_tag/display: no name provided!")
            else:
                name = query['name']
            result = self.__get_tag(cfg, name)
            if result:
                return result.to_dict()
            else:
                return None
        except Exception, e:
            # something odd happened, explode violently
            cfg.log.debug("API_tag/display: error: %s" % e)
            raise TagError("API_tag/display: error: %s" % e)


    def add(self, query):
        """
        [description]
        create a new tags entry

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns true if successful, raises an error if not
        """
        # setting variables
        # config object. love this guy.
        cfg = self.cfg
        # setting our valid query keys
        common = MothershipCommon(cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'add')

        try:
            # to make our conditionals easier
            if 'name' not in query.keys() or not query['name']:
                cfg.log.debug("API_tag/add: no name provided!")
                raise TagError("API_tag/add: no name provided!")
            else:
                name = query['name']

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    cfg.log.debug("API_tag/add: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise TagError("API_tag/add: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            if 'start_port' in query.keys() and query['start_port']:
                start_port = int(query['start_port'])
            else:
                start_port = None
            if 'stop_port' in query.keys() and query['stop_port']:
                stop_port = int(query['stop_port'])
            else:
                stop_port = None
            if 'security_level' in query.keys() and query['security_level']:
                security_level = int(query['security_level'])
            else:
                security_level = None

            if start_port and not stop_port:
                cfg.log.debug("API_tag/add: start_port requires a stop_port!")
                raise TagError("API_tag/add: start_port requires a stop_port!")
            elif stop_port and not start_port:
                cfg.log.debug("API_tag/add: stop_port requires a start_port!")
                raise TagError("API_tag/add: stop_port requires a start_port!")
                 

            # Check for duplicate tags.
            duptag = self.display(query)
            if duptag:
                cfg.log.debug("API_tag/add: entry exists for name=%s" % name)
                raise TagError("API_tag/add: entry exists for name=%s" % name )
            tag = Tag(name, start_port, stop_port, security_level)
            cfg.log.debug("API_tag/add: creating entry for name=%s start_port=%s stop_port=%s security_level=%s" % (tag.name, tag.start_port, tag.stop_port, tag.security_level))
            cfg.dbsess.add(tag)
            cfg.dbsess.commit()
            return 'success'
        except Exception, e:
            # something odd happened, explode violently
            cfg.dbsess.rollback()
            cfg.log.debug("API_tag/add: error: %s" % e)
            raise TagError("API_tag/add: error: %s" % e)


    def delete(self, query):
        """
        [description]
        delete a tag from the tag table

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns "success" if successful, None if unsuccessful 
        """
        # setting variables
        # config object. love this guy.
        cfg = self.cfg

        try:
            # to make our conditionals easier
            if 'name' not in query.keys():
                cfg.log.debug("API_tag/delete: no name provided!")
                raise TagError("API_tag/delete: no name provided!")
            else:
                name = query['name']
            listservers = API_list_servers(cfg)
            lssquery = {'tag': name}
            if listservers.lss(lssquery):
                raise TagError("API_tag/delete: tag is still mapped to servers! unmap before deleting")
            result = self.__get_tag(cfg, name)
            if result:
                cfg.dbsess.delete(result)
                cfg.dbsess.commit()
                cfg.log.debug("API_tag/delete: deleted tag: %s" % name)
                return "success"
            else:
                return None
        except Exception, e:
            # something odd happened, explode violently
            cfg.dbsess.rollback()
            cfg.log.debug("API_tag/delete: error: %s" % e)
            raise TagError("API_tag/delete: error: %s" % e)


    def update(self, query):
        """
        [description]
        update/alter an existing tag entry

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns success if successful, raises an error if not
        """
        # setting variables
        # config object. love this guy.
        cfg = self.cfg
        # setting our valid query keys
        common = MothershipCommon(cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'update')

        try:
            # this is a sanity clause...hey wait a minute! you can't fool me! there ain't no sanity clause
            if 'name' not in query.keys():
                cfg.log.debug("API_tag/update: no name provided!")
                raise TagError("API_tag/update: no name provided!")
            else:
                name = query['name']

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    cfg.log.debug("API_tag/update: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise TagError("API_tag/update: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # to make everything just a bit more readable 
            if 'start_port' in query.keys() and query['start_port'] and query['start_port'] != "None":
                start_port = int(query['start_port'])
            else:
                start_port = None
            if 'stop_port' in query.keys() and query['stop_port'] and query['stop_port'] != "None":
                stop_port = int(query['stop_port'])
            else:
                stop_port = None
            if 'security_level' in query.keys() and query['security_level'] and query['security_level'] != "None":
                security_level = int(query['security_level'])
            else:
                security_level = None

            if not security_level and not start_port and not stop_port:
                cfg.log.debug("API_tag/update: no updates specified!")
                raise TagError("API_tag/update: no updates specified!")

            # because you know someone will try this...
            if start_port and stop_port and (start_port > stop_port):
                cfg.log.debug("API_tag/update: start_port (%s) cannot be greater than stop_port (%s)!" % (start_port, stop_port))
                raise TagError("API_tag/update: start_port (%s) cannot be greater than stop_port (%s)!" % (start_port, stop_port))

            # make sure the tag we've been asked to update actually exists
            tag = self.__get_tag(cfg, name)
            if tag:
                # because you know someone will try this...
                if start_port and not stop_port and tag.stop_port and (start_port > tag.stop_port):
                    cfg.log.debug("API_tag/update: start_port (%s) cannot be greater than tag.stop_port (%s)!" % (start_port, tag.stop_port))
                    raise TagError("API_tag/update: start_port (%s) cannot be greater than tag.stop_port (%s)!" % (start_port, tag.stop_port))
                if not start_port and stop_port and tag.start_port and (tag.start_port > stop_port):
                    cfg.log.debug("API_tag/update: tag.start_port (%s) cannot be greater than stop_port (%s)!" % (tag.start_port, stop_port))
                    raise TagError("API_tag/update: tag.start_port (%s) cannot be greater than stop_port (%s)!" % (tag.start_port, stop_port))
                if start_port:
                    tag.start_port = start_port
                if stop_port:
                    tag.stop_port = stop_port
                if security_level:
                    tag.security_level = security_level 
            else:
                cfg.log.debug("API_tag/update: no entry exists for name=%s. use API_tag/add instead" % name)
                raise TagError("API_tag/update: no entry exists for name=%s. use API_tag/add instead" % name )
            cfg.log.debug("API_tag/update: updating entry for name=%s with: start_port=%s stop_port=%s security_level=%s" % (tag.name, tag.start_port, tag.stop_port, tag.security_level))
            cfg.dbsess.add(tag)
            cfg.dbsess.commit()
            return 'success'
        except Exception, e:
            # something odd happened, explode violently
            cfg.dbsess.rollback()
            cfg.log.debug("API_tag/update: error: %s" % e)
            raise TagError("API_tag/update: error: %s" % e)


    def tag(self, query):
        """
        [description]
        map a tag to a server/realm/site/global 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns success if successful, raises an error if not
        """
        # setting variables
        # config object. love this guy.
        cfg = self.cfg
        # setting our valid query keys
        common = MothershipCommon(cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'tag')

        try:
            # this is a sanity clause...hey wait a minute! you can't fool me! there ain't no sanity clause
            if 'name' not in query.keys():
                cfg.log.debug("API_tag/tag: no name provided!")
                raise TagError("API_tag/tag: no name provided!")
            else:
                name = query['name']
            if 'unqdn' not in query.keys():
                cfg.log.debug("API_tag/tag: no unqdn provided!")
                raise TagError("API_tag/tag: no unqdn provided!")
            else:
                unqdn = query['unqdn']

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    cfg.log.debug("API_tag/tag: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise TagError("API_tag/tag: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # make sure the tag we've been asked to update actually exists
            tag = self.__get_tag(cfg, name)
            if tag:
                cfg.log.debug("API_tag/tag: mapping tag \"%s\" to unqdn\"%s\"" % (name, unqdn))
            else:
                cfg.log.debug("API_tag/tag: no entry exists for name=%s. use API_tag/add to add a tag first" % name)
                raise TagError("API_tag/tag: no entry exists for name=%s. use API_tag/add to add a tag first" % name )
            kv = API_kv(cfg)
            kvquery = {'value': query['name'], 'key': 'tag', 'unqdn': query['unqdn']}
            ret = kv.add(kvquery)
            if ret == "success":
                return ret
            else:
                cfg.dbsess.rollback()
                raise TagError("API_tag/tag: something has gone horribly wrong!") 
        except Exception, e:
            # something odd happened, explode violently
            cfg.dbsess.rollback()
            cfg.log.debug("API_tag/tag: error: %s" % e)
            raise TagError("API_tag/tag: error: %s" % e)


    def untag(self, query):
        """
        [description]
        unmap a tag from a server/realm/site/global 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns success if successful, raises an error if not
        """
        # setting variables
        # config object. love this guy.
        cfg = self.cfg
        # setting our valid query keys
        common = MothershipCommon(cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'untag')

        try:
            # this is a sanity clause...hey wait a minute! you can't fool me! there ain't no sanity clause
            if 'name' not in query.keys():
                cfg.log.debug("API_tag/untag: no name provided!")
                raise TagError("API_tag/untag: no name provided!")
            else:
                name = query['name']
            if 'unqdn' not in query.keys():
                cfg.log.debug("API_tag/untag: no unqdn provided!")
                raise TagError("API_tag/untag: no unqdn provided!")
            else:
                unqdn = query['unqdn']

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    cfg.log.debug("API_tag/untag: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise TagError("API_tag/untag: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # make sure the tag mapping we've been asked to update actually exists
            kv = API_kv(cfg)
            kvquery = {'value': query['name'], 'key': 'tag', 'unqdn': query['unqdn']}
            if kv.select(kvquery):
                # mapping exists, remove it
                kv.delete(kvquery)
                return "success"
            else:
                # mapping does not exist, explode
                cfg.dbsess.rollback()
                raise TagError("API_tag/untag: mapping not found for tag \"%s\" and unqdn \"%s\"" % (query['name'], query['unqdn']))
        except Exception, e:
            # something odd happened, explode violently
            cfg.dbsess.rollback()
            cfg.log.debug("API_tag/untag: error: %s" % e)
            raise TagError("API_tag/untag: error: %s" % e)


# internal functions below here

    def __get_tag(self, cfg, name):
        """
        stuff here
        """
        try:
            result = cfg.dbsess.query(Tag).\
                     filter(Tag.name == name).first()
            if result:
                return result
            else:
                return None
        except Exception, e:
            cfg.dbsess.rollback()
            cfg.log.debug("API_tag/__get_tag: error: %s" % e)
            raise TagError("API_tag/__get_tag: error: %s" % e)
