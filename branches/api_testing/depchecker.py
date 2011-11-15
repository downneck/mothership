#!/usr/bin/env python
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
#
# A very simple dependency checker to ensure that mothership
# dependencies are all ready

import sys
import shlex
import subprocess

def check_or_die(cmd, descr):
    """
        Run a command and check exit value.  Exit if not good
    """
    args = shlex.split(cmd)
    sys.stdout.write("Checking %s... " % descr)
    retval = subprocess.call(args,
                stdout=open('/dev/null', 'w'),
                stderr=subprocess.STDOUT)
    if retval == 0:
        print "YES"
        return None
    else:
        print "NO"
        return cmd

deps = [
    ["which psql", "postgres is installed"],
    ["which python", "python is installed"],
    ["python -c 'import psycopg2'", "psycopg2 is installed"],
    ["python -c 'import cmdln'", "cmdln is installed"],
    ["which cobbler", "cobbler is installed"],
    ["which puppet", "puppet is installed"]
]

fail = []

for item in deps:
    retval = check_or_die(item[0], item[1])
    if retval:
        fail.append(retval)


if not fail:
    print "\nAll check tests passed!  You can begin the configuration phase of mothership"
else:
    print "\nYour system failed the following checks:"
    for failcmd in fail:
        print failcmd
    print "Please install the missing software and re-run the installer"
    sys.exit(1)
