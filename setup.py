#!/usr/bin/env python
req = ['python-dateutil','pandas','matplotlib','numpy','beautifulsoup4']
# %%
import pip
try:
    import conda.cli
    conda.cli.main('install',*req)
except Exception as e:
    pip.main(['install'] + req)
# %% install
from setuptools import setup

setup(name='Amtrak Connections',
      packages=['amtrakconn'],
      author='Michael Hirsch, Ph.D.',
      description='Plots historical Amtrak connections',
      version='0.5',
      )
