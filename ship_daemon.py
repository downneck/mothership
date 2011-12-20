#!/usr/bin/python26

# imports
from bottle import Bottle, run
from mothership import configure
import os
import sys

# for >=2.6 use json, >2.6 use simplejson
try:
    import json as myjson
except ImportError:
    import simplejson as myjson

# bottle crap
import bottle
bottle.debug(True)



# start doin stuff
httpship = Bottle()
cfg = configure.Configure('/etc/mothership.yaml')

module_metadata = {}
basepath = sys.path[0]
try:
    for i in os.walk(basepath+'/mothership/').next()[1]:
        if i == 'serverinfo':
            print "mothership."+i
            mod = __import__("mothership."+i)
            foo = getattr(mod, i)
            bar = getattr(foo, i)
            inst = bar(cfg)
            module_metadata[i] = inst
except ImportError, e:
    print "problem importing "+i
    print "error: "+e

@httpship.route('/')
def index():
    return "<P>Callable paths:<BR>"+"<BR>".join(module_metadata.keys())

@httpship.route("/<path>")
def top_path(path):
    return path
    #print module_metadata[path].metadata


# the daemon
run(httpship, host='0.0.0.0', port=8081, reloader=True)
