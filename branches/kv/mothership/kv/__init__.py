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
from mothership.mothership_models import *

class KVError(Exception):
    pass

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
            filter(KV.hostname==hostname).\
            filter(KV.realm==realm).\
            filter(KV.site_id==site_id).\
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
            order_by(desc(KV.hostname), desc(KV.realm), desc(KV.site_id))
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
    # make sure we have a value
    if not value:
        raise KVError('No value specified!')

    # if we're adding a tag, make sure it exists, first!
    if key == 'tag':
        tag = cfg.dbsess.query(Tag).filter(Tag.name==value).first()
        if not tag:
            print "Trying to apply a nonexistent tag. Abort! Abort!"
            raise KVError('Try "ship tag --help" for more info')

    # make sure the serverpath exists
    hostname, realm, site_id = mothership.split_fqdn(fqdn)
    if hostname != None:
        results = cfg.dbsess.query(Server)
        results = results.\
            filter(Server.site_id==site_id).\
            filter(Server.realm==realm).\
            filter(Server.hostname==hostname).\
            first()
        if not results:
            raise KVError('Trying to apply a tag to a nonexistent host. Abort!')

    # Check for duplicate key=value.
    kv = select(cfg, fqdn, key, value)
    if kv:
        print "that key=value pair exists already!"
        ans = raw_input("Do you want to update it? (y/n): ")
        if ans == "Y" or ans == "y":
            print "updating key=value"
            kv = upsert(cfg, fqdn, key, value)
            return kv
        else:
            print "key=value unchanged, exiting."
            return kv
    print "no existing key=value found, inserting."
    if fqdn == '':
        print "this will apply %s=%s globally" % (key, value)
        ans = raw_input("are you sure you want to do this? (y/n): ")
        if ans == "Y" or ans == "y":
            kv = new(fqdn, key, value)
            cfg.dbsess.add(kv)
            cfg.dbsess.commit()
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
        print "key=value not found, adding"
        kv = new(fqdn, key, value)
    print "key=value found, updating"
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
    else:
        print "key=value not found, exiting."
