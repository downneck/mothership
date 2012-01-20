#!/usr/bin/python

import setuptools
from setuptools import setup,  find_packages

install_requires = [
    'cmdln',
    'SQLAlchemy == 0.5.5'
    ]

extras_require = {
    'ldap' : 'python-ldap',
    'postgres' : 'psycopg2'
    }

setup(name='Mothership',
      author='Gilt SA team',
      author_email='sa@gilt.com',
      description='Mothership - asset managment',
      packages=find_packages(),
      scripts=['ship',
               'ship_readonly'
               ],
      url='http://mothership.sf.net',
      version='0.0.4',
     )
