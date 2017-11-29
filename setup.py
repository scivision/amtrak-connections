#!/usr/bin/env python
install_requires = ['python-dateutil','pandas','matplotlib','numpy', 'beautifulsoup4']
tests_requires=['nose','coveralls']

# %% install
from setuptools import setup,find_packages

setup(name='Amtrak Connections',
      packages=find_packages(),
      author='Michael Hirsch, Ph.D.',
      description='Plots historical Amtrak connections',
      version='0.5.0',
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require={'test':tests_require},
      python_requires='>=2.7',
      )
