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
                            'fqdn': {
                                'vartype': 'string',
                                'desc': 'fqdn/unqdn/realm_path of the entry',
                            },
                            'key': {
                                'vartype': 'string',
                                'desc': 'key to filter on (use "%" for all keys)',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 1,
                        'args': {
                            'value': {
                                'vartype': 'string',
                                'desc': 'value to filter on',
                            },
                        },
                    },
                    'cmdln_aliases': [
                        'kv_select',
                        'key_value_select',
                    ],
                    'return': {
                        'kv_entry': 'dict',
                    },
                },
            },
        }


    # select a single query
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
        cfg = self.cfg
        try:
            # check for reasonable query values
            if 'fqdn' in query.keys() and query['fqdn']:
                if cfg.debug:
                    print "API_kv/select: querying for fqdn: %s" % query['fqdn']
            else:
                if cfg.debug:
                    print "API_kv/select: you must specify a (string) fqdn"
                raise KVError("API_kv/select: you must specify a (string) fqdn")

            if 'key' in query.keys() and query['key']:
                if cfg.debug:
                    print "API_kv/select: querying for key: %s" % query['key']
            else:
                if cfg.debug:
                    print "API_kv/select: you must specify a (string) key"
                raise KVError("API_kv/select: you must specify a (string) key")

            # translate our fqdn to hostname, realm, site_id
            try:
                hostname, realm, site_id = mothership.split_fqdn(query['fqdn'])
            except:
                if cfg.debug:
                    print "API_kv/select: mothership.get_unqdn(query['fqdn']) failed!"
                raise KVError("API_kv/select: mothership.get_unqdn(query['fqdn']) failed!")

            # get stuff from the db
            # query on value if we're asked to
            if 'value' in query.keys() and query['value']:
                if cfg.debug:
                    print "API_kv/select: querying for value: %s" % query['value']
                try:
                    kv_entry = cfg.dbsess.query(KV).\
                        filter(KV.hostname==hostname).\
                        filter(KV.realm==realm).\
                        filter(KV.site_id==site_id).\
                        filter(KV.key==query['key']).\
                        filter(KV.value==query['value']).first()
                    if not kv_entry:
                        raise KVError("API_kv/select: kv_entry is empty! (value provided)")
                except Exception, e:
                    if cfg.debug:
                        print "API_kv/select: query for value failed: %s\nerror: %s" % (query['value'], e)
                    raise KVError("API_kv/select: query for value failed: %s\nerror: %s" % (query['value'], e))
            elif 'value' in query.keys() and not query['value']:
                if cfg.debug:
                    print "API_kv/select: you must provide a (string) value in order to query by value"
                raise KVError("API_kv/select: you must provide a (string) value in order to query by value")
            # if we don't get a value
            else:
                try:
                    kv_entry = cfg.dbsess.query(KV).\
                        filter(KV.hostname==hostname).\
                        filter(KV.realm==realm).\
                        filter(KV.site_id==site_id).\
                        filter(KV.key==query['key']).first()
                except Exception, e:
                    if cfg.debug:
                        print "API_kv/select: query for fqdn failed: %s\nerror: %s" % (query['fqdn'], e)
                        print "API_kv/select: hostname=%s, realm=%s, site_id=%s, key=%s" % (hostname, realm, site_id, query['key'])
                    raise KVError("API_kv/select: query for fqdn failed: %s]nerror: %s" % (query['fqdn'], e))

            # just need one result
            try:
                return kv_entry.to_dict()
            except Exception, e:
                if cfg.debug:
                    print "API_kv/select: kv_entry = results.first() failed\nAPI_kv/select: error: %s\nhostname=%s, realm=%s, site_id=%s, key=%s" % (e, hostname, realm, site_id, query['key'])
                raise KVError("API_kv/select: kv_entry = results.first() failed\nAPI_kv/select: error: %s\nhostname=%s, realm=%s, site_id=%s, key=%s" % (e, hostname, realm, site_id, query['key']))
        except KVError, e:
            raise KVError(e)









#def new(fqdn, key, value):
#    """
#    Constructor that takes a host.realm.site style fqdn.
#    """
#    hostname, realm, site_id = mothership.split_fqdn(fqdn)
#    kv = KV(key, value, hostname, realm, site_id)
#    return kv
#
#
#def collect(cfg, fqdn, key=None, value=None):
#    """
#    Returns a list of all matches.
#    """
#    results = cfg.dbsess.query(KV)
#
#    if fqdn != None:
#        hostname, realm, site_id = mothership.split_fqdn(fqdn)
#        results = results.\
#            filter(or_(KV.site_id==site_id, KV.site_id==None)).\
#            filter(or_(KV.realm==realm, KV.realm==None)).\
#            filter(or_(KV.hostname==hostname, KV.hostname==None)).\
#            order_by(desc(KV.hostname), desc(KV.realm), desc(KV.site_id))
#    if key:
#        results = results.filter(KV.key==key)
#    if value:
#        results = results.filter(KV.value==value)
#
#    kvs = results.all()
#    return kvs
#
#def add(cfg, fqdn, key, value):
#    """
#    Add a new value with set semantics.
#    """
#    # make sure we have a value
#    if not value:
#        raise KVError('No value specified!')
#
#    # Check for duplicate key=value.
#    kv = select(cfg, fqdn, key, value)
#    if kv:
#        print "that key=value pair exists already!"
#        ans = raw_input("Do you want to update it? (y/n): ")
#        if ans == "Y" or ans == "y":
#            print "updating key=value"
#            kv = upsert(cfg, fqdn, key, value)
#            return kv
#        else:
#            print "key=value unchanged, exiting."
#            return kv
#    print "no existing key=value found, inserting."
#    if fqdn == '':
#        print "this will apply %s=%s globally" % (key, value)
#        ans = raw_input("are you sure you want to do this? (y/n): ")
#        if ans == "Y" or ans == "y":
#            kv = new(fqdn, key, value)
#            cfg.dbsess.add(kv)
#            cfg.dbsess.commit()
#            return kv
#    kv = new(fqdn, key, value)
#    cfg.dbsess.add(kv)
#    cfg.dbsess.commit()
#    return kv
#
#def upsert(cfg, fqdn, key, value):
#    """
#    Insert a new value or update existing.
#    """
#    kv = select(cfg, fqdn, key)
#    if not kv:
#        print "key=value not found, adding"
#        kv = new(fqdn, key, value)
#    print "key=value found, updating"
#    kv.value = value
#    cfg.dbsess.add(kv)
#    cfg.dbsess.commit()
#    return kv
#
#def delete(cfg, fqdn, key, value):
#    """
#    Delete a row matching both key and value.
#    """
#    kv = select(cfg, fqdn, key, value=value)
#    if kv:
#        cfg.dbsess.delete(kv)
#        cfg.dbsess.commit()
#    else:
#        print "key=value not found, exiting."
