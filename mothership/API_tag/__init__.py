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
    mothership.API_kv

    Package for interacting with the KV store in mothership
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
                            'start': {
                                'vartype': 'int',
                                'desc': 'starting port',
                                'ol': 's',
                            },
                            'stop': {
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
                            'start': {
                                'vartype': 'string',
                                'desc': 'start of port range',
                                'ol': 's',
                            },
                            'stop': {
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


    # Add a tag
    def add_tag(cfg, name, start_port=None, stop_port=None, security_level=None):
        badtag = cfg.dbsess.query(Tag).\
                  filter(Tag.name==name).first()
    
        if badtag:
            raise MothershipError("tag \"%s\" already exists, aborting" % name)
    
        r = Tag(name, start_port, stop_port, security_level)
        cfg.dbsess.add(r)
        cfg.dbsess.commit()
    
    
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
            print "name: %s\nstart_port: %s\nstop_port: %s\nsecurity level: %s" % (r.name, r.start_port, r.stop_port, r.security_level)
    
    
