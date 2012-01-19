#!/usr/bin/python26
import os
import sys

import bottle
from bottle import static_file
from bottle import response

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
    buf = "<P>loaded modules:<BR><BR>"
    for k in cfg.module_metadata.keys():
        cm.debug('route: /')
        cm.debug('metadata key: '+k)
        try:
            buf += "<A HREF=\"/%s\">/%s</A><BR>" % (cfg.module_metadata[k].namespace, cfg.module_metadata[k].namespace)
            cm.debug(buf)
        except:
            continue
    buf += "<BR><BR>to reload modules call:<BR><A HREF=\"/loadmodules\">/loadmodules</A><BR>"
    buf += "<BR><BR>to get JSON list of loaded modules call:<BR><A HREF=\"/modules\">/modules</A><BR>"
    return buf


@httpship.route('/modules')
def loaded_modules():
    """
    returns a list of currently loaded modules
    """
    buf = []
    for k in cfg.module_metadata.keys():
        cm.debug('route: /')
        cm.debug('metadata key: '+k)
        try:
            buf.append(cfg.module_metadata[k].namespace)
            cm.debug(buf)
        except:
            continue
    response.content_type = 'application/json'
    return myjson.JSONEncoder().encode(buf)

@httpship.route("/:pname")
def namespace_path(pname):
    """
    returns data about a namespace's public functions
    """
    buf = "Callable functions:<BR><BR>"
    buf += "<A HREF=\"/%s/metadata\">/%s/metadata</A><BR>" % (pname, pname)
    cm.debug("buf: %s" % buf)
    cm.debug("pname: %s" %pname)
    cm.debug("cfg.module_metadata[pname]: %s " %cfg.module_metadata[pname].metadata)
    for meth in cfg.module_metadata[pname].metadata['methods']:
        cm.debug(meth)
        buf += "<A HREF=\"/%s/%s\">/%s/%s</A><BR>" % (pname, meth, pname, meth)
    return buf

@httpship.route("/:pname/:callpath", method=('GET', 'POST', 'PUT', 'DELETE'))
def callable_path(pname, callpath):
    """
    returns data about a function call or calls the function.
    will probably change significantly before the rewrite
    """
    query = bottle.request.GET
    pnameMetadata = cfg.module_metadata[pname]
        
    cm.debug("query keys: %s" % query.keys())
    # everyone has a 'metadata' construct
    # hard wire it into callpath options
    if callpath == 'metadata':
        cm.debug(myjson.JSONEncoder(indent=4).encode(pnameMetadata.metadata))
        buf = myjson.JSONEncoder().encode(pnameMetadata.metadata)
        response.content_type='application/json'
        return buf
    else:
        pnameCallpath = pnameMetadata.metadata['methods'][callpath]

    # we got an actual callpath! do stuff.
    if query:
        cm.debug("method called: %s" % myjson.JSONEncoder(indent=4).encode(cfg.module_metadata[pname].metadata['methods'][callpath]))
        if bottle.request.method == pnameCallpath['rest_type']:
            buf = getattr(pnameMetadata, callpath)
            returnme = buf(query)
            cm.debug(myjson.JSONEncoder(indent=4).encode(returnme))
            response.content_type='application/json'
            return myjson.JSONEncoder().encode(returnme)
        else:
            raise ShipDaemonError("request method \"%s\" does not match allowed type \"%s\" for call \"/%s/%s\"" % (bottle.request.method, pnameCallpath['rest_type'], pname, callpath))
    # everyone wants query strings, blow up and spit out information if
    # we don't get any query strings
    else:
        buf = "Here are the possible query strings for \"/%s/%s\"<BR><BR>required_args:<BR>" % (pname, callpath)
        try:
            for req in pnameMetadata.metadata['methods'][callpath]['required_args']['args'].keys():
                cm.debug("required arg: %s" % req)
                buf += "%s (%s): %s<BR>" % (req, pnameCallpath['required_args']['args'][req]['vartype'], pnameCallpath['required_args']['args'][req]['desc'])
        except:
            buf += "No required_args found<BR>"
        try:
            buf += "<BR><BR>optional_args, please supply at least %s but not more than %s of the following:<BR>" % (pnameCallpath['optional_args']['min'], pnameCallpath['optional_args']['max'])
            for opt in pnameCallpath['optional_args']['args'].keys():
                cm.debug("optional arg: %s" % opt)
                if pnameCallpath['optional_args']['args'][opt]['vartype'] == "None":
                    buf += "<A HREF=\"/%s/%s?%s\">/%s/%s?%s</A> (%s): %s<BR>" % (pname, callpath, opt, pname, callpath, opt, pnameCallpath['optional_args']['args'][opt]['vartype'], pnameCallpath['optional_args']['args'][opt]['desc'])
                else:
                    buf += "/%s/%s?%s (%s): %s<BR>" % (pname, callpath, opt, pnameCallpath['optional_args']['args'][opt]['vartype'], pnameCallpath['optional_args']['args'][opt]['desc'])
        except:
            buf += "<BR><BR>optional_args:<BR>No optional_args found<BR>"
        try:
            buf += "<BR><BR>return:<BR>%s" % myjson.JSONEncoder(indent=4).encode(pnameCallpath['return'])
        except:
            buf += "<BR><BR>return:<BR>ERROR: improperly formed return metadata"
        cm.debug(buf)
        return buf

@httpship.route('/favicon.ico')
def get_favicon():
    return static_file('favicon.ico', root='static/')

# run our module loader once at startup
load_modules()
# the daemon
bottle.run(httpship, host='0.0.0.0', port=8081, reloader=False)
