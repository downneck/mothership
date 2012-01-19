#!/usr/bin/python26

# system imports
import os
import sys
import datetime
import bottle
from bottle import static_file
from bottle import response
from socket import gethostname

# mothership imports
from mothership import configure
from mothership.common import MothershipCommon

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
cm = MothershipCommon('ship_daemon.log', to_file=False)

# generic mothership exception type
class ShipDaemonError(Exception):
    pass

# create a json-able dict of important info
def __generate_json_header():
    jbuf = {}
    jbuf['status'] = 0
    jbuf['timestamp'] = str(datetime.datetime.now())
    jbuf['nodename'] = gethostname()
    return jbuf


@httpship.route('/loadmodules')
def load_modules():
    """
    scans our main path for modules, loads valid modules
    """
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


@httpship.route('/')
def index():
    """
    main url, currently spits back info about loaded modules and such
    will probably change quite a lot before the rewrite gets going
    more than likely will merge with /modules route below
    """
    response.content_type='application/json'
    jbuf = __generate_json_header()
    jbuf['request'] = '/'
    jbuf['data'] = "loaded modules: "
    for k in cfg.module_metadata.keys():
        cm.debug('route: /')
        cm.debug('metadata key: '+k)
        try:
            jbuf['data'] += " %s" % cfg.module_metadata[k].namespace
        except:
            continue
    jbuf['data'] += ". for more info on a module, call /<modulename>"
    jbuf['data'] += ". to reload modules call: /loadmodules"
    jbuf['data'] += ". to get JSON list of loaded modules call: /modules"
    return myjson.JSONEncoder().encode(jbuf)


@httpship.route('/modules')
def loaded_modules():
    """
    returns a list of currently loaded modules
    """
    response.content_type='application/json'
    jbuf = __generate_json_header()
    jbuf['request'] = '/modules'
    jbuf['data'] = []
    for k in cfg.module_metadata.keys():
        cm.debug('route: /')
        cm.debug('metadata key: '+k)
        try:
            jbuf['data'].append(cfg.module_metadata[k].namespace)
            cm.debug(jbuf)
        except:
            continue
    response.content_type = 'application/json'
    return myjson.JSONEncoder().encode(jbuf)

@httpship.route("/:pname")
def namespace_path(pname):
    """
    returns data about a namespace's public functions
    """
    response.content_type='application/json'
    jbuf = __generate_json_header()
    jbuf['request'] = "/%s" % pname
    jbuf['data'] = {}
    jbuf['data']['callable_functions'] = []
    cm.debug("jbuf: %s" % jbuf)
    cm.debug("pname: %s" %pname)
    cm.debug("cfg.module_metadata[pname]: %s " %cfg.module_metadata[pname].metadata)
    for meth in cfg.module_metadata[pname].metadata['methods']:
        cm.debug(meth)
        jbuf['data']['callable_functions'].append("/%s" % meth)
    return myjson.JSONEncoder().encode(jbuf)

@httpship.route("/:pname/:callpath", method=('GET', 'POST', 'PUT', 'DELETE'))
def callable_path(pname, callpath):
    """
    returns data about a function call or calls the function.
    will probably change significantly before the rewrite
    """
    response.content_type='application/json'
    jbuf = __generate_json_header()
    jbuf['request'] = "/%s/%s" % (pname, callpath)
    query = bottle.request.GET
    pnameMetadata = cfg.module_metadata[pname]

    cm.debug("query keys: %s" % query.keys())
    # everyone has a 'metadata' construct
    # hard wire it into callpath options
    if callpath == 'metadata':
        cm.debug(myjson.JSONEncoder(indent=4).encode(pnameMetadata.metadata))
        jbuf['data'] = pnameMetadata.metadata
        return myjson.JSONEncoder().encode(jbuf)
    else:
        pnameCallpath = pnameMetadata.metadata['methods'][callpath]

    # we got an actual callpath! do stuff.
    if query:
        cm.debug("method called: %s" % myjson.JSONEncoder(indent=4).encode(cfg.module_metadata[pname].metadata['methods'][callpath]))
        if bottle.request.method == pnameCallpath['rest_type']:
            buf = getattr(pnameMetadata, callpath)
            jbuf['data'] = buf(query)
            cm.debug(myjson.JSONEncoder(indent=4).encode(jbuf))
            return myjson.JSONEncoder().encode(jbuf)
        else:
            raise ShipDaemonError("request method \"%s\" does not match allowed type \"%s\" for call \"/%s/%s\"" % (bottle.request.method, pnameCallpath['rest_type'], pname, callpath))
    # everyone wants query strings, blow up and spit out information if
    # we don't get any query strings
    else:
        jbuf['data'] = {}
        jbuf['data']['available_query_strings'] = {}
        try:
            for req in pnameMetadata.metadata['methods'][callpath]['required_args']['args'].keys():
                cm.debug("required arg: %s" % req)
            jbuf['data']['available_query_strings']['required_args'] = pnameCallpath['required_args']
        except:
            pass
        try:
            jbuf['data']['available_query_strings']['optional_args'] = pnameCallpath['optional_args']
            for opt in pnameCallpath['optional_args']['args'].keys():
                cm.debug("optional arg: %s" % opt)
        except:
            pass
        return myjson.JSONEncoder(indent=4).encode(jbuf)
        cm.debug(jbuf)

@httpship.route('/favicon.ico')
def get_favicon():
    return static_file('favicon.ico', root='static/')

# run our module loader once at startup
load_modules()
# the daemon
bottle.run(httpship, host='0.0.0.0', port=8081, reloader=False)
