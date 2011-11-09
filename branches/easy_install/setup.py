#!/usr/bin/env python

from setuptools import setup,  find_packages

setup(name='Mothership',
      version='0.1',
      description='Mothership - asset managment',
      author='Gilt SA team',
      author_email='sa@gilt.com',
      url='http://mothership.sf.net',
      packages=find_packages(),
      scripts=['ship']
     )
