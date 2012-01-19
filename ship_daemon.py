#!/usr/bin/python26
import os
import sys

import bottle
from bottle import response

from mothership import configure
from mothership.API_common import *

# for >=2.6 use json, >2.6 use simplejson
try:
    import json as myjson
except ImportError:
    import simplejson as myjson

#### cfg.debugGING ####
bottle.debug(True)

# instantiate a bottle
httpship = bottle.Bottle()

# suck in our configure object
cfg = configure.Configure('mothership.yaml')
cm = MothershipCommon('ship_daemon.log')

# generic mothership exception type
class ShipDaemonError(Exception):
    pass

# scans our main path for modules, loads valid modules
@httpship.route('/loadmodules')
def load_modules():
    """
    scans our main path for modules, loads valid modules
    """
    if cfg.debug:
        cm.debug("loadmodules() called directly")
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
                cm.debug("importing mothership.%s:" % i)
                if i in old_metadata.keys():
                    try:
                        cm.debug("unloading module: %s" % sys.modules['mothership.'+i])
                        del sys.modules['mothership.'+i]
                    except:
                        pass
                    cm.debug("module unloaded: mothership."+i)
                mod = __import__("mothership."+i)
                cm.debug("import complete")
                foo = getattr(mod, i)
                cm.debug(foo)
                bar = getattr(foo, i)
                if cfg.debug:
                    print bar
                inst = bar(cfg)
                if cfg.debug:
                    print inst
                cfg.module_metadata[i] = inst
            except Exception, e:
                if cfg.debug:
                    print "import error: %s" % e
    except ImportError, e:
        print "problem importing "+i
        print "error: "+e


# run our module loader once at startup
load_modules()


# main url, currently spits back info about loaded modules and such
# will probably change quite a lot before the rewrite gets going
# more than likely will merge with /modules route below
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
    buf += "<BR><BR>to get JSON list of loaded modules call:<BR><A HREF=\"/modules\">/modules</A><BR>"
    return buf


# returns a list of currently loaded modules
@httpship.route('/modules')
def loaded_modules():
    buf = []
    for k in cfg.module_metadata.keys():
        if cfg.debug:
            print 'route: /'
            print 'metadata key: '+k
        try:
            buf.append(cfg.module_metadata[k].namespace)
            if cfg.debug:
                print buf
        except:
            continue
    response.content_type = 'application/json'
    return myjson.JSONEncoder().encode(buf)


# returns data about a namespace's public functions
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


# returns data about a function call or calls the function.
# will probably change significantly before the rewrite
@httpship.route("/:pname/:callpath", method=('GET', 'POST', 'PUT', 'DELETE'))
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
            return buf
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
        try:
            buf += "<BR><BR>return:<BR>%s" % myjson.JSONEncoder(indent=4).encode(cfg.module_metadata[pname].metadata['methods'][callpath]['return'])
        except:
            buf += "<BR><BR>return:<BR>ERROR: improperly formed return metadata"
        if cfg.debug:
            print buf
        return buf
    # we got an actual callpath! do stuff.
    else:
        response.content_type='application/json'
        if cfg.debug:
            #print "method called: %s" % myjson.JSONEncoder(indent=4).encode(cfg.module_metadata[pname].metadata['methods'][callpath])
            if bottle.request.method == cfg.module_metadata[pname].metadata['methods'][callpath]['rest_type']:
                buf = getattr(cfg.module_metadata[pname], callpath)
                returnme = buf(query)
                print myjson.JSONEncoder(indent=4).encode(returnme)
                return myjson.JSONEncoder().encode(returnme)
            else:
                raise ShipDaemonError("request method \"%s\" does not match allowed type \"%s\" for call \"/%s/%s\"" % (bottle.request.method, cfg.module_metadata[pname].metadata['methods'][callpath]['rest_type'], pname, callpath))
        else:
            if bottle.request.method == cfg.module_metadata[pname].metadata['methods'][callpath]['rest_type']:
                buf = getattr(cfg.module_metadata[pname], callpath)
                returnme = buf(query)
                return myjson.JSONEncoder().encode(returnme)
            else:
                raise ShipDaemonError("request method \"%s\" does not match allowed type \"%s\" for call \"/%s/%s\"" % (bottle.request.method, cfg.module_metadata[pname].metadata['methods'][callpath]['rest_type'], pname, callpath))

# the daemon
bottle.run(httpship, host='0.0.0.0', port=8081, reloader=False)
