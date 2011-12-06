#!/usr/bin/python

import setuptools
from setuptools import setup,  find_packages

install_requires = [
    'psycopg2',
    'cmdln',
    'python-ldap',
    'SQLAlchemy'
    ]

setup(name='Mothership',
      author='Gilt SA team',
      author_email='sa@gilt.com',
      description='Mothership - asset managment',
      install_requires = install_requires,
      packages=find_packages(),
      scripts=['ship',
               'ship_readonly'
               ],
      url='http://mothership.sf.net',
      version='0.1',
     )
