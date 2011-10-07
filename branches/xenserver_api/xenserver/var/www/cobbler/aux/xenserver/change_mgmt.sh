#!/bin/bash
# Script to change management interface to specified port

if [[ $# -lt 1 ]]; then
    echo "Usage: ${0##*/} interface-name (i.e. bond0 or eth0)"
    exit 1
fi

BOND=$1
XE=/opt/xensource/bin/xe
uuid_bond=$( $XE pif-list host-name-label=$HOSTNAME device=$BOND params=uuid | sed 's/^.*: //' )
$XE host-management-reconfigure pif-uuid=$uuid_bond

# Configure the defautl gateway after any nic changes
${0%%/*}/default_gateway.sh

