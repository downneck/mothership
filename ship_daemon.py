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

import bottle
# uncomment to debug
bottle.debug(True)



# instantiate a bottle
httpship = Bottle()
# suck in our configure object
cfg = configure.Configure('/etc/mothership.yaml')
# dict to hold our modules' metadata
module_metadata = {}
# base path we're being called from, to find our modules
basepath = sys.path[0]
try:
    # get a list of all subdirectories under mothership
    for i in os.walk(basepath+'/mothership/').next()[1]:
        try:
            # import each module in the list above, grab the metadata
            # from it's main class
            mod = __import__("mothership."+i)
            foo = getattr(mod, i)
            bar = getattr(foo, i)
            inst = bar(cfg)
            module_metadata[i] = inst
        except:
            print "module \"%s\" does not have a valid main class" % i
except ImportError, e:
    print "problem importing "+i
    print "error: "+e

@httpship.route('/')
def index():
    return "<P>Callable paths:<BR>"+"<BR>".join(module_metadata.keys())

@httpship.route("/:pname")
def top_path(pname):
    return module_metadata[pname].metadata


# the daemon
run(httpship, host='0.0.0.0', port=8081, reloader=True)