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
from jinja2 import Environment, FileSystemLoader
# urllib2 sucks when you need to use POST and you don't know beforehand
# that you need to use POST, so we use 'requests' instead. so that we
# can let the modules define themselves
import requests
from optparse import OptionParser
import json as myjson

# mothership imports
from mothership.configure import Configure, ConfigureCli


# our exception class
class ShipCLIError(Exception):
    pass


# swap a dict around
def swap_dict(odict):
    return dict([(v, k) for (k, v) in odict.iteritems()])


# if someone runs: ship
def print_submodules(cfg, module_map):
    try:
        print "Available submodules:\n"
        for i in module_map.keys():
            response = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/'+i+'/metadata')
            mmeta = myjson.loads(response.content)
            if mmeta['status'] != 0:
                print "Error occurred:\n%s" % mmeta['msg']
                sys.exit(1)
            print "%s (%s): %s" % (module_map[i], i.split('API_')[1], mmeta['data']['config']['description'])
        print "\nRun \"ship <submodule>\" for more information"
    except Exception, e:
        raise ShipCLIError("Error: %s" % e)


# if someone runs: ship <module>
def print_commands(cfg, module_map):
    try:
        revmodule_map = swap_dict(module_map)
        response = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/'+revmodule_map[sys.argv[1]]+'/metadata')
        mmeta = myjson.loads(response.content)
        if mmeta['status'] != 0:
            print "Error occurred:\n%s" % mmeta['msg']
            sys.exit(1)
        print "Available module commands:\n"
        for k in mmeta['data']['methods'].keys():
            print sys.argv[1]+'/'+k
        print "\nRun \"ship <submodule>/<command>\" for more information"
    except Exception, e:
        raise ShipCLIError("Error: %s" % e)


# if someone runs: ship <module>/<command>
def print_command_args(cfg, module_map):
    try:
        revmodule_map = swap_dict(module_map)
        module, call = sys.argv[1].split('/')
        response = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/'+revmodule_map[module]+'/metadata')
        mmeta = myjson.loads(response.content)
        if mmeta['status'] != 0:
            raise ShipCLIError("Error:\n%s" % mmeta['msg'])
        if not call in mmeta['data']['methods'].keys():
            raise ShipCLIError("Invalid command issued: %s" % sys.argv[1].split('/')[1])
        if 'args' in mmeta['data']['methods'][call]['required_args']:
            print "\nRequired arguments:"
            for k in mmeta['data']['methods'][call]['required_args']['args'].keys():
                print "--%s (-%s): %s" % (k, mmeta['data']['methods'][call]['required_args']['args'][k]['ol'], mmeta['data']['methods'][call]['required_args']['args'][k]['desc'])
        if 'args' in mmeta['data']['methods'][call]['optional_args']:
            print "\nOptional arguments, supply a minimum of %s and a maximum of %s of the following:" % (mmeta['data']['methods'][call]['optional_args']['min'], mmeta['data']['methods'][call]['optional_args']['max'])
            for k in mmeta['data']['methods'][call]['optional_args']['args'].keys():
                print "--%s (-%s): %s" % (k, mmeta['data']['methods'][call]['optional_args']['args'][k]['ol'], mmeta['data']['methods'][call]['optional_args']['args'][k]['desc'])
        print ""
    except Exception, e:
        raise ShipCLIError(e)


# if someone runs: ship <module>/<command> --option1=bleh -o2 foo
def call_command(cfg, module_map):
    try:
        revmodule_map = swap_dict(module_map)
        module, call = sys.argv[1].split('/')
        if revmodule_map[module]:
            buf = "" # our argument buffer for urlencoding
            response = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/'+revmodule_map[module]+'/metadata')
            mmeta = myjson.loads(response.content)
            if mmeta['status'] != 0:
                print "Error occurred:\n%s" % mmeta['msg']
                sys.exit(1)

            # set up our command line options through optparse. will
            # change this to argparse if we upgrade past python 2.7
            parser = OptionParser()
            arglist = {}
            if 'args' in mmeta['data']['methods'][call]['required_args']:
                for k in mmeta['data']['methods'][call]['required_args']['args'].keys():
                    if mmeta['data']['methods'][call]['required_args']['args'][k]['vartype'] != "None":
                        parser.add_option('-'+mmeta['data']['methods'][call]['required_args']['args'][k]['ol'],\
                                          '--'+k, help=mmeta['data']['methods'][call]['required_args']['args'][k]['desc'])
                        arglist[k] = mmeta['data']['methods'][call]['required_args']['args'][k]['vartype']
                    else:
                        parser.add_option('-'+mmeta['data']['methods'][call]['required_args']['args'][k]['ol'],\
                                          '--'+k, help=mmeta['data']['methods'][call]['required_args']['args'][k]['desc'],\
                                          action="store_true")
                        arglist[k] = mmeta['data']['methods'][call]['required_args']['args'][k]['vartype']
            elif 'args' in mmeta['data']['methods'][call]['optional_args']:
                for k in mmeta['data']['methods'][call]['optional_args']['args'].keys():
                    if mmeta['data']['methods'][call]['optional_args']['args'][k]['vartype'] != "None":
                        parser.add_option('-'+mmeta['data']['methods'][call]['optional_args']['args'][k]['ol'],\
                                          '--'+k, help=mmeta['data']['methods'][call]['optional_args']['args'][k]['desc'])
                        arglist[k] = mmeta['data']['methods'][call]['optional_args']['args'][k]['vartype']
                    else:
                        parser.add_option('-'+mmeta['data']['methods'][call]['optional_args']['args'][k]['ol'],\
                                          '--'+k, help=mmeta['data']['methods'][call]['optional_args']['args'][k]['desc'],\
                                          action="store_true")
                        arglist[k] = mmeta['data']['methods'][call]['optional_args']['args'][k]['vartype']
            else:
                raise ShipCLIError("Error: no arguments defined")

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
            if mmeta['data']['methods'][call]['rest_type'] == 'GET':
                callresponse = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/'+revmodule_map[module]+'/'+call+'?'+buf)
            elif mmeta['data']['methods'][call]['rest_type'] == 'POST':
                callresponse = requests.post('http://'+cfg.api_server+':'+cfg.api_port+'/'+revmodule_map[module]+'/'+call+'?'+buf)
            elif mmeta['data']['methods'][call]['rest_type'] == 'DELETE':
                callresponse = requests.delete('http://'+cfg.api_server+':'+cfg.api_port+'/'+revmodule_map[module]+'/'+call+'?'+buf)
            elif mmeta['data']['methods'][call]['rest_type'] == 'PUT':
                callresponse = requests.put('http://'+cfg.api_server+':'+cfg.api_port+'/'+revmodule_map[module]+'/'+call+'?'+buf)
            responsedata = myjson.loads(callresponse.content)
            if responsedata['status'] != 0:
                print "Error occurred:\n%s" % responsedata['msg']
                sys.exit(1)

            # if we get just a unicode string back, it's a status
            # message...print it. otherwise, we got back a dict or list
            # or something similar, fire it off at the template engine
            # if it blows up, dump the error and the response we got
            # from ship_daemon.py
            if isinstance(responsedata['data'], unicode):
                print responsedata['data']
            else:
                try:
                    print_responsedata(responsedata, mmeta)
                except Exception, e:
                    print "Error: %s\n\n" % e
                    print responsedata
        else:
            raise ShipCLIError("Invalid module specified: %s" % sys.argv[1].split('/')[0])
    except Exception, e:
        raise ShipCLIError("Error: %s" % e)


# prints out response data, according to a jinja2 template defined in
# the module
def print_responsedata(responsedata, mmeta):
    """
    prints out response data according to a jinja2 template defined in the module

    this frontend always uses "mothership/<modulename>template.cmdln" for its template file
    """
    module = mmeta['request'].split('/metadata')[0].split('/')[1]
    env = Environment(loader=FileSystemLoader('mothership/'+module))
    try:
        template = env.get_template('template.cmdln')
    except Exception, e:
        raise ShipCLIError("template.cmdln not found for module: %s\nError: %s" % (module, e))
    print template.render(r=responsedata)


# main execution block
if __name__ == "__main__":
    # the global CLI config. useful everywhere
    cfg = ConfigureCli('mothership_cli.yaml')

    # prevent root from running ship
    if sys.stdin.isatty():
        if os.getlogin() == 'root':
            print "Please do not run ship as root"
            raise ShipCLIError("Your effective uid: " + os.geteuid())

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
        # grab a list of loaded modules from the API server
        response = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/modules')
        # decode the response into a dict
        response_dict = myjson.loads(response.content)
        # check the status on our JSON response. 0 == good, anything
        # else == bad. expect error information in the 'msg' payload
        if response_dict['status'] != 0:
            print "Error occurred:\n%s" % response_dict['msg']
            sys.exit(1)
        # if it didn't blow up, populate the module list
        module_list = response_dict['data']
        module_map = {}
        for i in module_list:
            response = requests.get('http://'+cfg.api_server+":"+cfg.api_port+'/'+i+'/metadata')
            response_dict = myjson.loads(response.content)
            module_map[i] = response_dict['data']['config']['shortname']
        # a reverse module map, useful in constructing our cmdln
        revmodule_map = swap_dict(module_map)

        # command line-y stuff. the order of the if statements is very
        # important. please be careful if you have to move things
        #
        # user ran: ship
        if len(sys.argv) < 2:
            if cfg.debug:
                print "print_submodules called()"
            print_submodules(cfg, module_map)
        # user ran: ship <valid module>
        elif len(sys.argv) == 2 and sys.argv[1] in module_map.values():
            if cfg.debug:
                print "print_commands called()"
            print_commands(cfg, module_map)
        # user ran: ship <valid module>/<valid command>
        elif len(sys.argv) == 2 and sys.argv[1].split('/')[0] in module_map.values():
            if cfg.debug:
                print "print_command_args called()"
            print_command_args(cfg, module_map)
        # user ran: ship <invalid module>/<invalid command>
        elif len(sys.argv) == 2 and sys.argv[1].split('/')[0] not in module_map.values():
            raise ShipCLIError("Requested module does not exist: %s" % "API_"+sys.argv[1].split('/')[0])
        # user ran: ship <invalid module>
        elif len(sys.argv) == 2 and sys.argv[1] not in module_map.values():
            raise ShipCLIError("Requested module does not exist: %s" % "API_"+sys.argv[1])
        # user ran: ship <valid module>/<valid command> --valid=args -a
        elif len(sys.argv) >= 3:
            if cfg.debug:
                print "call_command called()"
            call_command(cfg, module_map)
        # user ran some real ugly crap.
        else:
            raise ShipCLIError("bad command line:\n%s" % " ".join(sys.argv))

    except IOError, e:
        print "Missing config file: mothership_cli.yaml"
        print "ERROR: %s" % e
        sys.exit(1)
    except Exception, e:
        print "Error in __main__: %s" % e
