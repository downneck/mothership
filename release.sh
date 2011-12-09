#!/bin/bash

set -e 
set -u

if test ! -f 'setup.py'; then
    echo 'ERROR: setup.py is not in the current dir'
    exit -1
fi

echo ''
echo 'WARNIG:\n'
echo '\tNote this script will increase only the minor version'
echo '\tif this is not what you want the script will wait 10 sec'
echo '\tbefore continue with the operation (i.e you can control+c now)'
sleep 10

CURRENT=`cat setup.py | grep version | awk -F = {'print $2'} | sed -e "s/'\(.*\)',/\1/g"`
NEW=`echo ${CURRENT} | awk -F. {'print $1,$2,$3+1'}| tr -s '\ ' '.'`

echo "New Mothership version will be ${NEW}"
echo "Last 5 sec for abort (i.e control+c)"
sleep 5

git tag -a ${NEW} HEAD -m "${NEW}"
python setup.py bdist

echo 'New tar.gz created inside dist/ with version $NEW'
