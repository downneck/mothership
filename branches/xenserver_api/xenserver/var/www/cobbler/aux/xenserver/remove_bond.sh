#!/bin/bash
# Script to join pool master and remove old bond

BOND=${1:-bond0}
XE=/opt/xensource/bin/xe
uuid_host=$($XE host-list name-label=$HOSTNAME params=uuid | sed 's/^.*: //' )
uuid_bond=$($XE pif-list device=$BOND host-uuid=$uuid_host params=uuid | sed 's/^.*: //')
uuid_pif=$($XE bond-list master=$uuid_bond params=uuid | sed 's/^.*: //')
uuid_net=$($XE pif-list device=$BOND host-uuid=$uuid_host params=network-uuid | sed 's/^.*: //')
$XE pif-param-set uuid=$uuid_bond disallow-unplug="false"
$XE pif-unplug uuid=$uuid_bond
$XE bond-destroy uuid=$uuid_pif
#$XE pif-forget uuid=$uuid_bond
$XE network-destroy uuid=$uuid_net

