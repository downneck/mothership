#!/usr/bin/env python
# Testing basic libcloud functions with EC2 in preparation for ship functionality

import os
import re
import sys
import types
import socket
from pprint import pprint

from libcloud.types import Provider 
from libcloud.providers import get_driver 
 
EC2_ACCESS_ID = open('/Users/klee/.ec2/access','r').readline().rstrip()
EC2_SECRET_KEY = open('/Users/klee/.ec2/secret','r').readline().rstrip()
 
Driver = get_driver(Provider.EC2) 
conn = Driver(EC2_ACCESS_ID, EC2_SECRET_KEY) 
 

#print conn.list_images() 
#print conn.list_sizes() 
#print conn.list_nodes() 


def usage(code=0):
    print '''
Usage: %s -s

    -h				help
    -f host|ip			find host/ip
    -r host|ip			reboot host/ip
    ''' % os.path.basename(sys.argv[0])
    sys.exit(code)


def find_node(n):
    if re.search('\w+', n):
        n = socket.gethostbyname(n)
    for node in conn.list_nodes():
        for p in node.public_ip:
            if re.search(n, p):
                return node


def security_group(g):
    pass 


def reboot_node(n):
    node = find_node(n)
    if not node:
        print 'Node matching "%s" not found' % n
    else:
        num = node.id.replace('i-','')
        ans = raw_input("to reboot node \"%s\" please type \"reboot_%s\": " %
            (node.public_ip[0], num))
        if ans != "reboot_%s" % num:
            raise RuntimeError("aborted by user")
        else:
            conn.reboot_node(node)


def main (args):
    # parse/process command line options/arguments
    import getopt
    try:
        opts, args = getopt.getopt(args, "f:g:hr:",
            [ '--find', '--group',
              '--reboot',
              '--help' ])
    except getopt.error:
        usage(3)

    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage(3)
        if opt in ('-g', '--group'):
            security_group(val)
            sys.exit(0)
        if opt in ('-r', '--reboot'):
            reboot_node(val)
            sys.exit(0)
        if opt in ('-f', '--find'):
            node = find_node(val)
            for key in dir(node):
                attr = getattr(node, key)
                if re.match('__', key): continue
                if type(attr) is types.StringType or \
                   type(attr) is types.ListType or \
                   type(attr) is types.DictType:
                    print key+': ',
                    pprint(attr)
            sys.exit(0)

    #print dir(conn)
    usage(3)


if __name__ == "__main__":
    main(sys.argv[1:])

