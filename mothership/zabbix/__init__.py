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
mothership.zabbix 
for interacting with the zabbix API

requires a third-party download of the zabbix API!
see INSTALL
"""

import sys
import mothership

# Useful handy functions brought in from mothership
from mothership.kv import collect as kv_collect
from mothership.kv import select as kv_select

# All of the models and sqlalchemy are brought in
# to simplify referencing
from mothership.mothership_models import *

def add(cfg, unqdn, zs_unqdn, zabbix_template):
    """
    [description]
    add a server to Zabbix 

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        unqdn: unqualified domain name of the server to add
        zs_unqdn: unqdn of the zabbix server
        zabbix_template: zabbix template to link the server to

    [return value]
    no explicit return
    """

    # check to see if zabbix is enabled in the config
    if cfg.zab_active == False:
      print "Zabbix is not active, skipping. Zabbix can be enabled in the mothership config file."
      return
    else:
      # Import Zabbix API
      from zabbix_api2 import ZabbixAPI, ZabbixAPIException

    # stitch together some info about our host
    host,realm,site_id = mothership.split_fqdn(unqdn)
    fqdn = '.'.join([unqdn,cfg.domain])
    if zs_unqdn==None:
      zs_unqdn, zs_user, zs_pass = get_default_server(cfg, realm, site_id)
    else:
      zs_user = str(kv_select(cfg, zs_unqdn, key="zabbix_admin_user")).split('=')[1]
      zs_pass = str(kv_select(cfg, zs_unqdn, key="zabbix_admin_pass")).split('=')[1]
    zs_host,zs_realm,zs_site_id = mothership.split_fqdn(zs_unqdn)
    zs_fqdn = '.'.join([zs_unqdn,cfg.domain])

    # set the zabbix host and url path, log in
    try:
        # uncomment to debug
        #zapi = ZabbixAPI(zs_fqdn,'/', debug_level=6)
        zapi = ZabbixAPI(zs_fqdn,'/')
        zapi.login(zs_user, zs_pass)
        # uncomment to debug
        #print "Zabbix API Version: %s" % zapi.api_version()
        #print "Logged in: %s" % str(zapi.test_login())
    except ZabbixAPIException, e:
        sys.stderr.write(str(e) + '\n')

    # get server info
    s, n, h = mothership.snh(cfg, host, realm, site_id)

    # Construct the tag template name.
    # All templates descend from the default
    discard,zab_def_tmpl = str(kv_select(cfg, '', key="zabbix_default_template")).split('=')
    # uncomment to debug
    #print 'Default template is: ' + zab_def_tmpl
    zab_tag_tmpl = zab_def_tmpl + '_' + s.tag
    # get the templateid from zabbix   
    zab_tid = None
    t = zapi.template.get(host=zab_tag_tmpl)
    if t:
      for k in t.keys():
        zab_tid = t[k]['templateid']
    else:
      pass 

    # if we're given a template, try and use that
    if zabbix_template:
      t = zapi.template.get(host=zabbix_template)
      if t:
        for k in t.keys():
          zab_tid = t[k]['templateid']
        print "Found template for: " + zabbix_template + ", templateid: " + zab_tid
      # if template we were given doesn't exist, try the tag template
      elif zab_tid:
        print "No template found for: " + zabbix_template + ", trying tag template for \"" + zab_tag_tmpl + "\""
        print "Found tag template for: " + zab_tag_tmpl + ", templateid: " + zab_tid
      else:
        print "No template found for: " + zabbix_template + ", trying tag template for \"" + zab_tag_tmpl + "\""
        print "No tag template found for: " + zab_tag_tmpl + ", creating one and linking to the default: "+zab_def_tmpl

        # we'll need the hostgroup ID for the "Templates" group
        tgid = None
        hg = zapi.hostgroup.get(filter={'name':'Templates'})
        if hg:
          for k in hg:
            tgid = k['groupid']
        else:
          print "Templates group not found! Fix Zabbix"
    
        if tgid:
           print "Templates group id: "+tgid
        else:
           print "Templates goup id is empty, something went wrong"

        # Get the template ID for the default template
        discard,zab_def_tmpl = str(kv_select(cfg, '', key="zabbix_default_template")).split('=')
        t = zapi.template.get(host=zab_def_tmpl)
        if t:
          for k in t.keys():
            zab_tid = t[k]['templateid'] 
            print "Found default template: " + zab_def_tmpl + ", templateid: " + zab_tid
        else:
          print "No default template! Check mothership's KV"
          return
         
        # Create the tag template, assign it to the default Templates group, link to the default template
        t = zapi.template.create(host=zab_tag_tmpl, groups={'groupid':tgid}, templates={'templateid':zab_tid})
        print "Created template: "+zab_tag_tmpl+" with template ID: "+t['templateids'][0]
        zab_tid = t['templateids'][0]

    # if no template is given and if one exists, use the tag template
    # this is constructed automatically from the tag name
    elif zab_tid:
      print "No template supplied, trying tag template for \"" + zab_tag_tmpl + "\""
      print "Found tag template for: " + zab_tag_tmpl + ", templateid: " + zab_tid
    # if all else fails, create a tag template linked to the default template
    else:
        print "No tag template found for: " + zab_tag_tmpl + ", creating one and linking to the default: "+zab_def_tmpl

        # we'll need the hostgroup ID for the "Templates" group
        tgid = None
        hg = zapi.hostgroup.get(filter={'name':'Templates'})
        if hg:
            tgid = hg[0]['groupid']
        else:
          print "Templates group not found! Fix Zabbix"
    
        if tgid:
           print "Templates group id: "+tgid
        else:
           print "Templates goup id is empty, something went wrong"

        # Get the template ID for the default template
        discard,zab_def_tmpl = str(kv_select(cfg, '', key="zabbix_default_template")).split('=')
        t = zapi.template.get(host=zab_def_tmpl)
        if t:
          for k in t.keys():
            zab_tid = t[k]['templateid'] 
            print "Found default template: " + zab_def_tmpl + ", templateid: " + zab_tid
        else:
          print "No default template! Check mothership's KV"
          return
         
        # Create the tag template, assign it to the default Templates group, link to the default template
        t = zapi.template.create(host=zab_tag_tmpl, groups={'groupid':tgid}, templates={'templateid':zab_tid})
        print "Created template: "+zab_tag_tmpl+" with template ID: "+t['templateids'][0]
        zab_tid = t['templateids'][0]


    # Check to see if the tag has a group. if not, create it
    zab_tag_group = []
    a_tags = kv_collect(cfg, unqdn, key='tag')
    t = zapi.hostgroup.get(filter={'name':s.tag})
    if t:
        print "Found group "+s.tag+" adding "+unqdn+" to it"
        zab_tag_group.append(t)
    else:
        print "No group found for "+s.tag+", creating it and adding "+unqdn+" to it"
        hgid = zapi.hostgroup.create(name=s.tag)['groupids'][0]
        zab_tag_group.append(hgid)

    # check to see if the ancillary tags have groups. if not, create them
    for tag_kv in a_tags:
      discard,r = str(tag_kv).split('=')
      t = zapi.hostgroup.get(filter={'name':r})
      if t:
          print "Found group "+r+" adding "+unqdn+" to it"
          zab_tag_group.append(t)
      else:
          print "No group found for "+r+", creating it and adding "+unqdn+" to it"
          hgid = zapi.hostgroup.create(name=r)['groupids'][0]
          zab_tag_group.append(hgid)

    # Insert the host into zabbix
    try:
      zapi.host.create(host=unqdn, dns=fqdn, groups=zab_tag_group, templates=[zab_tid], port='10050')
    except ZabbixAPIException, e:
      sys.stderr.write(str(e) + '\n')


def remove(cfg, unqdn, zs_unqdn):
    """
    [description]
    Delete a server *completely* from zabbix. 
    removes all graphs and data items from the DB

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        unqdn: unqualified domain name of the server to delete 
        zs_unqdn: unqdn of the zabbix server

    [return value]
    no explicit return
    """


    # check to see if zabbix is enabled in the config
    if cfg.zab_active == False:
      print "Zabbix is not active, skipping. Zabbix can be enabled in the mothership config file."
      return
    else:
      pass

    # stitch together some info about our host
    host,realm,site_id = mothership.split_fqdn(unqdn)
    if zs_unqdn==None:
      zs_unqdn, zs_user, zs_pass = get_default_server(cfg, realm, site_id)
    else:
      zs_user = str(kv_select(cfg, zs_unqdn, key="zabbix_admin_user")).split('=')[1]
      zs_pass = str(kv_select(cfg, zs_unqdn, key="zabbix_admin_pass")).split('=')[1]
    zs_host,zs_realm,zs_site_id = mothership.split_fqdn(zs_unqdn)
    zs_fqdn = '.'.join([zs_unqdn,cfg.domain])

    # set the zabbix host and url path, log in
    try:
        # uncomment to debug
        #zapi = ZabbixAPI(zs_fqdn,'/', debug_level=6)
        zapi = ZabbixAPI(zs_fqdn,'/')
        zapi.login(zs_user, zs_pass)
        # uncomment to debug
        #print "Zabbix API Version: %s" % zapi.api_version()
        #print "Logged in: %s" % str(zapi.test_login())
    except ZabbixAPIException, e:
        sys.stderr.write(str(e) + '\n')

    try:
      t = zapi.host.get(filter={'host':unqdn})
    except ZabbixAPIException, e:
      sys.stderr.write(str(e) + '\n')
    hid = None
    if t:
        hid = t['hostid']
        print unqdn+" found, host id is: " + hid
    else:
        print "Host not found: " + unqdn
    
    if hid:
      print '\n********************************************************************'
      print '* ACHTUNG! This will remove all data associated with this machine! *'
      print '*     To stop taking data but keep all graphs, use "--disable"     *'
      print '********************************************************************\n'
      ans = raw_input('To continue deleting, please type "delete_%s": ' % host)
      if ans != 'delete_%s' % host:
        print 'Remove server aborted'
      else:
        zapi.host.delete([hid])
        print "Completely removing host "+host+" with ID: "+hid
    else:
      print "Host ID is empty, aborting"


def enable(cfg, unqdn, zs_unqdn):
    """
    [description]
    enable a server within zabbix

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        unqdn: unqualified domain name of the server to enable 
        zs_unqdn: unqdn of the zabbix server

    [return value]
    no explicit return
    """



    # check to see if zabbix is enabled in the config
    if cfg.zab_active == False:
      print "Zabbix is not active, skipping. Zabbix can be enabled in the mothership config file."
      return
    else:
      pass

    # stitch together some info about our host
    host,realm,site_id = mothership.split_fqdn(unqdn)
    if zs_unqdn==None:
      zs_unqdn, zs_user, zs_pass = get_default_server(cfg, realm, site_id)
    else:
      zs_user = str(kv_select(cfg, zs_unqdn, key="zabbix_admin_user")).split('=')[1]
      zs_pass = str(kv_select(cfg, zs_unqdn, key="zabbix_admin_pass")).split('=')[1]
    zs_host,zs_realm,zs_site_id = mothership.split_fqdn(zs_unqdn)
    zs_fqdn = '.'.join([zs_unqdn,cfg.domain])

    # set the zabbix host and url path, log in
    try:
        # uncomment to debug
        #zapi = ZabbixAPI(zs_fqdn,'/', debug_level=6)
        zapi = ZabbixAPI(zs_fqdn,'/')
        zapi.login(zs_user, zs_pass)
        # uncomment to debug
        #print "Zabbix API Version: %s" % zapi.api_version()
        #print "Logged in: %s" % str(zapi.test_login())
    except ZabbixAPIException, e:
        sys.stderr.write(str(e) + '\n')

    # get host info
    t = zapi.host.get(filter={'host':unqdn}, output='extend')
    hid = None
    if t:
        hid = t['hostid']
        hstatus = t['status']
    else:
        print "Host not found: " + unqdn

    # enable only if it's disabled, let the user know
    if hstatus == '0': 
      print "Host is already enabled"
      return
    else:
      print unqdn+" is disabled, enabling"
      zapi.host.update(hostid=hid, status='0') 
    
    
def disable(cfg, unqdn, zs_unqdn):
    """
    [description]
    disable a server within zabbix

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        unqdn: unqualified domain name of the server to disable
        zs_unqdn: unqdn of the zabbix server

    [return value]
    no explicit return
    """

    # just making sure something is assigned to it...
    hstatus = None

    # check to see if zabbix is enabled in the config
    if cfg.zab_active == False:
      print "Zabbix is not active, skipping. Zabbix can be enabled in the mothership config file."
      return
    else:
      pass

    # stitch together some info about our host
    host,realm,site_id = mothership.split_fqdn(unqdn)
    if zs_unqdn==None:
      zs_unqdn, zs_user, zs_pass = get_default_server(cfg, realm, site_id)
    else:
      zs_user = str(kv_select(cfg, zs_unqdn, key="zabbix_admin_user")).split('=')[1]
      zs_pass = str(kv_select(cfg, zs_unqdn, key="zabbix_admin_pass")).split('=')[1]
    zs_host,zs_realm,zs_site_id = mothership.split_fqdn(zs_unqdn)
    zs_fqdn = '.'.join([zs_unqdn,cfg.domain])

    # set the zabbix host and url path, log in
    try:
        # uncomment to debug
        #zapi = ZabbixAPI(zs_fqdn,'/', debug_level=6)
        zapi = ZabbixAPI(zs_fqdn,'/')
        zapi.login(zs_user, zs_pass)
        # uncomment to debug
        #print "Zabbix API Version: %s" % zapi.api_version()
        #print "Logged in: %s" % str(zapi.test_login())
    except ZabbixAPIException, e:
        sys.stderr.write(str(e) + '\n')

    # get host info
    t = zapi.host.get(filter={'host':unqdn}, output='extend')
    hid = None
    if t:
        hid = t['hostid']
        hstatus = t['status']
    else:
        print "Host not found: " + unqdn

    # disable only if it's enabled, let the user know
    if hstatus != '0':
        print unqdn+" is already disabled"
        return
    else:
        print "Disabling %s in zabbix. to completely delete all data use \"ship zbx -r\"" % unqdn
        zapi.host.update(hostid=hid, status='1') 


# Display info about a host in zabbix
def display(cfg, unqdn, zs_unqdn):
    """
    [description]
    display a server's zabbix info

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        unqdn: unqualified domain name of the server to display 
        zs_unqdn: unqdn of the zabbix server

    [return value]
    no explicit return
    """


    # check to see if zabbix is enabled in the config
    if cfg.zab_active == False:
      print "Zabbix is not active, skipping. Zabbix can be enabled in the mothership config file."
      return
    else:
      pass

    # stitch together some info about our host
    host,realm,site_id = mothership.split_fqdn(unqdn)
    if zs_unqdn==None:
      zs_unqdn, zs_user, zs_pass = get_default_server(cfg, realm, site_id)
    else:
      zs_user = str(kv_select(cfg, zs_unqdn, key="zabbix_admin_user")).split('=')[1]
      zs_pass = str(kv_select(cfg, zs_unqdn, key="zabbix_admin_pass")).split('=')[1]
    zs_host,zs_realm,zs_site_id = mothership.split_fqdn(zs_unqdn)
    zs_fqdn = '.'.join([zs_unqdn,cfg.domain])

    # set the zabbix host and url path, log in
    try:
        # uncomment to debug
        #zapi = ZabbixAPI(zs_fqdn,'/', debug_level=6)
        zapi = ZabbixAPI(zs_fqdn,'/')
        zapi.login(zs_user, zs_pass)
        # uncomment to debug
        #print "Zabbix API Version: %s" % zapi.api_version()
        #print "Logged in: %s" % str(zapi.test_login())
    except ZabbixAPIException, e:
        sys.stderr.write(str(e) + '\n')

    # get server,network,hardware info
    s, n, h = mothership.snh(cfg, host, realm, site_id)
 
    # get group id for group "Templates"
    tgid = None
    hg = zapi.hostgroup.get(filter={'name':'Templates'})
    if hg:
        tgid = t['groupid']
    else:
      print "Templates group not found! Fix Zabbix"

    if tgid:
      print "Templates group id: "+tgid
    else:
      print "Templates goup id is empty, something went wrong"

   
    # get default template info 
    discard,zab_def_tmpl = str(kv_select(cfg, '', key="zabbix_default_template")).split('=')
    t = zapi.template.get(host=zab_def_tmpl)
    if t:
      for k in t.keys():
        zab_tid = t[k]['templateid'] 
        print "Found default template: " + zab_def_tmpl + ", templateid: " + zab_tid
    else:
      print "No default template! Check mothership's KV"

    # get tag template id if exists
    tname = zab_def_tmpl+s.tag
    t = zapi.template.get(host=tname)
    if t:
      for k in t:
        tid = t[k]['templateid']
      print "Template "+tname+" found, ID: "+tid
    else:
      print "Template not found: "+tname

    # get host status 
    t = zapi.host.get(filter={'host':unqdn}, output='extend')
    hid = None
    if t:
        hid = t['hostid']
        hstatus = t['status']
        if hstatus == '0':
          print unqdn+" id: "+hid+" status: "+hstatus+" (enabled)"
        else:
          print unqdn+" id: "+hid+" status: "+hstatus+" (disabled)"
    else:
        print "Host not found: " + unqdn


def get_default_server(cfg, realm, site_id):
    """
    [description]
    retrieves and returns the default server, user, and pass for zabbix in whatever the realm.site_id is its given
     

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        realm: realm to return server data for
        site_id: site_id to return server data for

    [return value]
    returns zs_unqdn, zs_user, zs_pass as a list 
    """

    serv = cfg.dbsess.query(Server).\
    filter(Server.tag=="zabbix_server").\
    filter(Server.realm==realm).\
    filter(Server.site_id==site_id).\
    first()
    
    zs_unqdn = '.'.join([serv.hostname,realm,site_id])
    discard,zs_user = str(kv_select(cfg, zs_unqdn, key="zabbix_admin_user")).split('=')
    discard,zs_pass = str(kv_select(cfg, zs_unqdn, key="zabbix_admin_pass")).split('=')

    retval = [zs_unqdn, zs_user, zs_pass]
    return retval
