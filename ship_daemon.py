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


# scans our main path for modules, loads valid modules
@httpship.route('/loadmodules')
def load_modules():
    """
    scans our main path for modules, loads valid modules
    """
    if cfg.debug:
            print "loadmodules() called directly"
    # clear module metadata
    old_metadata = cfg.module_metadata
    cfg.module_metadata = {}
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
                if i in old_metadata.keys():
                    try:
                        del sys.modules['mothership.'+i]
                    except:
                        pass
                    if cfg.debug:
                        print "module unloaded: mothership."+i
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
                cfg.module_metadata[i] = inst
            except:
                pass
    except ImportError, e:
        print "problem importing "+i
        print "error: "+e


# run our module loader once at startup
load_modules()


@httpship.route('/')
def index():
    buf = "<P>loaded modules:<BR><BR>"
    for k in cfg.module_metadata.keys():
        if cfg.debug:
            print 'route: /'
            print 'metadata key: '+k
        try:
            buf += "<A HREF=\"/%s\">/%s</A><BR>" % (cfg.module_metadata[k].namespace, cfg.module_metadata[k].namespace)
            if cfg.debug:
                print buf
        except:
            continue
    buf += "<BR><BR>to reload modules call:<BR><A HREF=\"/loadmodules\">/loadmodules</A><BR>"
    return buf


@httpship.route("/:pname")
def namespace_path(pname):
    buf = "Callable functions:<BR><BR>"
    buf += "<A HREF=\"/%s/metadata\">/%s/metadata</A><BR>" % (pname, pname)
    if cfg.debug:
        print "buf: "+buf
        print "pname: "+pname
        print "cfg.module_metadata[pname]: "
        print cfg.module_metadata[pname].metadata
    for meth in cfg.module_metadata[pname].metadata['methods']:
        if cfg.debug:
            print meth
        buf += "<A HREF=\"/%s/%s\">/%s/%s</A><BR>" % (pname, meth, pname, meth)
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
            print myjson.JSONEncoder(indent=4).encode(cfg.module_metadata[pname].metadata)
            buf = myjson.JSONEncoder().encode(cfg.module_metadata[pname].metadata)
            return buf
        else:
            buf = myjson.JSONEncoder().encode(cfg.module_metadata[pname].metadata)
            return buf
    # everyone wants query strings, blow up and spit out information if
    # we don't get any query strings
    elif not query:
        buf = "Here are the possible query strings for \"/%s/%s\"<BR><BR>required_args:<BR>" % (pname, callpath)
        try:
            for req in cfg.module_metadata[pname].metadata['methods'][callpath]['required_args']['args'].keys():
                if cfg.debug:
                    print "required arg: %s" % req
                buf += "%s (%s): %s<BR>" % (req, cfg.module_metadata[pname].metadata['methods'][callpath]['required_args']['args'][req]['vartype'], cfg.module_metadata[pname].metadata['methods'][callpath]['required_args']['args'][req]['desc'])
        except:
            buf += "No required_args found<BR>"
        try:
            buf += "<BR><BR>optional_args, please supply at least %s but not more than %s of the following:<BR>" % (cfg.module_metadata[pname].metadata['methods'][callpath]['optional_args']['min'], cfg.module_metadata[pname].metadata['methods'][callpath]['optional_args']['max'])
            for opt in cfg.module_metadata[pname].metadata['methods'][callpath]['optional_args']['args'].keys():
                if cfg.debug:
                    print "optional arg: %s" % opt
                if cfg.module_metadata[pname].metadata['methods'][callpath]['optional_args']['args'][opt]['vartype'] == "None":
                    buf += "<A HREF=\"/%s/%s?%s\">/%s/%s?%s</A> (%s): %s<BR>" % (pname, callpath, opt, pname, callpath, opt, cfg.module_metadata[pname].metadata['methods'][callpath]['optional_args']['args'][opt]['vartype'], cfg.module_metadata[pname].metadata['methods'][callpath]['optional_args']['args'][opt]['desc'])
                else:
                    buf += "/%s/%s?%s (%s): %s<BR>" % (pname, callpath, opt, cfg.module_metadata[pname].metadata['methods'][callpath]['optional_args']['args'][opt]['vartype'], cfg.module_metadata[pname].metadata['methods'][callpath]['optional_args']['args'][opt]['desc'])
        except:
            buf += "<BR><BR>optional_args:<BR>No optional_args found<BR>"
        if cfg.debug:
            print buf
        return buf
    # we got an actual callpath! do stuff.
    else:
        if cfg.debug:
            print "method called: %s" % myjson.JSONEncoder(indent=4).encode(cfg.module_metadata[pname].metadata['methods'][callpath]['call'])
            buf = getattr(cfg.module_metadata[pname], cfg.module_metadata[pname].metadata['methods'][callpath]['call'])
            print myjson.JSONEncoder(indent=4).encode(buf(query))
            return myjson.JSONEncoder().encode(buf(query))
        else:
            buf = getattr(cfg.module_metadata[pname], cfg.module_metadata[pname].metadata['methods'][callpath]['call'])
            return myjson.JSONEncoder().encode(buf(query))


@httpship.route("/favicon.ico")
def favicon():
    return bottle.static_file('favicon.ico', root=sys.path[0])


@httpship.route("/test")
def test():
    pass


# the daemon
bottle.run(httpship, host='0.0.0.0', port=8081, reloader=False)
