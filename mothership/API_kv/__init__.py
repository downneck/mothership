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
from mothership.validate import *

class KVError(Exception):
    pass

class API_kv:

    def __init__(self, cfg):
        self.cfg = cfg
        self.common = MothershipCommon(cfg)
        self.version = 1
        self.namespace = 'API_kv'
        self.metadata = {
            'config': {
                'shortname': 'kv',
                'description': 'allows interaction with the KeyValue table (not to be taken lightly)',
                'module_dependencies': {
                    'mothership_models': 1,
                },
            },
            'methods': {
                'select': {
                    'description': 'select a single KV entry',
                    'rest_type': 'GET',
                    'admin_only': False, 
                    'required_args': {
                        'args': {
                        },
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 3,
                        'args': {
                            'unqdn': {
                                'vartype': 'str',
                                'desc': 'unqdn/realm_path of the entry. enter any portion or "GLOBAL" to select a global value',
                                'ol': 'u',
                            },
                            'key': {
                                'vartype': 'str',
                                'desc': 'key to filter on (leave blank or omit for all keys)',
                                'ol': 'k',
                            },
                            'value': {
                                'vartype': 'str',
                                'desc': 'value to filter on',
                                'ol': 'v',
                            },
                            'any': {
                                'vartype': 'bool',
                                'desc': 'return the first entry we can find (overrides all other options)',
                                'ol': 'a',
                            },
                        },
                    },
                    'return': {
                        'kv_entry': 'KVObject dict',
                    },
                },
                'collect': {
                    'description': 'get all kv entries that match a query',
                    'rest_type': 'GET',
                    'admin_only': False, 
                    'required_args': {
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 3,
                        'args': {
                            'unqdn': {
                                'vartype': 'str',
                                'desc': 'unqdn/realm_path of the entries. enter any portion or "GLOBAL" to select all global values',
                                'ol': 'u',
                            },
                            'key': {
                                'vartype': 'str',
                                'desc': 'key to filter on (leave blank or omit for all keys)',
                                'ol': 'k',
                            },
                            'value': {
                                'vartype': 'str',
                                'desc': 'value to filter on',
                                'ol': 'v',
                            },
                            'all': {
                                'vartype': 'bool',
                                'desc': 'gimme everything! (return all KV entries, overrides all other options)',
                                'ol': 'a',
                            },
                        },
                    },
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
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'unqdn': {
                                'vartype': 'str',
                                'desc': 'unqdn/realm_path of the entry. enter any portion or "GLOBAL" to add a global value',
                                'ol': 'u',
                            },
                            'key': {
                                'vartype': 'str',
                                'desc': 'key to add',
                                'ol': 'k',
                            },
                            'value': {
                                'vartype': 'str',
                                'desc': 'value to add',
                                'ol': 'v',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'true/false': 'bool',
                    },
                },
                'delete': {
                    'description': 'delete a KV entry',
                    'rest_type': 'DELETE',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'unqdn': {
                                'vartype': 'str',
                                'desc': 'unqdn/realm_path of the entry. enter any portion or "GLOBAL" to delete a global value',
                                'ol': 'u',
                            },
                            'key': {
                                'vartype': 'str',
                                'desc': 'key to remove',
                                'ol': 'k',
                            },
                            'value': {
                                'vartype': 'str',
                                'desc': 'value to remove',
                                'ol': 'v',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'update': {
                    'description': 'update a KV entry',
                    'rest_type': 'PUT',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'unqdn': {
                                'vartype': 'str',
                                'desc': 'unqdn/realm_path of the entry. enter any portion or "GLOBAL" to update a global value',
                                'ol': 'u',
                            },
                            'key': {
                                'vartype': 'str',
                                'desc': 'key to update',
                                'ol': 'k',
                            },
                            'value': {
                                'vartype': 'str',
                                'desc': 'value to update',
                                'ol': 'v',
                            },
                            'new_value': {
                                'vartype': 'str',
                                'desc': 'new value to update to',
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
        valid_qkeys = self.common.get_valid_qkeys(self.namespace, 'select')

        try:
            # to make our conditionals easier
            if 'unqdn' not in query.keys() or query['unqdn'] == 'GLOBAL':
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
                    cfg.log.debug("API_kv/collect: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise KVError("API_kv/collect: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # if we don't get values for anything, explode.
            if not unqdn and not key and not value and not any:
                cfg.log.debug("API_kv/select: no valid query keys!")
                raise KVError("API_kv/select: no valid query keys!")

            # translate our unqdn to hostname, realm, site_id
            try:
                if unqdn:
                    hostname, realm, site_id = v_split_unqn(unqdn)
            except Exception, e:
                cfg.log.debug("API_kv/select: %s" % e)

            # grab the first thing we can find.
            if any:
                cfg.log.debug("API_kv/select: querying for any record")
                kv_entry = cfg.dbsess.query(KV).first()

            # site_id, nothing else
            elif site_id and not key and not hostname and not realm:
                cfg.log.debug("API_kv/select: querying for: site_id" % site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.site_id==site_id).first()

            # site_id, realm, nothing else
            elif site_id and realm and not key and not hostname:
                cfg.log.debug("API_kv/select: querying for: realm=%s, site_id=%s" % (realm, site_id))
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).first()

            # site_id, realm, hostname, nothing else
            elif site_id and realm and hostname and not key:
                cfg.log.debug("API_kv/select: querying for: hostname=%s, realm=%s, site_id=%s" % (hostname, realm, site_id))
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).\
                               filter(KV.hostname==hostname).first()

            # value, nothing else
            elif value and not unqdn and not key:
                cfg.log.debug("API_kv/select: querying for: value=%s" % value)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.value==value).first()

            # value, site_id
            elif site_id and value and not hostname and not realm and not key:
                cfg.log.debug("API_kv/select: querying for: value=%s, site_id=%s" % (value, site_id))
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==value).\
                               filter(KV.site_id==site_id).first()

            # value, site_id, realm
            elif site_id and realm and value and not hostname and not key:
                cfg.log.debug("API_kv/select: querying for: value=%s, realm=%s, site_id=%s" % (value, realm, site_id))
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==value).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).first()

            # value, site_id, realm, hostname
            elif site_id and realm and hostname and value and not key:
                cfg.log.debug("API_kv/select: querying for: value=%s, realm=%s, site_id=%s" % (value, realm, site_id))
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==value).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).\
                               filter(KV.hostname==hostname).first()

            # key, nothing else
            elif key and not unqdn and not value:
                cfg.log.debug("API_kv/select: querying for: key=%s" % key)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).first()

            # site_id, key
            elif site_id and key and not hostname and not realm and not value:
                cfg.log.debug("API_kv/select: querying for: key=%s, site_id=%s" % (key, site_id))
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).\
                               filter(KV.site_id==site_id).first()

            # realm, site_id, key
            elif realm and site_id and key and not hostname and not value:
                cfg.log.debug("API_kv/select: querying for: key=%s, site_id=%s, realm=%s" % (key, site_id, realm))
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).first()

            # hostname, realm, site_id, key
            elif hostname and realm and site_id and key and not value:
                cfg.log.debug("API_kv/select: querying for: key=%s, site_id=%s, realm=%s, hostname=%s" % (key, site_id, realm, hostname))
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).\
                               filter(KV.hostname==hostname).first()

            # key, value, nothing else
            elif value and key and not unqdn:
                cfg.log.debug("API_kv/select: querying on: key=%s, value=%s" % (key, value))
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).\
                               filter(KV.value==value).first()

            # key, value, site_id
            elif site_id and value and key and not hostname and not realm:
                cfg.log.debug("API_kv/select: querying on: key=%s, value=%s, site_id=%s" % (key, value, site_id))
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).\
                               filter(KV.value==value).\
                               filter(KV.site_id==site_id).first()

            # key, value, site_id, realm
            elif site_id and realm and value and key and not hostname:
                cfg.log.debug("API_kv/select: querying on: key=%s, value=%s, realm=%s, site_id=%s" % (key, value, realm, site_id))
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).\
                               filter(KV.value==value).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).first()

            # hostname, realm, site_id, key, value
            elif hostname and realm and site_id and key and value:
                cfg.log.debug("API_kv/select: querying for: key=%s, site_id=%s, realm=%s, hostname=%s, value=%s" % (key, site_id, realm, hostname, value))
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==key).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).\
                               filter(KV.hostname==hostname).\
                               filter(KV.value==value).first()

            if kv_entry:
                return [kv_entry.to_dict(),]
            else:
                cfg.log.debug("API_kv/select: no results found for query")
                return None

        except Exception, e:
            cfg.dbsess.rollback()
            raise KVError("API_kv/select: error: %s" % e) 


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
        valid_qkeys = self.common.get_valid_qkeys(self.namespace, 'collect')

        try:
            # to make our conditionals easier
            if 'unqdn' not in query.keys() or query['unqdn'] == 'GLOBAL':
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
                    cfg.log.debug("API_kv/collect: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise KVError("API_kv/collect: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # get the whole damn KV table
            results = cfg.dbsess.query(KV)

            # the "all" query overrides everything, so we blank out all
            # other values before filtering
            if all:
                buf += "all records"
                unqdn = None
                key = None
                value = None

            # filtery by unqdn (or any portion thereof)
            if unqdn != None:
                hostname, realm, site_id = v_split_unqn(unqdn)
                buf += "unqdn=%s hostname=%s realm=%s site_id=%s " % (unqdn, hostname, realm, site_id)
                results = results.\
                    filter(or_(KV.site_id==site_id, KV.site_id==None)).\
                    filter(or_(KV.realm==realm, KV.realm==None)).\
                    filter(or_(KV.hostname==hostname, KV.hostname==None))
            # filter by key
            if key:
                buf += "key=%s " % key
                results = results.filter(KV.key==key)
            # filter by value
            if value:
                buf += "value=%s " % value
                results = results.filter(KV.value==value)
            # turn the kv objects into dicts, append to list
            for i in results.all():
                kv_entries.append(i.to_dict())
            cfg.log.debug(buf)
            # return list
            return kv_entries
        except Exception, e:
            cfg.log.debug("Error: %s" % e)
            cfg.log.debug("dumping buffer: %s" % buf)
            cfg.dbsess.rollback()
            raise KVError("API_kv/collect: error: %s" % e) 


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
        valid_qkeys = self.common.get_valid_qkeys(self.namespace, 'add')

        try:
            # to make our conditionals easier
            if 'unqdn' not in query.keys():
                cfg.log.debug("API_kv/add: no unqdn provided!")
                raise KVError("API_kv/add: no unqdn provided!")
            else:
                unqdn = query['unqdn']
            if 'key' not in query.keys() or not query['key']:
                cfg.log.debug("API_kv/add: no key provided!")
                raise KVError("API_kv/add: no key provided!")
            else:
                key = query['key']
            if 'value' not in query.keys() or not query['value']:
                cfg.log.debug("API_kv/add: no value provided!")
                raise KVError("API_kv/add: no value provided!")
            else:
                value = query['value']

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    cfg.log.debug("API_kv/add: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise KVError("API_kv/add: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # Check for duplicate key=value.
            dupkv = self.select(query)
            if dupkv:
                cfg.log.debug("API_kv/add: entry exists for unqdn=%s key=%s value=%s" % (unqdn, key, value))
                raise KVError("API_kv/add: entry exists for unqdn=%s key=%s value=%s" % (unqdn, key, value))
            if unqdn == 'GLOBAL':
                cfg.log.debug("API_kv/add: creating entry for unqdn=(global!) key=%s value=%s" % (key, value))
                kv = self.__new(unqdn, key, value)
                cfg.dbsess.add(kv)
                cfg.dbsess.commit()
                return 'success'
                cfg.log.debug("API_kv/add: creating entry for unqdn=%s key=%s value=%s" % (unqdn, key, value))
            kv = self.__new(unqdn, key, value)
            cfg.dbsess.add(kv)
            cfg.dbsess.commit()
            return 'success'
        except Exception, e:
            cfg.dbsess.rollback()
            raise KVError("API_kv/add: error: %s" % e) 


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
        valid_qkeys = self.common.get_valid_qkeys(self.namespace, 'update')

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
                    cfg.log.debug("API_kv/update: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise KVError("API_kv/update: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # get the whole damn KV table

            # filtery by unqdn (or any portion thereof)
            if unqdn != None:
                hostname, realm, site_id = v_split_unqn(unqdn)
                buf += "unqdn=%s hostname=%s realm=%s site_id=%s " % (unqdn, hostname, realm, site_id)
            else:
                buf += "unqdn=(global!) hostname=%s realm=%s site_id=%s " % (hostname, realm, site_id)
            # try to find an existing entry
            result = cfg.dbsess.query(KV).\
                filter(KV.site_id==site_id).\
                filter(KV.realm==realm).\
                filter(KV.hostname==hostname).\
                filter(KV.key==key).\
                filter(KV.value==value).first()
            if result:
                cfg.log.debug(buf)
                result.value = new_value
                cfg.dbsess.add(result)
                cfg.dbsess.commit()
                return 'success'
            else:
                cfg.dbsess.rollback()
                raise KVError("API_kv/update: query failed for unqdn=%s key=%s value=%s, no record to update" % (unqdn, key, value))
        except Exception, e:
            cfg.dbsess.rollback()
            raise KVError("API_kv/update: error: %s" % e) 

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
        valid_qkeys = self.common.get_valid_qkeys(self.namespace, 'delete')

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
                    cfg.log.debug("API_kv/delete: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise KVError("API_kv/delete: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # filtery by unqdn (or any portion thereof)
            if unqdn != 'GLOBAL':
                hostname, realm, site_id = v_split_unqn(unqdn)
                buf += "unqdn=%s hostname=%s realm=%s site_id=%s " % (unqdn, hostname, realm, site_id)
            else:
                buf += "unqdn=(global!)"
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
                cfg.log.debug(buf)
                return 'success'
            else:
                cfg.log.debug("API_kv/delete: query failed for unqdn=%s key=%s value=%s, nothing to delete!" % (unqdn, key, value))
                cfg.dbsess.rollback()
                raise KVError("API_kv/delete: query failed for unqdn=%s key=%s value=%s, nothing to delete!" % (unqdn, key, value))
        except Exception, e:
            cfg.dbsess.rollback()
            raise KVError("API_kv/delete: error: %s" % e) 

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
        try:
            if unqdn == 'GLOBAL':
                hostname, realm, site_id = (None,)*3
            else:
                hostname, realm, site_id = v_split_unqn(unqdn)
            if hostname:
                v_get_server_obj(self.cfg, unqdn)
            elif realm:
                v_unqn_in_servers(self.cfg, realm, site_id)
            elif site_id:
                v_site_id(self.cfg, site_id)
 
            kv = KV(key, value, hostname, realm, site_id)
            return kv
        except Exception, e:
            self.cfg.dbsess.rollback()
            raise KVError("API_kv/__new: error: %s" % e) 
