#!/usr/bin/python26

# imports
from mothership import configure
import os
import sys
import bottle

# for >=2.6 use json, >2.6 use simplejson
try:
    import json as myjson
except ImportError:
    import simplejson as myjson

#### DEBUGGING ####
# uncomment to debug bottle
bottle.debug(True)
# set to True to debug ship-daemon.py
#DEBUG=True
DEBUG=False


# instantiate a bottle
httpship = bottle.Bottle()
# suck in our configure object
cfg = configure.Configure('mothership.yaml')
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
            if DEBUG:
                print "\nimporting mothership.%s:" % i
            mod = __import__("mothership."+i)
            if DEBUG:
                print "import complete"
            foo = getattr(mod, i)
            if DEBUG:
                print foo
            bar = getattr(foo, i)
            if DEBUG:
                print bar
            inst = bar(cfg)
            if DEBUG:
                print inst
            module_metadata[i] = inst
        except:
            if DEBUG:
                print "module \"%s\" does not have a valid main class" % i
            else:
                pass
except ImportError, e:
    print "problem importing "+i
    print "error: "+e

@httpship.route('/')
def index():
    buf = "<P>namespaces:<BR><BR>"
    for k in module_metadata.keys():
        if DEBUG:
            print 'route: /'
            print 'metadata key: '+k
        try:
            buf += "/"+module_metadata[k].namespace+"<BR>"
            if DEBUG:
                print buf
        except:
            continue
    return buf

@httpship.route("/:pname")
def namespace_path(pname):
    buf = "Callable paths:<BR><BR>"
    buf += "/"+pname+"/metadata<BR>"
    if DEBUG:
        print "buf: "+buf
        print "pname: "+pname
        print "module_metadata[pname]: "
        print module_metadata[pname].metadata
    for meth in module_metadata[pname].metadata['methods']:
        if DEBUG:
            print meth
        buf += "/%s/%s<BR>" % (pname, meth)
    return buf

@httpship.route("/:pname/:callpath")
def callable_path(pname, callpath):
    query = bottle.request.GET
    if DEBUG:
        print "query keys: %s" % query.keys()
    if callpath == 'metadata':
        if DEBUG:
            print myjson.JSONEncoder(indent=4).encode(module_metadata[pname].metadata)
            buf = myjson.JSONEncoder().encode(module_metadata[pname].metadata)
            return buf
        else:
            buf = myjson.JSONEncoder().encode(module_metadata[pname].metadata)
            return buf
    else:
        if DEBUG:
            print "method called: %s" % myjson.JSONEncoder(indent=4).encode(module_metadata[pname].metadata['methods'][callpath]['call'])
            buf = getattr(module_metadata[pname], module_metadata[pname].metadata['methods'][callpath]['call'])
            print myjson.JSONEncoder(indent=4).encode(buf(query, DEBUG))
            return myjson.JSONEncoder().encode(buf(query, DEBUG))
        else:
            buf = getattr(module_metadata[pname], module_metadata[pname].metadata['methods'][callpath]['call'])
            return myjson.JSONEncoder().encode(buf(query, DEBUG))

@httpship.route("/test")
def test():
    query = {}
    query = bottle.request.GET
    print "num query strings: %s" % len(query)
    if query:
        for k in query.keys():
            print "key: %s, value: %s" % (k, query[k])
    else:
        print "no query string"

# the daemon
bottle.run(httpship, host='0.0.0.0', port=8081, reloader=False)
