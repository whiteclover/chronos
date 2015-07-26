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

import logging
import time
import tornado
import chronos
import os
import urllib2


def test_process():
    LOGGER.info("process pid %s", os.getpid())


def test(word):
    LOGGER.info("an other task, say '%s'", word)


def say():
    response = urllib2.urlopen('https://www.google.com/')
    html = response.read()
    LOGGER.info(html[:10])


def init():
    global LOGGER
    debug = True
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', filemode='a+')

    LOGGER = logging.getLogger("demo")

    # bind a ioloop or use default ioloop
    chronos.setup()  # chronos.setup(tornado.ioloop.IOLoop())
    chronos.schedule('say', chronos.every_second(1), say)
    chronos.schedule('say2', chronos.every_second(1), test_process, once=True, process=True)
    chronos.schedule('say3', chronos.every_second(1), lambda: test("test3"))
    chronos.start(True)

if __name__ == '__main__':

    init()
