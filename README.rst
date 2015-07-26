Chronos
#########

Chronos is a mutil-thread/mutil-process task scheduler drive by Tornado IOLoop.


.. contents::
    :depth: 4


Install
==============

Install the extension with the following command::

    $ easy_install chronospy

or alternatively if you have pip installed::


    $ pip install chronospy


or clone it form github then run the command in shell:

.. code-block:: bash

    cd chronos # the path to the project
    python setup.py install



Hello World
=============


.. code-block:: python

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


API
============

setup
-----------------------
setup(io_loop=None)

bind a io_loop  or use default ioloop.


schedule
--------------------------------------------------------------------------------------------

schedule(name, timer, func, once=False, start=False, process=False, max_executor=5)

add task into chronos:


:name: uniqe task name,
:timer: every timer object
:func: the task function
:once: set True will run only once time.
:start: when chronos start and schedule a new task, if set to True will add to Tornado IOLoop and schedule to run at time.
:process: if process is True, then the job will run in on a procees, otherwise defaultly running in thread.
:max_executor: the max threads(or processes) to run a task.


remove_task
------------------------------

remove_task(task_name)

stop and remove the task from chronos



start_task
--------------------------

start_task(task_name)

start the task in chronos


stop_task
----------------------------
stop_task(task_name)

stop the task in chronos

start
----------------------------
start(start_ioloop=False)

add tasks in ioloop, if you use chronos in a tornado web server, you can set start_ioloop to "False", then start your custom ioloop later.


stop
----------------------------------------------
stop(stop_ioloop=False, clear=True)

stop the task in ioloop

:stop_ioloop: will stop the ioloop if set to "True".
:clear: will remove tasks from chrons if set to "True".

how to use every tools
==========================

every_second
-----------------


set eveny seconds to run a job:

	every_second(5) # run job every 5 seconds


every_at
----------------


set every hourly or mintuely run a job:

	every_at(every_at(hour=1, minute=10, second=0)) # run at 01:10:00 every day
	every_at(every_at(minute=10, second=0)) # run at run at 10 mintue every hour


every
-------------

.. code-block:: python

	every(10).minutes
	every().hour
	every().day.at("10:30")
	every().monday
	every().wednesday.at("13:15")


LICENSE
=======

    Copyright (C) 2015 Thomas Huang

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 2 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.