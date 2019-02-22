#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst

import ah_bootstrap
from setuptools import setup
from configparser import ConfigParser

# Continue to use astropy_helpers for generating version.py for now
# Eventually we should be using setuptools_scm
from astropy_helpers.version_helpers import generate_version_py

conf = ConfigParser()
conf.read(['setup.cfg'])
metadata = dict(conf.items('metadata'))

name = metadata['package_name']
version = metadata['version']
release = 'dev' in version
generate_version_py(name, version, release)


setup()
