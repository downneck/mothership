#!/usr/bin/python

import setuptools
from setuptools import setup,  find_packages

install_requires = [
    'cmdln',
    'SQLAlchemy'
    ]

extras_require = {
    'ldap' : 'python-ldap',
    'postgres' : 'psycopg2'
    }

setup(name='Mothership',
      author='Gilt SA team',
      author_email='sa@gilt.com',
      description='Mothership - asset managment',
      install_requires = install_requires,
      extras_require = extras_require,
      packages=find_packages(),
      scripts=['ship',
               'ship_readonly'
               ],
      url='http://mothership.sf.net',
      version='0.0.1',
     )
