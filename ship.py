#!/usr/bin/env python

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

# system imports
import sys
import optparse
import textwrap
import time
import datetime
import os
import urllib2
# for >=2.6 use json, >2.6 use simplejson
try:
    import json as myjson
except ImportError:
    import simplejson as myjson

# mothership imports
from mothership.configure import Configure, ConfigureCli

# if someone runs: ship
def print_submodules(cfg, module_list):
    try:
        print "Available submodules:\n"
        for i in module_list:
            response = urllib2.urlopen('http://'+cfg.api_server+':'+cfg.api_port+'/'+i+'/metadata')
            mmeta = myjson.loads(response.read())
            print i.split('API_')[-1]+': '+mmeta['config']['description']
        print "\nRun \"ship <submodule>\" for more information"
    except Exception, e:
        if cfg.debug:
            print "Error: %s" % e
        raise Exception("Error: %s" % e)

# if someone runs: ship <module>
def print_commands(cfg, module_list):
    try:
        response = urllib2.urlopen('http://'+cfg.api_server+':'+cfg.api_port+'/API_'+sys.argv[1]+'/metadata')
        mmeta = myjson.loads(response.read())
        print "Available module commands:\n"
        for k in mmeta['methods'].keys():
            print sys.argv[1]+'/'+k
        print "\nRun \"ship <submodule>/<command>\" for more information"
    except Exception, e:
        if cfg.debug:
            print "Error: %s" % e
        raise Exception("Error: %s" % e)

# if someone runs: ship <module>/<command>
def print_command_args(cfg, module_list):
    try:
        module, call = sys.argv[1].split('/')
        response = urllib2.urlopen('http://'+cfg.api_server+':'+cfg.api_port+'/API_'+module+'/metadata')
        mmeta = myjson.loads(response.read())
        if 'args' in mmeta['methods'][call]['required_args']:
            print "\nRequired arguments:"
            for k in mmeta['methods'][call]['required_args']['args'].keys():
                print "--%s (-%s): %s" % (k, mmeta['methods'][call]['required_args']['args'][k]['ol'], mmeta['methods'][call]['required_args']['args'][k]['desc'])
        if 'args' in mmeta['methods'][call]['optional_args']:
            print "\nOptional arguments, supply a minimum of %s and a maximum of %s of the following:" % (mmeta['methods'][call]['optional_args']['min'], mmeta['methods'][call]['optional_args']['max'])
            for k in mmeta['methods'][call]['optional_args']['args'].keys():
                print "--%s (-%s): %s" % (k, mmeta['methods'][call]['optional_args']['args'][k]['ol'], mmeta['methods'][call]['optional_args']['args'][k]['desc'])
        print ""
    except Exception, e:
        if cfg.debug:
            print "Error: %s" % e
        raise Exception("Error: %s" % e)


def call_command(cfg, module_list):
    try:
        if 'API_'+sys.argv[1].split('/')[0] in module_list:
            module, call = sys.argv[1].split('/')
            response = urllib2.urlopen('http://'+cfg.api_server+':'+cfg.api_port+'/API_'+module+'/metadata')
            mmeta = myjson.loads(response.read())
            options = []
            n = 2
            while n <= len(sys.argv):
                options.append(sys.argv[n])
                n += 1
            print options
    except Exception, e:
        if cfg.debug:
            print "Error: %s" % e
        raise Exception("Error: %s" % e)


# main execution block
if __name__ == "__main__":
    # the global config. useful everywhere
    cfg = ConfigureCli('mothership_cli.yaml')

    # useful global values
    today = datetime.date.today()

    # prevent root from running ship
    if sys.stdin.isatty():
        if os.getlogin() == 'root':
            print "Please do not run ship as root"
            raise Exception("Your effective uid: " + os.geteuid())

    # write out the command line we were called with to an audit log
    try:
        alog = open(cfg.audit_log_file, 'a')
        ltz = time.tzname[time.daylight]
        tformat = "%Y-%m-%d %H:%M:%S"
        timestamp = datetime.datetime.now()
        if sys.stdin.isatty():
            username = os.getlogin()
        else:
            username = "nottyUID=" + str(os.geteuid())
        command_run = ' '.join(sys.argv)
        buffer = "%s %s: %s: %s\n" % (ltz, timestamp.strftime(tformat), username, command_run)
        alog.write(buffer)
        alog.close()
    except Exception, e:
        print "Exception: " + str(e)
        print "Problem writing to audit log file!"
        print "Audit file configured as: " + cfg.audit_log_file
        print "logline dump:"
        print "%s %s: %s: %s" % (ltz, timestamp, username, command_run)
        alog.close()

    # doin stuff 
    try:
        # grab a list of loaded modules from the API server, decode the
        # json into a list object
        response = urllib2.urlopen('http://'+cfg.api_server+':'+cfg.api_port+'/modules')
        module_list = myjson.loads(response.read())

        # command line-y stuff.
        if len(sys.argv) < 2:
            print_submodules(cfg, module_list)
        elif len(sys.argv) == 2 and 'API_'+sys.argv[1] in module_list:
            print_commands(cfg, module_list)
        elif len(sys.argv) == 2 and 'API_'+sys.argv[1].split('/')[0] in module_list:
            print_command_args(cfg, module_list)
        elif len(sys.argv) >= 3:
            call_command(cfg, module_list)
        else:
            raise Exception("bad command line:\n%s" % sys.argv)

    except IOError, e:
        print "Missing config file: mothership_cli.yaml"
        print "ERROR: %s" % e
        sys.exit(1)
    except Exception, e:
        print "Error: %s" % e
