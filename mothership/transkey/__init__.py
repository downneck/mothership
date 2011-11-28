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
Translate the keys of a dict with a specified dict-map,
join if mapped to a list, recurse if mapped to a dict

Run module as main script to see sample

mothership.transkey is a key translator between the source_dict and the target_dict desired
controlled my the map_dict specified.  For example, say the source is a database
with the following columns:

    source_dict = { col1:'val1', col2:'val2', ..., colX:'valX' }

and the target is dictionary of values that are built from the source values. To
translate you would build a map_dict like the following:

    map_dict = {
       'target_key1': 'scalar_value',
       'target_key2': col9,
       'target_key3': [ col8, col7 ],
       'target_key4': {
           'target_subkey1': col5,
           'target_subkey2': [ col4, source_key3 ],
        }
    }

The translation:

    target_dict = mothership.transkey(source_dict, map_dict, empty=True)

would yield:
   
    target_dict = {
       'target_key1': '',
       'target_key2': 'val9',
       'target_key3': 'val8.val7',
       'target_key4': {
           'target_subkey1': 'val5',
           'target_subkey2': 'val4.val3',
        }
    }
      
When empty=True, any keys that did NOT exist in the source_dict would result in
the deletion of the value in the target_dict.  If empty=False, however, the key
itself would become the value of the target_key:

    target_dict{ 'target_key1': 'scalar_value' }

Basically, all targets keys appear on the left of the map_dict, while any
combination of source keys are defined on the right.  Any source keys that are
not defined in the map_dict are automatically OMITTED, resulting in the instant
clean up if the source_dict had a lot of keys that were not needed in the target.

"""


import types


def transkey (olddict, mapdict, empty=False):
    newdict = {}
    for k in mapdict.keys():
        if type(mapdict[k]) is types.DictType:
            if 'rename' in mapdict[k]:
                newkey = mapdict[k]['rename']
                del mapdict[k]['rename']
            else:
                newkey = k
            if k == '*':
                for x in olddict.keys():
                    newdict[x] = mothership.transkey(olddict[x],mapdict[k], empty)
            else:
                newdict[newkey] = mothership.transkey(olddict[k],mapdict[k], empty)
        elif type(mapdict[k]) is types.ListType:
            delempty = []
            maplist = mapdict[k][:]
            for d in mapdict[k]:
                if d not in olddict.keys():
                    if empty:   # see below
                        delempty.append(d)
                    else:
                        olddict[d] = d
            if len(delempty) > 0:
                for d in delempty:  # separate delete dict to avoid skipping keys
                    maplist.remove(d)
                newdict[k] = '.'.join([ olddict[x] for x in maplist ])
            else:
                newdict[k] = '.'.join([ olddict[x] for x in mapdict[k] ])
        else:
            if k not in olddict:
                if empty:   # fill missing values with empty string?
                    newdict[mapdict[k]] = ''
                else:       # fill missing values with map key name
                    newdict[k] = mapdict[k]
            else:
                newdict[mapdict[k]] = olddict[k]
    return newdict


def transkey_sample ():
    olddict = {
        'str1' : 'string1',
        'str2' : 'string2',
        'list1' : [ 'elem1', 'elem2', 'elem3' ],
        'dict1' : {
            'str10': 'string10',
            'str20': 'string20',
            'str30': 'string30',
            'list10' : [ 'elem10', 'elem20', 'elem30' ],
            },
        'dict2' : {
            'str10': 'string10',
            'str20': 'string20',
            'str30': 'string30',
            'list10' : [ 'elem10', 'elem20', 'elem30' ],
            },
        'dict3' : {
            'str100': 'string100',
            'str200': 'string200',
            'str300': 'string300',
            'list100' : [ 'elem100', 'elem200', 'elem300' ],
            },
        'network' : {
            'eth0' : {
                'key1' : 'val1',
                'key2' : [ 'one', 'two', 'three' ]
                },
            'eth1' : {
                'key1' : 'val3',
                'key2' : [ 'four', 'five', 'six' ]
                }
            }
        }
    mapdict = {
        'test' : [ 'str1' ],
        'str1' : 'strA',
        'str2' : 'strB',
        'str3' : 'strC',
        'list1' : 'listA',
        'list2' : [ 'str3', 'str2', 'str1', 'static' ],
        'dict1' : 'dictA',
        'dict2' : {
            'str20' : 'new2',
            'list10' : 'array1'
            },
        'dict3' : {
            'rename' : 'hash3',
            'str300' : '123',
            'list100' : [ 'str300', 'str200', 'str100' ]
            },
        'network' : {
            'rename' : 'interfaces',
            '*' : {
                'key1' : 'string',
                'key2' : 'listing',
                },
            },
        }
    
    from pprint import pprint
    print "=== Original dict ==="
    pprint (olddict)
    print "=== Translation dict ==="
    pprint (mapdict)
    print "=== Translated dict ==="
    pprint (mothership.transkey(olddict, mapdict))


if __name__ == "__main__":
    mothership.transkey_sample()  # if not called as a module, execute example







