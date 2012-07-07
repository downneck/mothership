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
    mothership.API_tag

    Package for interacting with tags in mothership
"""

from sqlalchemy import or_, desc, MetaData

import mothership
from mothership.mothership_models import *

from mothership.common import *

class TagError(Exception):
    pass

class API_tag:

    def __init__(self, cfg):
        self.cfg = cfg
        self.version = 1
        self.namespace = 'API_tag'
        self.metadata = {
            'config': {
                'shortname': 'tag',
                'description': 'allows the creation and manipulation of tags',
                'module_dependencies': {
                    'mothership_models': 1,
                    'common': 1,
                },
            },
            'methods': {
                'display': {
                    'description': 'display a tag\'s info',
                    'rest_type': 'GET',
                    'admin_only': False,
                    'required_args': {
                        'name': {
                            'vartype': 'string',
                            'desc': 'name of the tag',
                            'ol': 'n',
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'tag': 'ORMobject',
                    },
                },
                'add': {
                    'description': 'create a tag entry in the tags table',
                    'rest_type': 'POST',
                    'admin_only': True,
                    'required_args': {
                        'args': {
                            'name': {
                                'vartype': 'string',
                                'desc': 'name of the tag to add to the database',
                                'ol': 'n',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 3,
                        'args': {
                            'start_port': {
                                'vartype': 'int',
                                'desc': 'starting port',
                                'ol': 's',
                            },
                            'stop_port': {
                                'vartype': 'int',
                                'desc': 'ending port',
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
                        'string': 'success!',
                    },
                },
                'delete': {
                    'description': 'delete a tag entry from the tags table',
                    'rest_type': 'DELETE',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'name': {
                                'vartype': 'string',
                                'desc': 'name of the tag to delete from the database',
                                'ol': 'n',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'string': 'success!',
                    },
                },
                'update': {
                    'description': 'update a tag entry in the tags table',
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
                                'vartype': 'string',
                                'desc': 'start of port range',
                                'ol': 's',
                            },
                            'stop_port': {
                                'vartype': 'string',
                                'desc': 'end of port range',
                                'ol': 't',
                            },
                            'security_level': {
                                'vartype': 'string',
                                'desc': 'security level override',
                                'ol': 'e',
                            },
                        },
                    },
                    'return': {
                        'string': 'success!',
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
                                'desc': 'unqdn of the server to map the tag onto',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'string': 'success!',
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
                                'desc': 'unqdn of the server to unmap the tag from',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'string': 'success!',
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
            raise TagError(e)


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
        valid_qkeys = self.common.get_valid_qkeys(cfg, self.namespace, 'add')

        try:
            # to make our conditionals easier
            if 'name' not in query.keys():
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
                start_port = query['start_port']
            else:
                start_port = None
            if 'stop_port' in query.keys() and query['stop_port']:
                stop_port = query['stop_port']
            else:
                stop_port = None
            if 'security_level' in query.keys() and query['security_level']:
                security_level = query['security_level']
            else:
                security_level = None

            # Check for duplicate tags.
            duptag = self.display(query)
            if duptag:
                cfg.log.debug("API_tag/add: entry exists for name=%s" % name)
                raise TagError("API_tag/add: entry exists for name=%s" % name )
            tag = self.Tag(name, start_port, stop_port, security_level)
            cfg.log.debug("API_tag/add: creating entry for name=%s start_port=%s stop_port=%s security_level=%s" % (tag.name, tag.start_port, tag.stop_port, tag.security_level))
            cfg.dbsess.add(tag)
            cfg.dbsess.commit()
            return 'success!'
        except Exception, e:
            raise TagError(e)
















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
            raise TagError(e)
        












# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! don't use this shit!

    # Remove a tag
    def rm_tag(cfg, name):
        r = cfg.dbsess.query(Tag).\
            filter(Tag.name==name).first()
    
        if not r:
            raise MothershipError("tag \"%s\" not found, aborting" % name)
    
        ans = raw_input("to delete tag \"%s\" please type \"delete_%s\": " % (name, name))
        if ans != "delete_%s" % name:
            raise MothershipError("aborted by user")
        else:
            cfg.dbsess.delete(r)
            cfg.dbsess.commit()
    
    
    # display a tag
    def display_tag(cfg, name):
        r = cfg.dbsess.query(Tag).\
            filter(Tag.name==name).first()
    
        if not r:
            raise MothershipError("tag \"%s\" not found, aborting" % name)
        else:
            print "name: %s\nstart_port_port: %s\nstop_port_port: %s\nsecurity level: %s" % (r.name, r.start_port_port, r.stop_port_port, r.security_level)
    
    
