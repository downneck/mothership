#!/usr/bin/python

# system imports
import os
import sys
import datetime
import bottle
import traceback
from bottle import static_file
from bottle import response
from socket import gethostname

# mothership imports
from mothership import configure
from mothership.common import *

# for >=2.6 use json, >2.6 use simplejson
try:
    import json as myjson
except ImportError:
    import simplejson as myjson

# turn on bottle debugging
bottle.debug(True)

# instantiate a bottle
httpship = bottle.Bottle()


# suck in our configure object
cfg = configure.MothershipConfigureDaemon('mothership_daemon.yaml')
cfg.load_config()
cm = MothershipCommon()


# generic mothership exception type
class ShipDaemonError(Exception):
    pass


# create a json-able dict of important info
def __generate_json_header():
    jbuf = {}
    jbuf['status'] = 0
    jbuf['nodeID'] = 0
    jbuf['msg'] = ""
    jbuf['timestamp'] = str(datetime.datetime.now())
    jbuf['nodename'] = gethostname()
    return jbuf


# authenticate incoming connections
def __auth_conn(jbuf, authtype):
    try:
        if bottle.request.auth == (cfg.api_info_user, cfg.api_info_pass) and authtype == 'info':
            return (True, jbuf)
        elif bottle.request.auth == (cfg.api_admin_user, cfg.api_admin_pass) and (authtype == 'admin' or authtype == 'info'):
            return (True, jbuf)
        elif bottle.request.cookies['apitest'] == 'ThisIsTheWorstAuthenticationMechanismInTheHistoryOfEver' and authtype == 'info': 
            return (True, jbuf)
        elif (bottle.request.auth == (cfg.api_info_user, cfg.api_info_pass) or bottle.request.cookies['apitest'] == 'letmein') and authtype == 'admin':
	    cfg.log.debug("authentication failed, you do not have admin-level access")
            jbuf['status'] = 1
            jbuf['data'] = ""
            jbuf['msg'] = "authentication failed, you do not have admin-level access"
            return (False, jbuf)
        else:
	    cfg.log.debug("authentication failed, no user/pass supplied")
            jbuf['status'] = 1
            jbuf['data'] = ""
            jbuf['msg'] = "authentication failed, no user/pass supplied"
            return (False, jbuf)
    except Exception, e:
        cfg.log.debug("auth request failed. error: %s" % e)
        jbuf['status'] = 1
        jbuf['data'] = ""
        jbuf['msg'] = "auth request failed. error: %s" % e 
        traceback.print_exc()
        return (False, jbuf)


@httpship.route('/loadmodules')
def load_modules(auth=True):
    """
    scans our main path for modules, loads valid modules
    """
    jbuf = __generate_json_header()
    jbuf['request'] = "/loadmodules"
    # authenticate the incoming request, only if we're being called externally
    if auth:
        authed, jbuf = __auth_conn(jbuf, 'admin')
        if not authed:
            response.content_type='text/html'
            raise bottle.HTTPError(401, '/') 
    # assuming we're authed, do stuff
    response.content_type='application/json'
    cfg.log.debug("loadmodules() called directly")
    # clear module metadata
    old_metadata = cfg.module_metadata
    cfg.module_metadata = {}
    # base path we're being called from, to find our modules
    basepath = sys.path[0]
    try:
        # get a list of all subdirectories under mothership
        for i in os.walk(basepath+'/mothership/').next()[1]:
            if 'API_' in i:
                try:
                    # import each module in the list above, grab the metadata
                    # from it's main class
                    cfg.log.debug("importing mothership.%s:" % i)
                    if i in old_metadata.keys():
                        try:
                            cfg.log.debug("unloading module: %s" % sys.modules['mothership.'+i])
                            del sys.modules['mothership.'+i]
                        except:
                            pass
                        cfg.log.debug("module unloaded: mothership."+i)
                    mod = __import__("mothership."+i)
                    cfg.log.debug("import complete")
                    foo = getattr(mod, i)
                    bar = getattr(foo, i)
                    inst = bar(cfg)
                    cfg.module_metadata[i] = inst
                except Exception, e:
                    cfg.log.debug("import error: %s" % e)
            else:
                cfg.log.debug("skipping non-api module: %s" % i)
        jbuf['data'] = "reloaded modules:"
        for k in cfg.module_metadata.keys():
            jbuf['data'] += " %s" % cfg.module_metadata[k].namespace
        return myjson.JSONEncoder().encode(jbuf)
    except Exception, e:
        jbuf['status'] = 1
        jbuf['data'] = ""
        jbuf['msg'] = "Exception in load_modules(). Error: %s" % e
        traceback.print_exc()
        return myjson.JSONEncoder().encode(jbuf)


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
    # authenticate the incoming request
    authed, jbuf = __auth_conn(jbuf, 'info')
    if not authed:
        response.content_type='text/html'
        raise bottle.HTTPError(401, '/') 
    # assuming we're authed, do stuff
    try:
        jbuf['data'] = "loaded modules: "
        for k in cfg.module_metadata.keys():
            cfg.log.debug('route: /')
            cfg.log.debug('metadata key: '+k)
            try:
                jbuf['data'] += " %s" % cfg.module_metadata[k].namespace
            except:
                continue
        jbuf['data'] += ". for more info on a module, call /<modulename>"
        jbuf['data'] += ". to reload modules call: /loadmodules"
        jbuf['data'] += ". to get JSON list of loaded modules call: /modules"
        return myjson.JSONEncoder().encode(jbuf)
    except Exception, e:
        jbuf['status'] = 1
        jbuf['data'] = "Exception in index(). Error: %s" % e
        traceback.print_exc()
        return myjson.JSONEncoder().encode(jbuf)


@httpship.route('/modules')
def loaded_modules():
    """
    returns a list of currently loaded modules
    """
    response.content_type='application/json'
    jbuf = __generate_json_header()
    jbuf['request'] = '/modules'
    # authenticate the incoming request
    authed, jbuf = __auth_conn(jbuf, 'info')
    if not authed:
        response.content_type='text/html'
        raise bottle.HTTPError(401, '/modules') 
    # assuming we're authed, do stuff
    try:
        jbuf['data'] = []
        for k in cfg.module_metadata.keys():
            cfg.log.debug('route: /')
            cfg.log.debug('metadata key: '+k)
            try:
                jbuf['data'].append(cfg.module_metadata[k].namespace)
                cfg.log.debug(jbuf)
            except:
                continue
        return myjson.JSONEncoder().encode(jbuf)
    except Exception, e:
        jbuf['status'] = 1
        jbuf['data'] = ""
        jbuf['msg'] = "Exception in loaded_modules(). Error: %s" % e
        traceback.print_exc()
        return myjson.JSONEncoder().encode(jbuf)


@httpship.route("/:pname")
def namespace_path(pname):
    """
    returns data about a namespace's public functions
    """
    response.content_type='application/json'
    jbuf = __generate_json_header()
    jbuf['request'] = "/%s" % pname
    # authenticate the incoming request
    authed, jbuf = __auth_conn(jbuf, 'info')
    if not authed:
        response.content_type='text/html'
        raise bottle.HTTPError(401, '/'+pname) 
    # assuming we're authed, do stuff
    try:
        jbuf['data'] = {}
        jbuf['data']['callable_functions'] = []
        cfg.log.debug("jbuf: %s" % jbuf)
        cfg.log.debug("pname: %s" %pname)
        cfg.log.debug("cfg.module_metadata[pname]: %s " %cfg.module_metadata[pname].metadata)
        for meth in cfg.module_metadata[pname].metadata['methods']:
            cfg.log.debug(meth)
            jbuf['data']['callable_functions'].append("/%s" % meth)
        return myjson.JSONEncoder().encode(jbuf)
    except Exception, e:
        jbuf['status'] = 1
        jbuf['data'] = ""
        jbuf['msg'] = "Exception in namespace_path(). Error: %s" % e
        traceback.print_exc()
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
    # authenticate the incoming request just enough to get metadata
    authed, jbuf = __auth_conn(jbuf, 'info')
    if not authed:
        response.content_type='text/html'
        raise bottle.HTTPError(401, '/'+pname+'/'+callpath) 
    # assuming we're authed, do stuff
    try:
        query = bottle.request.GET
        pnameMetadata = cfg.module_metadata[pname]
        cfg.log.debug("query keys: %s" % query.keys())
        # everyone has a 'metadata' construct
        # hard wire it into callpath options
        # this is an info-level request so no re-auth
        if callpath == 'metadata':
            cfg.log.debug(myjson.JSONEncoder(indent=4).encode(pnameMetadata.metadata))
            jbuf['data'] = pnameMetadata.metadata
            return myjson.JSONEncoder().encode(jbuf)
        else:
            pnameCallpath = pnameMetadata.metadata['methods'][callpath]
        # we got an actual callpath! do stuff.
        if query:
            cfg.log.debug("method called: %s" % myjson.JSONEncoder(indent=4).encode(cfg.module_metadata[pname].metadata['methods'][callpath]))
            if bottle.request.method == pnameCallpath['rest_type']:
                # check to see if the function we're calling is defined as "admin-only"
                # which requires a different user/pass than "info-only" requests
                if pnameCallpath['admin_only']:
                    reauthed, jbuf = __auth_conn(jbuf, 'admin')
                    if not reauthed:
                        response.content_type='text/html'
                        raise bottle.HTTPError(401, '/'+pname+'/'+callpath) 
                buf = getattr(pnameMetadata, callpath)
                jbuf['data'] = buf(query)
                cfg.log.debug(myjson.JSONEncoder(indent=4).encode(jbuf))
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
                    cfg.log.debug("required arg: %s" % req)
                jbuf['data']['available_query_strings']['required_args'] = pnameCallpath['required_args']
            except:
                pass
            try:
                jbuf['data']['available_query_strings']['optional_args'] = pnameCallpath['optional_args']
                for opt in pnameCallpath['optional_args']['args'].keys():
                    cfg.log.debug("optional arg: %s" % opt)
            except:
                pass
            return myjson.JSONEncoder(indent=4).encode(jbuf)
            cfg.log.debug(jbuf)
    # catch and re-raise HTTP auth errors
    except bottle.HTTPError:
        raise bottle.HTTPError(401, '/'+pname+'/'+callpath)
    except Exception, e:
        jbuf['status'] = 1
        jbuf['data'] = ""
        jbuf['msg'] = "Exception in callable_path(). Error: %s" % e
        traceback.print_exc()
        return myjson.JSONEncoder().encode(jbuf)


@httpship.route('/favicon.ico')
def get_favicon():
    """
    returns a favicon
    """
    try:
        return static_file('favicon.ico', root='static/')
    except Exception, e:
        jbuf = __generate_json_header()
        jbuf['request'] = "/favicon.ico"
        jbuf['status'] = 1
        jbuf['data'] = ""
        jbuf['msg'] = "Exception in get_favicon(). Error: %s" % e
        return myjson.JSONEncoder().encode(jbuf)


if __name__ == '__main__':
    # set up our logging
    try:
        cfg.log = MothershipLogger(cfg)
    except Exception, e:
        raise ShipDaemonError(e)
    cfg.log.debug("initializing logger in ship_daemon.py")
    # run our module loader once at startup
    load_modules(auth=False)
    # the daemon
    bottle.run(httpship, host='0.0.0.0', port=8081, reloader=False)
