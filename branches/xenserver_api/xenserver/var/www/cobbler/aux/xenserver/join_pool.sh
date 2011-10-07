#!/bin/bash
# Script to smartly join pool master 

XE=/opt/xensource/bin/xe

if [[ $($XE host-list params=uuid | grep -v ^$| wc -l) -gt 1 ]]; then
    echo -ne "\nYou are already part of a pool whose master is: "
    uuid_host=$( $XE pool-list params=master | sed 's/^.*: //' )
    $XE host-list uuid=$uuid_host params=name-label | sed 's/^.*: //'
else
    if [[ $# -lt 2 ]]; then
        echo "Usage: ${0##*/} master-address master-password [master-username(default:root)]"
        exit 1
    fi
    $XE pool-join master-address=$1 master-password=$2 master-username=${3:-root}
fi

cat << EOF

==================================================================================
IMPORTANT!
----------
Remove old local bond with /etc/firstboot.d/data/remove_bond.sh [bond0]
Recreate pooled bond with /etc/firstboot.d/data/configure_bond0.sh [bond0]
Add default gateway for bond with /etc/firstboot.d/data/default_gateway.sh [bond0]
==================================================================================

EOF

