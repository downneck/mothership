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
                                'desc': 'fqdn/unqdn/realm_path of the entry. enter any portion or none',
                            },
                            'key': {
                                'vartype': 'string',
                                'desc': 'key to filter on (leave blank for all keys)',
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
        # assigning stuff
        cfg = self.cfg
        holdplease = None
        hostname = None
        realm = None
        site_id = None

        try:
            # check for reasonable query values
            if not 'fqdn' in query.keys():
                if cfg.debug:
                    print "API_kv/select: you must specify a fqdn querykey"
                raise KVError("API_kv/select: you must specify a fqdn querykey")

            if not 'key' in query.keys():
                if cfg.debug:
                    print "API_kv/select: you must specify a key querykey"
                raise KVError("API_kv/select: you must specify a key querykey")
            # if the key named 'value' doesn't have a value. mildly confusing
            if 'value' in query.keys() and not query['value']:
                if cfg.debug:
                    print "API_kv/select: you must provide a (string) value in order to query by value"
                raise KVError("API_kv/select: you must provide a (string) value in order to query by value")

            # quick out if we don't get values for anything, search
            # globally and return the first record
            if not query['fqdn'] and not query['key'] and 'values' not in query.keys():
                if cfg.debug:
                    print "API_kv/select: querying globally for all keys"
                kv_entry = cfg.dbsess.query(KV).first()

            # translate our fqdn to hostname, realm, site_id
            try:
                if query['fqdn']:
                    hostname, realm, site_id = mothership.split_fqdn(query['fqdn'])
            except Exception, e:
                if cfg.debug:
                    print "API_kv/select: mothership.split_fqdn(query['fqdn']) failed!\nerror: %s" % e
                raise KVError("API_kv/select: mothership.split_fqdn(query['fqdn']) failed!\nerror: %s" % e)

            # site_id, nothing else
            if site_id and not query['key'] and not hostname and not realm and 'value' not in query.keys():
                if cfg.debug:
                    print "API_kv/select: querying for: site_id" % site_id
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==query['key']).\
                               filter(KV.site_id==site_id).first()

            # site_id, realm, nothing else
            if site_id and realm and not query['key'] and 'value' not in query.keys() and not hostname:
                if cfg.debug:
                    print "API_kv/select: querying for: realm=%s, site_id=%s" % (realm, site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).first()

            # site_id, realm, hostname, nothing else
            if site_id and realm and hostname and not query['key'] and 'value' not in query.keys():
                if cfg.debug:
                    print "API_kv/select: querying for: hostname=%s, realm=%s, site_id=%s" % (hostname, realm, site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).\
                               filter(KV.hostname==hostname).first()

            # value, nothing else
            if 'value' in query.keys() and query['value'] and not query['fqdn'] and not query['key']:
                if cfg.debug:
                    print "API_kv/select: querying for: value=%s" % query['value']
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.value==query['value']).first()

            # value, site_id
            if site_id and 'value' in query.keys() and query['value'] and not hostname and not realm and not query['key']:
                if cfg.debug:
                    print "API_kv/select: querying for: value=%s, site_id=%s" % (query['value'], site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==query['value']).\
                               filter(KV.site_id==site_id).first()

            # value, site_id, realm
            if site_id and realm and 'value' in query.keys() and query['value'] and not hostname and not query['key']:
                if cfg.debug:
                    print "API_kv/select: querying for: value=%s, realm=%s, site_id=%s" % (query['value'], realm, site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==query['value']).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).first()

            # value, site_id, realm, hostname
            if site_id and realm and hostname and 'value' in query.keys() and query['value'] and not query['key']:
                if cfg.debug:
                    print "API_kv/select: querying for: value=%s, realm=%s, site_id=%s" % (query['value'], realm, site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==query['value']).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).\
                               filter(KV.hostname==hostname).first()

            # key, nothing else
            if query['key'] and not query['fqdn'] and 'value' not in query.keys():
                if cfg.debug:
                    print "API_kv/select: querying for: key=%s" % query['key']
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==query['key']).first()

            # site_id, key
            if site_id and query['key'] and not hostname and not realm and 'value' not in query.keys():
                if cfg.debug:
                    print "API_kv/select: querying for: key=%s, site_id=%s" % (query['key'], site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==query['key']).\
                               filter(KV.site_id==site_id).first()

            # realm, site_id, key
            if realm and site_id and query['key'] and not hostname and 'value' not in query.keys():
                if cfg.debug:
                    print "API_kv/select: querying for: key=%s, site_id=%s, realm=%s" % (query['key'], site_id, realm)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==query['key']).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).first()

            # hostname, realm, site_id, key
            if hostname and realm and site_id and query['key'] and 'value' not in query.keys():
                if cfg.debug:
                    print "API_kv/select: querying for: key=%s, site_id=%s, realm=%s, hostname=%s" % (query['key'], site_id, realm, hostname)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==query['key']).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).\
                               filter(KV.hostname==hostname).first()

            # key, value, nothing else
            if 'value' in query.keys() and query['value'] and query['key'] and not query['fqdn']:
                if cfg.debug:
                    print "API_kv/select: querying on: key=%s, value=%s" % (query['key'], query['value'])
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==query['key']).\
                               filter(KV.value==query['value']).first()

            # key, value, site_id
            if site_id and 'value' in query.keys() and query['value'] and query['key'] and not hostname and not realm:
                if cfg.debug:
                    print "API_kv/select: querying on: key=%s, value=%s, site_id=%s" % (query['key'], query['value'], site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==query['key']).\
                               filter(KV.value==query['value']).\
                               filter(KV.site_id==site_id).first()

            # key, value, site_id, realm
            if site_id and realm and 'value' in query.keys() and query['value'] and query['key'] and not hostname:
                if cfg.debug:
                    print "API_kv/select: querying on: key=%s, value=%s, realm=%s, site_id=%s" % (query['key'], query['value'], realm, site_id)
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==query['key']).\
                               filter(KV.value==query['value']).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).first()

            # hostname, realm, site_id, key, value
            if hostname and realm and site_id and query['key'] and 'value' in query.keys() and query['value']:
                if cfg.debug:
                    print "API_kv/select: querying for: key=%s, site_id=%s, realm=%s, hostname=%s, value=%s" % (query['key'], site_id, realm, hostname, query['value'])
                kv_entry = cfg.dbsess.query(KV).\
                               filter(KV.key==query['key']).\
                               filter(KV.site_id==site_id).\
                               filter(KV.realm==realm).\
                               filter(KV.hostname==hostname).\
                               filter(KV.value==query['value']).first()

            if kv_entry:
                return kv_entry.to_dict()
            else:
                if cfg.debug:
                    print "API_kv/select: no results found for query"
                return None

        except Exception, e:
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
