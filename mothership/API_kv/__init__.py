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

class KVError(Exception):
    pass


class API_kv:

    def __init__(self, cfg):
        self.cfg = cfg
        self.version = 1
        self.name = 'API_kv'
        self.namespace = 'API_kv'
        self.metadata = {
            'config': {
                'description': 'allows interaction with the KeyValue table',
                'module_dependencies': {
                    'mothership_models': 1,
                },
            },
            'methods': {
                'select': {
                    'description': 'select a single KV entry',
                    'rest_type': 'GET',
                    'required_args': {
                        'args': {
                        },
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 1,
                        'args': {
                            'unqdn': {
                                'vartype': 'string',
                                'desc': 'unqdn/realm_path of the entry. enter any portion or none',
                            },
                            'key': {
                                'vartype': 'string',
                                'desc': 'key to filter on (leave blank or omit for all keys)',
                            },
                            'value': {
                                'vartype': 'string',
                                'desc': 'value to filter on',
                            },
                            'any': {
                                'vartype': 'None',
                                'desc': 'return the first entry we can find',
                            },
                        },
                    },
                    'cmdln_aliases': [
                        'kv_select',
                        'key_value_select',
                    ],
                    'return': {
                        'kv_entry': 'KVObject dict',
                    },
                },
                'collect': {
                    'description': 'get all kv entries that match a query',
                    'rest_type': 'GET',
                    'required_args': {
                        'args': {
                        },
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 1,
                        'args': {
                            'unqdn': {
                                'vartype': 'string',
                                'desc': 'unqdn/realm_path of the entries. enter any portion or none',
                            },
                            'key': {
                                'vartype': 'string',
                                'desc': 'key to filter on (leave blank or omit for all keys)',
                            },
                            'value': {
                                'vartype': 'string',
                                'desc': 'value to filter on',
                            },
                            'all': {
                                'vartype': 'None',
                                'desc': 'gimme everything! (return all KV entries)',
                            },
                        },
                    },
                    'cmdln_aliases': [
                        'kv_select',
                        'key_value_select',
                    ],
                    'return': {
                        'kv_entries': [
                            'KVobject dict',
                            'KVobject dict',
                        ],
                    },
                },
                'add': {
                    'description': 'add a KV entry',
                    'rest_type': 'POST',
                    'required_args': {
                        'args': {
                            'unqdn': {
                                'vartype': 'string',
                                'desc': 'unqdn/realm_path of the entry. enter any portion or none',
                            },
                            'key': {
                                'vartype': 'string',
                                'desc': 'key to add',
                            },
                            'value': {
                                'vartype': 'string',
                                'desc': 'value to add',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 0,
                        'args': {
                        },
                    },
                    'cmdln_aliases': [
                        'kv_add',
                        'key_value_add',
                    ],
                    'return': {
                        'true/false': 'bool',
                    },
                },
                'delete': {
                    'description': 'delete a KV entry',
                    'rest_type': 'DELETE',
                    'required_args': {
                        'args': {
                            'unqdn': {
                                'vartype': 'string',
                                'desc': 'unqdn/realm_path of the entry. enter any portion or none',
                            },
                            'key': {
                                'vartype': 'string',
                                'desc': 'key to remove',
                            },
                            'value': {
                                'vartype': 'string',
                                'desc': 'value to remove',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 0,
                        'args': {
                        },
                    },
                    'cmdln_aliases': [
                        'kv_delete',
                        'key_value_delete',
                        'kv_remove',
                        'key_value_remove',
                    ],
                    'return': {
                        'string': 'success!',
                    },
                },
                'update': {
                    'description': 'update a KV entry',
                    'rest_type': 'PUT',
                    'required_args': {
                        'args': {
                            'unqdn': {
                                'vartype': 'string',
                                'desc': 'unqdn/realm_path of the entry. enter any portion or none',
                            },
                            'key': {
                                'vartype': 'string',
                                'desc': 'key to update',
                            },
                            'value': {
                                'vartype': 'string',
                                'desc': 'value to update',
                            },
                            'new_value': {
                                'vartype': 'string',
                                'desc': 'new value to update to',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 0,
                        'args': {
                        },
                    },
                    'cmdln_aliases': [
                        'kv_update',
                        'key_value_update',
                    ],
                    'return': {
                        'string': 'success!',
                    },
                },
            },
        }


    # select a single query
    # there's definitely a more elegant way to do this
    # feel free to rewrite it :)
    def select(self, query):
        """
        [description]
        select a single KV entry

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns a specific KV entry dict.
        """
        # assigning stuff
        # our config. love this guy.
        cfg = self.cfg
        holdplease = None
        hostname = None
        realm = None
        site_id = None
        # return value
        kv_entry = None
        # setting our valid query keys
        valid_qkeys = []
        if self.metadata['methods']['select']['required_args']['args']:
            for i in self.metadata['methods']['select']['required_args']['args'].keys():
                valid_qkeys.append(i)
        if self.metadata['methods']['select']['optional_args']['args']:
            for i in self.metadata['methods']['select']['optional_args']['args'].keys():
                valid_qkeys.append(i)

        try:
            # to make our conditionals easier
            if 'unqdn' not in query.keys():
                unqdn = None
            else:
                unqdn = query['unqdn']
            if 'key' not in query.keys():
                key = None
            else:
                key = query['key']
            if 'value' not in query.keys():
                value = None
            else:
                value = query['value']
            if 'any' not in query.keys():
                any = None
            else:
                any = True

            # check for wierd query keys
            for qk in query.keys():
                if qk not in valid_qkeys:
                    if cfg.debug:
                        print "API_kv/collect: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys)
                    raise KVError("API_kv/collect: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # if we don't get values for anything, explode.
            if not unqdn and not key and not value and not any:
                if cfg.debug:
                    print "API_kv/select: no valid query keys!"
                raise KVError("API_kv/select: no valid query keys!")

            # translate our unqdn to hostname, realm, site_id
            try:
                if unqdn:
                    hostname, realm, site_id = mothership.split_fqdn(unqdn)
            except Exception, e:
                if cfg.debug:
                    print "API_kv/select: mothership.split_fqdn(unqdn) failed!\nerror: %s" % e

            # grab the first thing we can find.
            if any:
                if cfg.debug:
                    print "API_kv/select: querying for any record"
                kv_entry = cfg.dbsess.query(KV).first()

            # site_id, nothing else
            if site_id and not key and not hostname and not realm:
                if cfg.debug:
                    print "API_kv/select: querying for: site_id" % site_id
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.site_id==site_id).first()

            # site_id, realm, nothing else
            if site_id and realm and not key and not hostname:
                if cfg.debug:
                    print "API_kv/select: querying for: realm=%s, site_id=%s" % (realm, site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).first()

            # site_id, realm, hostname, nothing else
            if site_id and realm and hostname and not key:
                if cfg.debug:
                    print "API_kv/select: querying for: hostname=%s, realm=%s, site_id=%s" % (hostname, realm, site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).\
                               filter(KV.hostname==hostname).first()

            # value, nothing else
            if value and not unqdn and not key:
                if cfg.debug:
                    print "API_kv/select: querying for: value=%s" % value
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.value==value).first()

            # value, site_id
            if site_id and value and not hostname and not realm and not key:
                if cfg.debug:
                    print "API_kv/select: querying for: value=%s, site_id=%s" % (value, site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==value).\
                               filter(KV.site_id==site_id).first()

            # value, site_id, realm
            if site_id and realm and value and not hostname and not key:
                if cfg.debug:
                    print "API_kv/select: querying for: value=%s, realm=%s, site_id=%s" % (value, realm, site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==value).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).first()

            # value, site_id, realm, hostname
            if site_id and realm and hostname and value and not key:
                if cfg.debug:
                    print "API_kv/select: querying for: value=%s, realm=%s, site_id=%s" % (value, realm, site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==value).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).\
                               filter(KV.hostname==hostname).first()

            # key, nothing else
            if key and not unqdn and not value:
                if cfg.debug:
                    print "API_kv/select: querying for: key=%s" % key
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).first()

            # site_id, key
            if site_id and key and not hostname and not realm and not value:
                if cfg.debug:
                    print "API_kv/select: querying for: key=%s, site_id=%s" % (key, site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).\
                               filter(KV.site_id==site_id).first()

            # realm, site_id, key
            if realm and site_id and key and not hostname and not value:
                if cfg.debug:
                    print "API_kv/select: querying for: key=%s, site_id=%s, realm=%s" % (key, site_id, realm)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).first()

            # hostname, realm, site_id, key
            if hostname and realm and site_id and key and not value:
                if cfg.debug:
                    print "API_kv/select: querying for: key=%s, site_id=%s, realm=%s, hostname=%s" % (key, site_id, realm, hostname)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).\
                               filter(KV.hostname==hostname).first()

            # key, value, nothing else
            if value and key and not unqdn:
                if cfg.debug:
                    print "API_kv/select: querying on: key=%s, value=%s" % (key, value)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).\
                               filter(KV.value==value).first()

            # key, value, site_id
            if site_id and value and key and not hostname and not realm:
                if cfg.debug:
                    print "API_kv/select: querying on: key=%s, value=%s, site_id=%s" % (key, value, site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).\
                               filter(KV.value==value).\
                               filter(KV.site_id==site_id).first()

            # key, value, site_id, realm
            if site_id and realm and value and key and not hostname:
                if cfg.debug:
                    print "API_kv/select: querying on: key=%s, value=%s, realm=%s, site_id=%s" % (key, value, realm, site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).\
                               filter(KV.value==value).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).first()

            # hostname, realm, site_id, key, value
            if hostname and realm and site_id and key and value:
                if cfg.debug:
                    print "API_kv/select: querying for: key=%s, site_id=%s, realm=%s, hostname=%s, value=%s" % (key, site_id, realm, hostname, value)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).\
                               filter(KV.hostname==hostname).\
                               filter(KV.value==value).first()

            if kv_entry:
                return kv_entry.to_dict()
            else:
                if cfg.debug:
                    print "API_kv/select: no results found for query"
                return None

        except Exception, e:
            raise KVError(e)


    def collect(self, query):
        """
        [description]
        collect a group of KV entries

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns a list of kv object dicts.
        """
        # setting variables
        # config object. love this guy.
        cfg = self.cfg
        # setting up a debug buffer
        buf = "API_kv/collect: querying for "
        holdplease = None
        hostname = None
        realm = None
        site_id = None
        # our return value
        kv_entries = []
        # setting our valid query keys
        valid_qkeys = []
        if self.metadata['methods']['collect']['required_args']['args']:
            for i in self.metadata['methods']['collect']['required_args']['args'].keys():
                valid_qkeys.append(i)
        if self.metadata['methods']['collect']['optional_args']['args']:
            for i in self.metadata['methods']['collect']['optional_args']['args'].keys():
                valid_qkeys.append(i)

        try:
            # to make our conditionals easier
            if 'unqdn' not in query.keys():
                unqdn = None
            else:
                unqdn = query['unqdn']
            if 'key' not in query.keys():
                key = None
            else:
                key = query['key']
            if 'value' not in query.keys():
                value = None
            else:
                value = query['value']
            if 'all' not in query.keys():
                all = None
            else:
                all = True

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    if cfg.debug:
                        print "API_kv/collect: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys)
                    raise KVError("API_kv/collect: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # get the whole damn KV table
            results = cfg.dbsess.query(KV)

            # the "all" query overrides everything, so we blank out all
            # other values before filtering
            if all:
                if cfg.debug:
                    buf += "all records"
                unqdn = None
                key = None
                value = None

            # filtery by unqdn (or any portion thereof)
            if unqdn != None:
                hostname, realm, site_id = mothership.split_fqdn(unqdn)
                if cfg.debug:
                    buf += "unqdn=%s hostname=%s realm=%s site_id=%s " % (unqdn, hostname, realm, site_id)
                results = results.\
                    filter(KV.site_id==site_id).\
                    filter(KV.realm==realm).\
                    filter(KV.hostname==hostname)
            # filter by key
            if key:
                if cfg.debug:
                    buf += "key=%s " % key
                results = results.filter(KV.key==key)
            # filter by value
            if value:
                if cfg.debug:
                    buf += "value=%s " % value
                results = results.filter(KV.value==value)
            # turn the kv objects into dicts, append to list
            for i in results.all():
                kv_entries.append(i.to_dict())
            if cfg.debug:
                print buf
            # return list
            return kv_entries
        except Exception, e:
            if cfg.debug:
                print "Error: %s" % e
                print "dumping buffer: %s" % buf
            raise KVError(e)


    # add a new kv entry
    def add(self, query):
        """
        [description]
        create a new KV entry

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
        valid_qkeys = []
        if self.metadata['methods']['add']['required_args']['args']:
            for i in self.metadata['methods']['add']['required_args']['args'].keys():
                valid_qkeys.append(i)
        if self.metadata['methods']['add']['optional_args']['args']:
            for i in self.metadata['methods']['add']['optional_args']['args'].keys():
                valid_qkeys.append(i)

        try:
            # to make our conditionals easier
            if 'unqdn' not in query.keys():
                if cfg.debug:
                    print "API_kv/add: no unqdn provided!"
                raise KVError("API_kv/add: no unqdn provided!")
            else:
                unqdn = query['unqdn']
            if 'key' not in query.keys() or not query['key']:
                if cfg.debug:
                    print "API_kv/add: no key provided!"
                raise KVError("API_kv/add: no key provided!")
            else:
                key = query['key']
            if 'value' not in query.keys() or not query['value']:
                if cfg.debug:
                    print "API_kv/add: no value provided!"
                raise KVError("API_kv/add: no value provided!")
            else:
                value = query['value']

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    if cfg.debug:
                        print "API_kv/add: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys)
                    raise KVError("API_kv/add: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # Check for duplicate key=value.
            dupkv = self.select(query)
            if dupkv:
                if cfg.debug:
                    print "API_kv/add: entry exists for unqdn=%s key=%s value=%s" % (unqdn, key, value)
                raise KVError("API_kv/add: entry exists for unqdn=%s key=%s value=%s" % (unqdn, key, value))
            if not unqdn:
                if cfg.debug:
                    print "API_kv/add: creating entry for unqdn=(global!) key=%s value=%s" % (key, value)
                kv = self.__new(unqdn, key, value)
                cfg.dbsess.add(kv)
                cfg.dbsess.commit()
                return 'success!'
            if cfg.debug:
                    print "API_kv/add: creating entry for unqdn=%s key=%s value=%s" % (unqdn, key, value)
            kv = self.__new(unqdn, key, value)
            cfg.dbsess.add(kv)
            cfg.dbsess.commit()
            return 'success!'
        except Exception, e:
            raise KVError(e)


    def update(self, query):
        """
        [description]
        update a KV entry

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns true if successful, raises an error if not
        """
        # setting variables
        # config object. love this guy.
        cfg = self.cfg
        # setting up a debug buffer
        buf = "API_kv/update: update successful for "
        hostname = None
        realm = None
        site_id = None
        # setting our valid query keys
        valid_qkeys = []
        if self.metadata['methods']['update']['required_args']['args']:
            for i in self.metadata['methods']['update']['required_args']['args'].keys():
                valid_qkeys.append(i)
        if self.metadata['methods']['update']['optional_args']['args']:
            for i in self.metadata['methods']['update']['optional_args']['args'].keys():
                valid_qkeys.append(i)

        try:
            # to make our conditionals easier
            if 'unqdn' not in query.keys():
                unqdn = None
            else:
                unqdn = query['unqdn']
            if 'key' not in query.keys() or not query['key']:
                raise KVError("API_kv/update: no key supplied")
            else:
                key = query['key']
            if 'value' not in query.keys() or not query['value']:
                raise KVError("API_kv/update: no value supplied")
            else:
                value = query['value']
            if 'new_value' not in query.keys() or not query['new_value']:
                raise KVError("API_kv/update: no new_value supplied")
            else:
                new_value = query['new_value']

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    if cfg.debug:
                        print "API_kv/update: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys)
                    raise KVError("API_kv/update: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # get the whole damn KV table

            # filtery by unqdn (or any portion thereof)
            if unqdn != None:
                hostname, realm, site_id = mothership.split_fqdn(unqdn)
                if cfg.debug:
                    buf += "unqdn=%s hostname=%s realm=%s site_id=%s " % (unqdn, hostname, realm, site_id)
            else:
                if cfg.debug:
                    buf += "unqdn=(global!) hostname=%s realm=%s site_id=%s " % (hostname, realm, site_id)
            # try to find an existing entry
            result = cfg.dbsess.query(KV).\
                filter(KV.site_id==site_id).\
                filter(KV.realm==realm).\
                filter(KV.hostname==hostname).\
                filter(KV.key==key).\
                filter(KV.value==value).first()
            if result:
                if cfg.debug:
                    print buf
                result.value = new_value
                cfg.dbsess.add(result)
                cfg.dbsess.commit()
                return 'success!'
            else:
                raise KVError("API_kv/update: query failed for unqdn=%s key=%s value=%s, no record to update" % (unqdn, key, value))
        except Exception, e:
            raise KVError(e)

    def delete(self, query):
        """
        [description]
        delete a KV entry

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns true if successful, raises an error if not
        """
        # setting variables
        # config object. love this guy.
        cfg = self.cfg
        # setting up a debug buffer
        buf = "API_kv/delete: delete successful for "
        hostname = None
        realm = None
        site_id = None
        # setting our valid query keys
        valid_qkeys = []
        if self.metadata['methods']['delete']['required_args']['args']:
            for i in self.metadata['methods']['delete']['required_args']['args'].keys():
                valid_qkeys.append(i)
        if self.metadata['methods']['delete']['optional_args']['args']:
            for i in self.metadata['methods']['delete']['optional_args']['args'].keys():
                valid_qkeys.append(i)

        try:
            # to make our conditionals easier
            if 'unqdn' not in query.keys():
                unqdn = None
            else:
                unqdn = query['unqdn']
            if 'key' not in query.keys() or not query['key']:
                raise KVError("API_kv/update: no key supplied")
            else:
                key = query['key']
            if 'value' not in query.keys() or not query['value']:
                raise KVError("API_kv/update: no value supplied")
            else:
                value = query['value']

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    if cfg.debug:
                        print "API_kv/delete: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys)
                    raise KVError("API_kv/delete: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # get the whole damn KV table

            # filtery by unqdn (or any portion thereof)
            if unqdn != None:
                hostname, realm, site_id = mothership.split_fqdn(unqdn)
                if cfg.debug:
                    buf += "unqdn=%s hostname=%s realm=%s site_id=%s " % (unqdn, hostname, realm, site_id)
            else:
                if cfg.debug:
                    buf += "unqdn=(global!) hostname=%s realm=%s site_id=%s " % (hostname, realm, site_id)
            # try to find an existing entry
            result = cfg.dbsess.query(KV).\
                filter(KV.site_id==site_id).\
                filter(KV.realm==realm).\
                filter(KV.hostname==hostname).\
                filter(KV.key==key).\
                filter(KV.value==value).first()

            # check to see if we have an entry, if so...annihilate it!
            if result:
                cfg.dbsess.delete(result)
                cfg.dbsess.commit()
                if cfg.debug:
                    print buf
                return 'success!'
            else:
                if cfg.debug:
                    print "API_kv/delete: query failed for unqdn=%s key=%s value=%s, nothing to delete!" % (unqdn, key, value)
                raise KVError("API_kv/delete: query failed for unqdn=%s key=%s value=%s, nothing to delete!" % (unqdn, key, value))
        except Exception, e:
            raise KVError(e)

    # create a new KV object, return it. for use internally only
    def __new(self, unqdn, key, value):
        """
        [description]
        Constructor that takes a host.realm.site style fqdn.

        [parameter info]
        required:
            unqdn: really unqdn. host.realm.site_id we're operating on
            key: key to create
            value: value to assign to key

        [return]
        returns a KV ORMobject
        """
        hostname, realm, site_id = mothership.split_fqdn(unqdn)
        kv = KV(key, value, hostname, realm, site_id)
        return kv
