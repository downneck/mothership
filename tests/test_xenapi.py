import sys
import XenAPI
from pprint import pprint


class XenServerAPI:
    def __init__(self, host, user, passwd):
        self.session = XenAPI.Session('https://%s:443' % host)
        try: 
            self.session.xenapi.login_with_password(user, passwd)
        except XenAPI.Failure, e:
            # If slave host from pool chosed, contact master
            exec 'err=%s' % str(e)
            self.session = XenAPI.Session('https://%s:443' % err[1])
            self.session.xenapi.login_with_password(user, passwd)
        except Exception, e:
            print str(e)
            raise

    def choose_storage(self):
        srs = self.session.xenapi.SR.get_all_records()
        storage = {}
        for s in srs:
            if 'storage' in srs[s]['name_label'] and \
                'Removable' not in srs[s]['name_label'] \
                and srs[s]['name_label'] not in storage:
                storage[srs[s]['name_label']] = {
                    'size': long(srs[s]['physical_size']),
                    'used': long(srs[s]['physical_utilisation']),
                    'free': long(srs[s]['physical_size']) \
                          - long(srs[s]['physical_utilisation']),
                    }
    
        if len(storage.keys()) == 1:
            return storage.keys()[0]
        if len(storage.keys()) > 1:
            print 'There are multiple storage resources available:'
            for s in storage.keys():
                print '%d) %-35s (%5d GB free)' % (storage.keys().index(s),
                    s, storage[s]['free']/1024/1024/1024)
            ans = raw_input('Which one do you want to use: ')
            if int(ans) < 0 or int(ans) >= len(storage.keys()):
                print 'Storage selection aborted.'
                return False
            else:
                print 'User selected "%s"' % storage.keys()[int(ans)]
                return storage.keys()[int(ans)]
        else:
            return False
    
    def check_memory(self, need=None):
        maxfree = 0
        hosts = self.session.xenapi.host.get_all()
        for h in hosts:
            free = long(self.session.xenapi.host.compute_free_memory(h))/1024/1024
            #print '%-20s: %5d MB Memory Free' % (self.session.xenapi.host.get_hostname(h), free)
            if (free > maxfree):
                maxfree = free
        if need:
            return maxfree>=need
        else:
            return maxfree

    def check_vcpus(self, need=None):
        hcpus = 0
        vcpus = 0
        vms = self.session.xenapi.VM.get_all_records()
        for v in vms:
            if vms[v]['power_state'] == 'Running':
                if 'Control domain' in vms[v]['name_label']:
                    hcpus += int(vms[v]['VCPUs_max'])
                else:
                    vcpus += int(vms[v]['VCPUs_max'])
        #print 'Pool/Host is currently using %d out of %d CPUs' % (int(vcpus), int(hcpus))
        if need:
            return int(hcpus)-int(vcpus)>=need
        else:
            return int(hcpus)-int(vcpus)

    def check_storage(self, disk=None, need=None):
        if not disk:
            return False
        maxfree = 0
        srs = self.session.xenapi.SR.get_all()
        for s in srs:
            name = self.session.xenapi.SR.get_name_label(s)
            if name == disk:
                free = (long(self.session.xenapi.SR.get_physical_size(s)) \
                    - long(self.session.xenapi.SR.get_physical_utilisation(s))  \
                    ) / 1024 / 1024 / 1024
                #print '%-20s: %5d GB Storage Free' % (name, free)
                if (free > maxfree):
                    maxfree = free
        if need:
            return maxfree>=need
        else:
            return maxfree

if __name__ == "__main__":
    try:
        xs = XenServerAPI('xen1.mgmt', 'root', 'r0Qu3f0rt')
        disk = xs.choose_storage()
        print '\nUtilizing "%s"\n' % disk
        #print xs.check_memory()
        #print xs.check_memory(10000)
        #print xs.check_memory(20000)
        #print xs.check_vcpus()
        #print xs.check_vcpus(32)
        #print xs.check_vcpus(64)
        print xs.check_storage(disk)
    except Exception, e:
        print str(e)
        raise

    try:
        xs = XenServerAPI('xen5.mgmt', 'root', 'r0Qu3f0rt')
        #print '\nUtilizing "%s"\n' % xs.choose_storage()
        #print xs.check_memory()
        #print xs.check_vcpus()
    except Exception, e:
        print str(e)
        raise

