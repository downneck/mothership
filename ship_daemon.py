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

#### cfg.debugGING ####
# uncomment to debug bottle
bottle.debug(True)


# instantiate a bottle
httpship = bottle.Bottle()
# suck in our configure object
cfg = configure.Configure('mothership.yaml')
# set our debugging flag
cfg.debug = cfg.debug
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
            if cfg.debug:
                print "\nimporting mothership.%s:" % i
            mod = __import__("mothership."+i)
            if cfg.debug:
                print "import complete"
            foo = getattr(mod, i)
            if cfg.debug:
                print foo
            bar = getattr(foo, i)
            if cfg.debug:
                print bar
            inst = bar(cfg)
            if cfg.debug:
                print inst
            module_metadata[i] = inst
        except:
            if cfg.debug:
                print "module \"%s\" does not have a valid main class" % i
            else:
                pass
except ImportError, e:
    print "problem importing "+i
    print "error: "+e

@httpship.route('/')
def index():
    buf = "<P>loaded modules:<BR><BR>"
    for k in module_metadata.keys():
        if cfg.debug:
            print 'route: /'
            print 'metadata key: '+k
        try:
            buf += "/"+module_metadata[k].namespace+"<BR>"
            if cfg.debug:
                print buf
        except:
            continue
    return buf

@httpship.route("/:pname")
def namespace_path(pname):
    buf = "Callable functions:<BR><BR>"
    buf += "/"+pname+"/metadata<BR>"
    if cfg.debug:
        print "buf: "+buf
        print "pname: "+pname
        print "module_metadata[pname]: "
        print module_metadata[pname].metadata
    for meth in module_metadata[pname].metadata['methods']:
        if cfg.debug:
            print meth
        buf += "/%s/%s<BR>" % (pname, meth)
    return buf

@httpship.route("/:pname/:callpath")
def callable_path(pname, callpath):
    query = bottle.request.GET
    if cfg.debug:
        print "query keys: %s" % query.keys()
    # everyone has a 'metadata' construct
    # hard wire it into callpath options
    if callpath == 'metadata':
        if cfg.debug:
            print myjson.JSONEncoder(indent=4).encode(module_metadata[pname].metadata)
            buf = myjson.JSONEncoder().encode(module_metadata[pname].metadata)
            return buf
        else:
            buf = myjson.JSONEncoder().encode(module_metadata[pname].metadata)
            return buf
    # everyone wants query strings, blow up and spit out information if
    # we don't get any query strings
    elif not query:
        buf = "Here are the possible query strings for \"/%s/%s\"<BR><BR>required_args:<BR>" % (pname, callpath)
        try:
            for req in module_metadata[pname].metadata['methods'][callpath]['required_args']['args'].keys():
                if cfg.debug:
                    print "required arg: %s" % req
                buf += "%s (%s): %s<BR>" % (req, module_metadata[pname].metadata['methods'][callpath]['required_args']['args'][req]['vartype'], module_metadata[pname].metadata['methods'][callpath]['required_args']['args'][req]['desc'])
        except:
            buf += "No required_args found<BR>"
        buf += "<BR><BR>optional_args, please supply at least %s but not more than %s of the following:<BR>" % (module_metadata[pname].metadata['methods'][callpath]['optional_args']['min'], module_metadata[pname].metadata['methods'][callpath]['optional_args']['max'])
        try:
            for opt in module_metadata[pname].metadata['methods'][callpath]['optional_args']['args'].keys():
                if cfg.debug:
                    print "optional arg: %s" % opt
                buf += "%s (%s): %s<BR>" % (opt, module_metadata[pname].metadata['methods'][callpath]['optional_args']['args'][opt]['vartype'], module_metadata[pname].metadata['methods'][callpath]['optional_args']['args'][opt]['desc'])
        except:
            buf += "No optional_args found<BR>"
        if cfg.debug:
            print buf
        return buf
    # we got an actual callpath! do stuff.
    else:
        if cfg.debug:
            print "method called: %s" % myjson.JSONEncoder(indent=4).encode(module_metadata[pname].metadata['methods'][callpath]['call'])
            buf = getattr(module_metadata[pname], module_metadata[pname].metadata['methods'][callpath]['call'])
            print myjson.JSONEncoder(indent=4).encode(buf(query))
            return myjson.JSONEncoder().encode(buf(query))
        else:
            buf = getattr(module_metadata[pname], module_metadata[pname].metadata['methods'][callpath]['call'])
            return myjson.JSONEncoder().encode(buf(query))

@httpship.route("/test")
def test():
    query = {}
    query = bottle.request.GET
    if cfg.debug:
        print "num query strings: %s" % len(query)
    if query:
        for k in query.keys():
            print "key: %s, value: %s" % (k, query[k])
    else:
        buf = "Here are the possible query strings for module \"%s\"<BR><BR>required_args:<BR>" % 'list_servers'
        try:
            for req in module_metadata['list_servers'].metadata['methods']['lss']['required_args']['args'].keys():
                if cfg.debug:
                    print "required arg: %s" % req
                buf += "%s (%s): %s<BR>" % (req, module_metadata['list_servers'].metadata['methods']['lss']['required_args']['args'][req]['vartype'], module_metadata['list_servers'].metadata['methods']['lss']['required_args']['args'][req]['desc'])
        except:
            buf += "No required_args found<BR>"
        buf += "<BR><BR>optional_args:<BR>"
        try:
            for opt in module_metadata['list_servers'].metadata['methods']['lss']['optional_args']['args'].keys():
                if cfg.debug:
                    print "optional arg: %s" % opt
                buf += "%s (%s): %s<BR>" % (opt, module_metadata['list_servers'].metadata['methods']['lss']['optional_args']['args'][opt]['vartype'], module_metadata['list_servers'].metadata['methods']['lss']['optional_args']['args'][opt]['desc'])
        except:
            buf += "No optional_args found<BR>"
        if cfg.debug:
            print buf
        return buf


# the daemon
bottle.run(httpship, host='0.0.0.0', port=8081, reloader=False)
