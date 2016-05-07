#!/usr/bin/env python
# Copyright (C) 2015 Thomas Huang
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.version_info < (2, 7):
    raise NotImplementedError("Sorry, you need at least Python 2.7+ or Python 3.x to use chronos.")

import chronos


readme = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

setup(name='chronospy',
      version=chronos.__version__,
      description='Mutil-thread/mutil-process task scheduler drive by Tornado IOLoop for human.',
      long_description=readme,
      author="Thomas Huang",
      url='https://github.com/whiteclover/chronos',
      author_email='lyanghwy@gmail.com',
      py_modules=['chronos'],
      install_requires=['setuptools', 'tornado'],
      keywords=[
          'schedule', 'periodic', 'jobs', 'scheduling', 'clockwork',
          'cron'
      ],
      license="GPL",
      platforms='any',
      classifiers=(
          "Development Status :: 3 - Alpha",
          "License :: OSI Approved :: GNU Affero General Public License v3",
          "Natural Language :: English",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
          "Operating System :: OS Independent",
      )
      )
