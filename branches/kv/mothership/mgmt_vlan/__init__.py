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
for controlling port states on a management vlan
"""

import mothership
import subprocess

# Useful handy functions brought in from mothership
from mothership.kv import collect as kv_collect
from mothership.kv import select as kv_select

# All of the models and sqlalchemy are brought in
# to simplify referencing
from mothership.mothership_models import *


def enable(cfg, host, realm, site_id):
    """
    [description]
    un-shut a server's port on the management switch

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        host: the server whose port we're enabling
        realm: the realm the server lives in
        site_id: the site_id the server lives in

    [return value]
    no explicit return
    """ 

    # get management vlan web control panel credentials
    discard,user = str(kv_select(cfg, '', key="mgmt_vlan_web_control_user")).split('=')
    discard,password = str(kv_select(cfg, '', key="mgmt_vlan_web_control_password")).split('=')

    # get server switch port info
    s, n, h = mothership.snh(cfg, host, realm, site_id)
    for iface in n:
      if iface.interface == cfg.mgmt_vlan_interface:
        print "enabling mgmt port for %s.%s.%s" % (host, realm, site_id)
        switch_port = iface.switch_port
      else:
        pass

    # decide what method to use, based on /etc/mothership.yaml
    if cfg.mgmt_vlan_style == 'snmp':
        #need to write some method for snmp control
        print "snmp management vlan control has not yet been implemented" 
    elif cfg.mgmt_vlan_style == 'curl':
        # build our command line
        cmdln = "curl"
        upass = user + ":" + password
        cmdurl = cfg.mgmt_vlan_enable_url + switch_port
        # fire off a curl to hit the web control panel and enable the port
        subprocess.Popen([cmdln, '-k', '-u', upass, cmdurl], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        status(cfg, host, realm, site_id)
    else:
        print "An odd failure occurred in the mgmt_vlan section. please check your config"

def disable(cfg, host, realm, site_id):
    """
    [description]
    shut a server's port on the management switch

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        host: the server whose port we're disabling
        realm: the realm the server lives in
        site_id: the site_id the server lives in

    [return value]
    no explicit return
    """ 

    # get management vlan web control panel credentials
    discard,user = str(kv_select(cfg, '', key="mgmt_vlan_web_control_user")).split('=')
    discard,password = str(kv_select(cfg, '', key="mgmt_vlan_web_control_password")).split('=')

    # get server switch port info
    s, n, h = mothership.snh(cfg, host, realm, site_id)
    for iface in n:
      if iface.interface == cfg.mgmt_vlan_interface:
        print "disabling mgmt port for %s.%s.%s" % (host, realm, site_id)
        switch_port = iface.switch_port
      else:
        pass

    # decide what method to use, based on /etc/mothership.yaml
    if cfg.mgmt_vlan_style == 'snmp':
        #need to write some method for snmp control
        print "snmp management vlan control has not yet been implemented" 
    elif cfg.mgmt_vlan_style == 'curl':
        # build our command line
        cmdln = "curl"
        upass = user + ":" + password
        cmdurl = cfg.mgmt_vlan_disable_url + switch_port
        # fire off a curl to hit the web control panel and enable the port
        subprocess.Popen([cmdln, '-k', '-u', upass, cmdurl], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        status(cfg, host, realm, site_id)
    else:
        print "An odd failure occurred in the mgmt_vlan section. please check your config"


def status(cfg, host, realm, site_id):
    """
    [description]
    get status for a server's port on the management switch

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        host: the server whose port we're checking
        realm: the realm the server lives in
        site_id: the site_id the server lives in

    [return value]
    no explicit return
    """ 

    # get management vlan web control panel credentials
    discard,user = str(kv_select(cfg, '', key="mgmt_vlan_web_control_user")).split('=')
    discard,password = str(kv_select(cfg, '', key="mgmt_vlan_web_control_password")).split('=')

    # gather server info
    s, n, h = mothership.snh(cfg, host, realm, site_id)
    for iface in n:
      if iface.interface == cfg.mgmt_vlan_interface:
        switch_port = iface.switch_port
      else:
        pass

    # decide what method to use, based on /etc/mothership.yaml
    if cfg.mgmt_vlan_style == 'snmp':
        #need to write some method for snmp control
        print "snmp management vlan control has not yet been implemented" 
    elif cfg.mgmt_vlan_style == 'curl':
        # build our command line
        cmdln = "curl"
        upass = user + ":" + password
        cmdurl = cfg.mgmt_vlan_status_url 
        # fire off a curl to hit the web control panel and enable the port
        status = subprocess.Popen([cmdln, '-k', '-u', upass, cmdurl], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]

        # a bit of sanity
        if status:
          statuses = status.split('\n')
        else:
          print "Error, status check did not return data! Maybe something is wrong with your switch(es)?"
          return

        # search for our port
        for i in statuses:
          try:
            if i.index(switch_port):
              print i
              break
          except ValueError:
            pass
    else:
        print "An odd failure occurred in the mgmt_vlan section. please check your config"
