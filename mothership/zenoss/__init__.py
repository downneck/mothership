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
"""
Zenoss-3.0.x JSON API (python)

To quickly explore, execute 'python -i api_example.py host user pass'

z = ZenossAPI()
events = z.get_events()
etc.
"""

try:
    import json
except ImportError:
    import simplejson as json

import urllib
import urllib2


ROUTERS = { 'MessagingRouter': 'messaging',
            'EventsRouter': 'evconsole',
            'ProcessRouter': 'process',
            'ServiceRouter': 'service',
            'DeviceRouter': 'device',
            'NetworkRouter': 'network',
            'TemplateRouter': 'template',
            'DetailNavRouter': 'detailnav',
            'ReportRouter': 'report',
            'MibRouter': 'mib',
            'ZenPackRouter': 'zenpack' }

class ZenossError(Exception):
    pass

class ZenossAPI:
    def __init__(self, auth, debug=False):
        """
        Initialize the API connection, log in, and store authentication cookie
        """
        # Use the HTTPCookieProcessor as urllib2 does not save cookies by default
        self.urlOpener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        if debug: self.urlOpener.add_handler(urllib2.HTTPHandler(debuglevel=1))
        self.reqCount = 1

        self.auth = auth
        self.base = '/zport/dmd/Devices'
        if 'arch' in auth:
            self.arch = auth['arch']
        else:
            self.arch = '/Server/Linux/'

        # Contruct POST params and submit login.
        loginParams = urllib.urlencode(dict(
                        __ac_name = self.auth['user'],
                        __ac_password = self.auth['pass'],
                        submitted = 'true',
                        came_from = 'http://' + auth['host'] + ':8080/zport/dmd'))
        self.urlOpener.open('http://' + auth['host'] + ':8080/zport/acl_users/cookieAuthHelper/login',
                            loginParams)

    def _router_request(self, router, method, data=[]):
        if router not in ROUTERS:
            raise ZenossError('Router "' + router + '" not available.')

        # Contruct a standard URL request for API calls
        req = urllib2.Request('http://' + self.auth['host'] + ':8080/zport/dmd/' +
                              ROUTERS[router] + '_router')

        # NOTE: Content-type MUST be set to 'application/json' for these requests
        req.add_header('Content-type', 'application/json; charset=utf-8')

        # Convert the request parameters into JSON
        reqData = json.dumps([dict(
                    action=router,
                    method=method,
                    data=data,
                    type='rpc',
                    tid=self.reqCount)])

        # Increment the request count ('tid'). More important if sending multiple
        # calls in a single request
        self.reqCount += 1

        # Submit the request and convert the returned JSON to objects
        return json.loads(self.urlOpener.open(req, reqData).read())

##### Below are leftover examples provided by Zenoss as the only documentation of this API:

    def get_devices(self, deviceClass='/zport/dmd/Devices'):
        return self._router_request('DeviceRouter', 'getDevices',
            data=[{'uid': deviceClass, 'params': {}, 'limit': None}])['result']


    def get_events(self, device=None, component=None, eventClass=None):
        data = dict(start=0, limit=100, dir='DESC', sort='severity')
        data['params'] = dict(severity=[5,4,3,2], eventState=[0,1])

        if device: data['params']['device'] = device
        if component: data['params']['component'] = component
        if eventClass: data['params']['eventClass'] = eventClass

        return self._router_request('EventsRouter', 'query', [data])['result']

    def add_device(self, deviceName, deviceClass):
        data = dict(deviceName=deviceName, deviceClass=deviceClass)
        return self._router_request('DeviceRouter', 'addDevice', [data])

    def create_event_on_device(self, device, severity, summary):
        if severity not in ('Critical', 'Error', 'Warning', 'Info', 'Debug', 'Clear'):
            raise ZenossError('Severity "' + severity +'" is not valid.')

        data = dict(device=device, summary=summary, severity=severity,
                    component='', evclasskey='', evclass='')
        return self._router_request('EventsRouter', 'add_event', [data])

##### All mothership module-related functions will be below this line:

    def add_tag(self, tag, arch=None):
        if arch is None: arch = self.arch
        test = self.test_tag(tag, arch)
        if test['type'] == 'exception':
        #    print 'Node does not exist, adding'
            data = dict(type='organizer', contextUid=self.base+arch, id=tag)
            return self._router_request('DeviceRouter', 'addNode', [data])
        #else:
        #    print 'Node already exists'

    def add_host(self, unqdn, tag, arch=None):
        if arch is None: arch = self.arch
        # set state/tag first, in case host already exists
        self.set_host_state(unqdn)
        self.set_host_tag(unqdn, tag=tag, arch=arch)
        self.add_tag(tag=tag, arch=arch)
        # then proceed to addDevice, for new hosts
        data = dict(deviceName=unqdn, deviceClass=arch+tag, productionState=1000)
        return self._router_request('DeviceRouter', 'addDevice', [data])

    def disable_host(self, unqdn):
        return self.set_host_state(unqdn,-1)

    def set_host_ip(self, unqdn, ip=''):
        dev_list = self.get_devices()
        for device in dev_list['devices']:
            if device['name'] == unqdn:
                data = dict(uids=[device['uid']], hashcheck=dev_list['hash'], ip=ip)
                return self._router_request('DeviceRouter', 'resetIp', [data])

    def set_host_tag(self, unqdn, tag='', arch=None):
        if arch is None: arch = self.arch
        dev_list = self.get_devices()
        for device in dev_list['devices']:
            if device['name'] == unqdn:
                data = dict(uids=[device['uid']], hashcheck=dev_list['hash'], target=self.base+arch+tag)
                return self._router_request('DeviceRouter', 'moveDevices', [data])

    def set_host_state(self, unqdn, state=1000):
        dev_list = self.get_devices()
        for device in dev_list['devices']:
            if device['name'] == unqdn:
                data = dict(uids=[device['uid']], hashcheck=dev_list['hash'], prodState=state)
                return self._router_request('DeviceRouter', 'setProductionState', [data])

    def test_tag(self, tag, arch=None):
        if arch is None: arch = self.arch
        return self._router_request('DeviceRouter', 'getInfo', [{'uid':self.base+arch+tag}])

 
##### If this script is not run as a module:
if __name__ == "__main__":
    import os
    import sys
    if len(sys.argv) < 3:
        print '''
Usage: %s <host> <user> <pass>
       %s zenoss2.prod.iad login secret
''' % (tuple([ os.path.basename(sys.argv[0]) for i in range(0,2) ]))
        sys.exit(3)
    if 'debug' in sys.argv: debug = True
    auth = {
        'host': sys.argv[1],
        'user': sys.argv[2],
        'pass': sys.argv[3],
    }
    z = ZenossAPI(auth)
    print z.get_devices()

