#!/usr/bin/env python26

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
import pprint
# urllib2 sucks when you need to use POST and you don't know beforehand
# that you need to use POST, so we use 'requests' instead.
import requests
from optparse import OptionParser
import json as myjson


# mothership imports
from mothership.configure import Configure, ConfigureCli

# if someone runs: ship
def print_submodules(cfg, module_list):
    try:
        print "Available submodules:\n"
        for i in module_list:
            response = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/'+i+'/metadata')
            mmeta = myjson.loads(response.content)
            print i.split('API_')[-1]+': '+mmeta['config']['description']
        print "\nRun \"ship <submodule>\" for more information"
    except Exception, e:
        if cfg.debug:
            print "Error: %s" % e
        raise Exception("Error: %s" % e)

# if someone runs: ship <module>
def print_commands(cfg, module_list):
    try:
        response = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/API_'+sys.argv[1]+'/metadata')
        mmeta = myjson.loads(response.content)
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
        response = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/API_'+module+'/metadata')
        mmeta = myjson.loads(response.content)
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

# if someone runs: ship <module>/<command> --option1=bleh -o2 foo
def call_command(cfg, module_list):
    try:
        if 'API_'+sys.argv[1].split('/')[0] in module_list:
            buf = "" # our argument buffer for urlencoding
            module, call = sys.argv[1].split('/')
            response = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/API_'+module+'/metadata')
            mmeta = myjson.loads(response.content)

            # set up our command line options through optparse. will
            # change this to argparse if we upgrade past python 2.7
            parser = OptionParser()
            arglist = {}
            if 'args' in mmeta['methods'][call]['required_args']:
                for k in mmeta['methods'][call]['required_args']['args'].keys():
                    if mmeta['methods'][call]['required_args']['args'][k]['vartype'] != "None":
                        parser.add_option('-'+mmeta['methods'][call]['required_args']['args'][k]['ol'],\
                                          '--'+k, help=mmeta['methods'][call]['required_args']['args'][k]['desc'])
                        arglist[k] = mmeta['methods'][call]['required_args']['args'][k]['vartype']
                    else:
                        parser.add_option('-'+mmeta['methods'][call]['required_args']['args'][k]['ol'],\
                                          '--'+k, help=mmeta['methods'][call]['required_args']['args'][k]['desc'],\
                                          action="store_true")
                        arglist[k] = mmeta['methods'][call]['required_args']['args'][k]['vartype']
            elif 'args' in mmeta['methods'][call]['optional_args']:
                for k in mmeta['methods'][call]['optional_args']['args'].keys():
                    if mmeta['methods'][call]['optional_args']['args'][k]['vartype'] != "None":
                        parser.add_option('-'+mmeta['methods'][call]['optional_args']['args'][k]['ol'],\
                                          '--'+k, help=mmeta['methods'][call]['optional_args']['args'][k]['desc'])
                        arglist[k] = mmeta['methods'][call]['optional_args']['args'][k]['vartype']
                    else:
                        parser.add_option('-'+mmeta['methods'][call]['optional_args']['args'][k]['ol'],\
                                          '--'+k, help=mmeta['methods'][call]['optional_args']['args'][k]['desc'],\
                                          action="store_true")
                        arglist[k] = mmeta['methods'][call]['optional_args']['args'][k]['vartype']
            else:
                raise Exception("Error: no arguments defined")

            # parse our options and build a urlencode string to pass
            # over to the API service
            (options, args) = parser.parse_args(sys.argv[2:])
            for k in arglist.keys():
                a = vars(options)[k]
                if a:
                    if buf:
                        buf += '&'
                    if a != True:
                        buf += k+'='+str(a)
                    else:
                        buf += k

            # make the call out to our API service, expect JSON back,
            # load the JSON into the equivalent python variable type
            if mmeta['methods'][call]['rest_type'] == 'GET':
                callresponse = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/API_'+module+'/'+call+'?'+buf)
            elif mmeta['methods'][call]['rest_type'] == 'POST':
                callresponse = requests.post('http://'+cfg.api_server+':'+cfg.api_port+'/API_'+module+'/'+call+'?'+buf)
            responsedata = myjson.loads(callresponse.content)

            # print. prettily.
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(responsedata)

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
        response = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/modules')
        module_list = myjson.loads(response.content)

        # command line-y stuff.
        if len(sys.argv) < 2:
            if cfg.debug:
                print "print_submodules called()"
            print_submodules(cfg, module_list)
        elif len(sys.argv) == 2 and 'API_'+sys.argv[1] in module_list:
            if cfg.debug:
                print "print_commands called()"
            print_commands(cfg, module_list)
        elif len(sys.argv) == 2 and 'API_'+sys.argv[1].split('/')[0] in module_list:
            if cfg.debug:
                print "print_command_args called()"
            print_command_args(cfg, module_list)
        elif len(sys.argv) >= 3:
            if cfg.debug:
                print "call_command called()"
            call_command(cfg, module_list)
        else:
            raise Exception("bad command line:\n" % sys.argv)

    except IOError, e:
        print "Missing config file: mothership_cli.yaml"
        print "ERROR: %s" % e
        sys.exit(1)
    except Exception, e:
        print "Error in __main__: %s" % e