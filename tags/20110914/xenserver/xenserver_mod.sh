#!/bin/bash

# Verify user is root
if [[ $(id -un) != 'root' ]]; then
    echo "This script can only be run as root!"
    exit 3
fi

# cobbler subdirs
cobbler_dirs="
    etc/cobbler/power
    var/lib/cobbler/kickstarts
    var/lib/cobbler/triggers/sync/post
    var/www/cobbler/aux/xenserver
    "

# The aux/xenserver was not part of the original cobbler design
[[ ! -d /var/www/cobbler/aux/xenserver ]] \
    && mkdir -p /var/www/cobbler/aux/xenserver

# Check to ensure cobbler dirs exists before updating
for d in $cobbler_dirs; do
    if [[ -d /$d ]]; then
        cp -f $d/* /$d
    else
        echo "Skipping missing /$d, check your cobbler installation"
    fi
done

