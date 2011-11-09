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
mothership.ssh

this module holds methods for dealing with SSH
things like manipulating host keys and user public keys
"""

# imports
import os
import mothership.validate

# db imports
from mothership.mothership_models import *

# create an error class
class SSHError(Exception):
    pass

# turn a public key file into an array of keys
def unpack_ssh_public_key_file(cfg, keyfile):
    """
    [description]
    unpacks a (potentially multi-line) ssh2 public key file into an array of keys

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        keyfile: the filesystem path to the ssh2 public key file

    [return value]
    returns an array of valid ssh2 public keys, suitable for storage in db or writing to an authorized_keys file
    """

    # make sure the keyfile exists
    if os.path.isfile(keyfile):
        f = open(keyfile, 'r')
        pubkey = f.readlines()
        f.close()
    else:
        raise SSHError("public key file does not exist, aborting!")
    # iterate through multiple keys (potentially), make sure they're valid
    ssh_public_key_array = []
    for key in pubkey:
        if mothership.validate.v_ssh2_pubkey(cfg, key) == False:
            raise SSHError("Keyfile contains lines that are improperly formatted or not ssh2 keys, aborting\nmothership does not currently support ssh v1 keys")
        else:
            ssh_public_key_array.append(key)
            continue
    return ssh_public_key_array


# writes an ssh public key string to a file
def write_key_to_file(cfg, pubkey_string, keyfile):
    """
    [description]
    wrtes an ssh public key string to a file

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        pubkey_string: a string (with embedded newlines) of ssh2 keys
        keyfile: the filesystem path to the ssh2 public key file

    [return value]
    no explicit return
    """
    pubkey_array = pubkey_string.split('\n')

    for key in pubkey_array:
        if mothership.validate.v_ssh2_pubkey(cfg, key) == False:
            raise SSHError("Keyfile contains lines that are improperly formatted or not ssh2 keys, aborting\nmothership does not currently support ssh v1 keys")

    if os.path.isfile(keyfile):
        ans = raw_input("keyfile exists, overwrite? (y/n): ")
        if ans != "Y" and ans != "y":
            raise SSHError("aborted by user input")

    head, tail = os.path.split(keyfile)
    if not tail:
        raise SSHError("no filename provided")
    elif head and not tail:
        raise SSHError("no filename provided")
    elif head and tail and not os.path.isdir(head):
        ans = raw_input("Directory %s does not exist, do you want to create it? (y/n): " % head)
        if ans != "Y" and ans != "y":
            raise SSHError("aborted by user input")
        else:
            os.makedirs(head, 0755)
            print "Directory %s created" % head

    f = open(keyfile, 'w')
    if not f:
        raise SSHError("Unable to open keyfile")
    f.write(pubkey_string)
    f.close()
