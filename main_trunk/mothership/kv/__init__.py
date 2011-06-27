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
    mothership.kv

    Package for interacting with the KV store in mothership
"""

from sqlalchemy import or_, desc, MetaData

import mothership
from mothership_models import *

def new(fqdn, key, value):
    """
    Constructor that takes a host.realm.site style fqdn.
    """
    hostname, realm, site_id = mothership.split_fqdn(fqdn)
    kv = KV(key, value, hostname, realm, site_id)
    return kv

def select(cfg, fqdn, key, value=None):
    """
    Returns a specific KV object.
    """
    hostname, realm, site_id = mothership.split_fqdn(fqdn)
    results = cfg.dbsess.query(KV).\
            filter(KV.site_id==site_id).\
            filter(KV.realm==realm).\
            filter(KV.hostname==hostname).\
            filter(KV.key==key)
    if value:
        results = results.filter(KV.value==value)
    kv = results.first()
    return kv

def collect(cfg, fqdn, key=None, value=None):
    """
    Returns a list of all matches.
    """
    results = cfg.dbsess.query(KV)

    if fqdn != None:
        hostname, realm, site_id = mothership.split_fqdn(fqdn)
        results = results.\
            filter(or_(KV.site_id==site_id, KV.site_id==None)).\
            filter(or_(KV.realm==realm, KV.realm==None)).\
            filter(or_(KV.hostname==hostname, KV.hostname==None)).\
            order_by(desc(KV.site_id), desc(KV.realm), desc(KV.hostname))
    if key:
        results = results.filter(KV.key==key)
    if value:
        results = results.filter(KV.value==value)

    kvs = results.all()
    return kvs

def add(cfg, fqdn, key, value):
    """
    Add a new value with set semantics.
    """
    # Check for duplicate key=value.
    kv = select(cfg, fqdn, key, value)
    if kv:
        return kv
    kv = new(fqdn, key, value)
    cfg.dbsess.add(kv)
    cfg.dbsess.commit()
    return kv

def upsert(cfg, fqdn, key, value):
    """
    Insert a new value or update existing.
    """
    kv = select(cfg, fqdn, key)
    if not kv:
        kv = new(fqdn, key, value)
    kv.value = value
    cfg.dbsess.add(kv)
    cfg.dbsess.commit()
    return kv

def delete(cfg, fqdn, key, value):
    """
    Delete a row matching both key and value.
    """
    kv = select(cfg, fqdn, key, value=value)
    if kv:
        cfg.dbsess.delete(kv)
        cfg.dbsess.commit()
