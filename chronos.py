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


"""Chronos
===========

Chronos is a mutil-thread/mutil-process task scheduler drive by Tornado IOLoop.
"""

from datetime import timedelta, datetime, time as datetime_time

import logging
import multiprocessing
import os
import signal
import sys
import threading
import time

import tornado.ioloop


try:
    from thread import get_ident
except ImportError:
    from _thread import get_ident


LOG = logging.getLogger("chronos")


__version__ = '0.1.7'


def every_second(seconds):
    """
    Iterator-based timer

    @example
            every(seconds=10)
    @return an iterator of timedelta object

    >>> t = every_second(10)
    >>> t.next().total_seconds()
    10.0
    >>> t.next().total_seconds()
    10.0
    """
    delta = timedelta(seconds=seconds)
    # Never return StopIteration
    while 1:
        yield delta


class every_at(object):
    """
    A class-based iterator that help install a timer for hourly scheduled task
    - Every hour in a day
    - Fixed hour in a day

    The name is chosen in all lower case to make it looks like a function because it will
    be used as if it was a generator.
    >>> h = every_at(minute=10)

    """

    def __init__(self, hour=None, minute=0, second=0):
        self.started = False
        self.hour = hour
        self.minute = minute
        self.second = second

    def __iter__(self):
        return self

    def next(self):
        '''
        Never return StopIteration
        '''
        if self.started is False:

            self.started = True
            now_ = datetime.now()
            if self.hour:
                # Fixed hour in a day
                # Next run will be the next day
                scheduled = now_.replace(hour=self.hour, minute=self.minute, second=self.second, microsecond=0)
                if scheduled == now_:
                    return timedelta(seconds=0)
                elif scheduled < now_:
                    # Scheduled time is passed
                    return scheduled.replace(day=now_.day + 1) - now_
            else:
                # Every hour in a day
                # Next run will be the next hour
                scheduled = now_.replace(minute=self.minute, second=self.second, microsecond=0)
                if scheduled == now_:
                    return timedelta(seconds=0)
                elif scheduled < now_:
                    # Scheduled time is passed
                    return scheduled.replace(hour=now_.hour + 1) - now_
            return scheduled - now_
        else:
            if self.hour:
                return timedelta(days=1)  # next day
            return timedelta(hours=1)  # next hour


class every(object):

    """A periodic job as used by `Chronos`."""

    def __init__(self, interval=1):
        self.interval = interval  # pause interval * unit between runs
        self.unit = None  # time units, e.g. 'minutes', 'hours', ...
        self.at_time = None  # optional time at which this job runs
        self.period = None  # timedelta between runs, only valid for
        self.start_day = None  # Specific day of the week to start on
        self.fisrt_ruuned = False

    def __repr__(self):
        """Dump printter
        """
        if self.at_time is not None:
            return 'Every %s %s at %s' % (
                self.interval,
                self.unit[:-1] if self.interval == 1 else self.unit,
                self.at_time)
        else:
            return 'Every %s %s' % (
                self.interval,
                self.unit[:-1] if self.interval == 1 else self.unit)

    @property
    def second(self):
        assert self.interval == 1
        return self.seconds

    @property
    def seconds(self):
        self.unit = 'seconds'
        return self

    @property
    def minute(self):
        assert self.interval == 1
        return self.minutes

    @property
    def minutes(self):
        self.unit = 'minutes'
        return self

    @property
    def hour(self):
        assert self.interval == 1
        return self.hours

    @property
    def hours(self):
        self.unit = 'hours'
        return self

    @property
    def day(self):
        assert self.interval == 1
        return self.days

    @property
    def days(self):
        self.unit = 'days'
        return self

    @property
    def week(self):
        assert self.interval == 1
        return self.weeks

    @property
    def monday(self):
        assert self.interval == 1
        self.start_day = 'monday'
        return self.weeks

    @property
    def tuesday(self):
        assert self.interval == 1
        self.start_day = 'tuesday'
        return self.weeks

    @property
    def wednesday(self):
        assert self.interval == 1
        self.start_day = 'wednesday'
        return self.weeks

    @property
    def thursday(self):
        assert self.interval == 1
        self.start_day = 'thursday'
        return self.weeks

    @property
    def friday(self):
        assert self.interval == 1
        self.start_day = 'friday'
        return self.weeks

    @property
    def saturday(self):
        assert self.interval == 1
        self.start_day = 'saturday'
        return self.weeks

    @property
    def sunday(self):
        assert self.interval == 1
        self.start_day = 'sunday'
        return self.weeks

    @property
    def weeks(self):
        self.unit = 'weeks'
        return self

    def at(self, time_str):
        """Schedule the job every day at a specific time.
        Calling this is only valid for jobs scheduled to run every
        N day(s).
        """
        assert self.unit in ('days', 'hours') or self.start_day
        hour, minute = [t for t in time_str.split(':')]
        minute = int(minute)
        if self.unit == 'days' or self.start_day:
            hour = int(hour)
            assert 0 <= hour <= 23
        elif self.unit == 'hours':
            hour = 0
        assert 0 <= minute <= 59
        self.at_time = datetime_time(hour, minute)
        return self

    def __iter__(self):
        return self

    def next(self):
        """Compute the instant when this job should run next."""
        # Allow *, ** magic temporarily:
        # pylint: disable=W0142
        assert self.unit in ('seconds', 'minutes', 'hours', 'days', 'weeks')
        self.period = timedelta(**{self.unit: self.interval})
        now_ = datetime.now()
        next_run = now_ + self.period
        if self.start_day is not None:
            assert self.unit == 'weeks'
            weekdays = (
                'monday',
                'tuesday',
                'wednesday',
                'thursday',
                'friday',
                'saturday',
                'sunday'
            )
            assert self.start_day in weekdays
            weekday = weekdays.index(self.start_day)
            days_ahead = weekday - next_run.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_run += timedelta(days_ahead) - self.period
        if self.at_time is not None:
            assert self.unit in ('days', 'hours') or self.start_day is not None
            kwargs = {
                'minute': self.at_time.minute,
                'second': self.at_time.second,
                'microsecond': 0
            }
            if self.unit == 'days' or self.start_day is not None:
                kwargs['hour'] = self.at_time.hour
            next_run = next_run.replace(**kwargs)
            # If we are running for the first time, make sure we run
            # at the specified time *today* (or *this hour*) as well
            if not self.fisrt_ruuned:

                if (self.unit == 'days' and self.at_time > now_.time() and
                        self.interval == 1):
                    next_run = next_run - timedelta(days=1)
                elif self.unit == 'hours' and self.at_time.minute > now_.minute:
                    next_run = next_run - timedelta(hours=1)
                self.fisrt_ruuned = True
        if self.start_day is not None and self.at_time is not None:
            # Let's see if we will still make that time we specified today
            if (next_run - now_).days >= 7:
                next_run -= self.period
        return next_run - now_


_SHUTDOWNTASK = None


class Task(object):

    """"Task  executor manager """

    def __init__(self, task_name, action, timer, io_loop, once=False, process=False, max_executor=5):
        """Scheduler Task

        schedule task

        Arguments:
            task_name {Sting} - -  the  unique identifire for the task
            action {Function} - - the task execute callable method
            timer {Scheule timer} - -   every timer object
            io_loop {IOLoop} - - the tornado IOLoop instance

        Keyword Arguments:
            once {bool} - -  when setting to ``True``, running only once time, else running loop(default: {False})
            process {bool} - -  when seting to ``True``, the executer will set to be process, else thread(default: {False})
            max_executor {number} - - The max number of executor(default: {5})

        Raises:
            ValueError - - Periodic callback must have a positive callback_time
        """
        callback_time = timer.next().total_seconds()
        if callback_time <= 0:
            raise ValueError("Periodic callback must have a positive callback_time")

        self.name = task_name
        self.action = action
        self.timer = timer
        self.once = once

        self.io_loop = io_loop
        self.max_executor = max_executor

        self.process = process
        self.executor_creator = ProcessExecutor if process else ThreadExecutor
        self.executors = []

        self._running = False
        self._timeout = None
        self.last_run = None

    def _new_executor(self):
        """Create new task executor
        """
        return self.executor_creator(self.action, self.name)

    @property
    def next_timeout(self):
        """Generating next running time
        """
        return self.timer.next().total_seconds()

    def start(self):
        """Starts the timer."""
        if self._running:
            LOG.info("Task '%s' had started" % (self.name))
            return
        self._running = True
        self._next_timeout = self.io_loop.time()
        self._schedule_next()

    def _schedule_next(self):
        """Scheduling next task executor time and setting the timer in IoLoop
        """
        if self._running:
            current_time = self.io_loop.time()
            self._next_timeout = current_time + self.next_timeout
            self._timeout = self.io_loop.add_timeout(self._next_timeout, self._run)

    def _run(self):
        """Running the executor
        """
        if not self._running:
            return

        executor = None
        try:
            executor = self.get_executor()
            if executor:
                executor.resume()
                self.last_run = datetime.now()
            else:
                LOG.warning("Above max task executors for Task<%s>" % (self.name))
        except Exception:
            LOG.error("Error in periodic callback", exc_info=True)
        finally:
            if not self.once:
                self._schedule_next()
            else:
                LOG.info("clear executors")
                self.stop(True)

    def get_executor(self):
        """Getting an task excutor from idle pool or creating a new one.
        """
        self.executors = [executor for executor in self.executors if executor.is_alive()]  # clear dead executor
        for executor in self.executors:
            if executor.is_idle():
                return executor

        executor = None
        if len(self.executors) < self.max_executor:
            executor = self._new_executor()
            self.executors.append(executor)
        return executor

    def stop(self, clear=False):
        """Stops the timer."""
        if not self._running:
            return
        self._running = False
        self.clear_executor(clear)

        if self._timeout is not None:
            self.io_loop.remove_timeout(self._timeout)
            self._timeout = None

    def running_executors(self):
        """Get running executors
        """
        return [e for e in self.executors if not e.is_idle()]

    def clear_executor(self, clear=False, timeout=5):
        """Clear and stop the executor

        Keyword Arguments:
            clear {bool} - -  whe setting to ``True``, will cear the task ioloop and executor pool(default: {False})
            timeout {number} - - the time wating the executor stop(default: {5})
        """
        # Must shut down executors here so the code that calls
        # this method can know when all executors are stopped.
        LOG.info("clear executors")
        ShutDown(self, clear, timeout).shutdown()

    def try_shutdown_thread(self):
        """Shutdown and stop the theading executor pool
        """
        for executor in self.executors:
            if executor.is_idle():
                if not self.process:
                    executor.action = _SHUTDOWNTASK
                    executor.resume()

    def try_shutdown_process(self):
        """Shutdown and stop the processing executor pool
        """
        if self.process:
            for executor in self.executors:
                self._graceful_shutdown_process(executor)

    def _graceful_shutdown_process(self, executor):
        """Gracefully shutdown and stop the processing executor pool
        """
        if executor.is_alive():
            executor.terminate()
            os.kill(executor.pid, signal.SIGTERM)
            # Force kill
            if executor.is_alive():
                terminate_process(executor.pid)

    def clear(self):
        """Clear the task action and executor pool
        """
        self.action = None
        self.executors[:] = []


class ShutDown(object):
    """Task shutdwon processer
    """

    def __init__(self, task, clear, timeout):
        """Task shutdwon processer

        Arguments:
            task {Task} - - The schedule task
            clear {bool} - - when ``True`` clear the task form ioloop and clear the exextuor
            timeout {number} - - the time watting for clear
        """
        LOG.debug(" shutdown Try stop task: %s", task.name)
        self.task = task
        self.timeout = timeout
        self._timeout = None
        self.clear = clear
        # try clear wait timer
        self.try_until = None
        self._next_timeout = None

    def shutdown(self):
        """Clear the task schedule
        """
        current_time = time.time()
        self.try_until = current_time + self.timeout
        self._schedule_next(current_time)
        LOG.debug("Try stop task: %s", self.task.name)

    def _try_shutdown(self):
        """Removing the task form ioloop and clear the task info
        """
        current_time = time.time()
        if current_time < self.try_until:
            self.task.try_shutdown_thread()
            self._schedule_next(current_time)
        else:
            self.task.try_shutdown_process()
            if self._timeout is not None:
                self.task.io_loop.remove_timeout(self._timeout)
                self._timeout = None
            LOG.info('Clear and stop task: "%s"' % (self.task.name))
            if self.clear:
                self.task.io_loop = None
            self.task.clear()
            self.task = None

    def _schedule_next(self, current_time):
        """Setting the timer to clear the task
        Arguments:
            current_time {number} - - the seconds in time future
        """
        self._next_timeout = current_time + 1
        self._timeout = self.task.io_loop.add_timeout(self._next_timeout, self._try_shutdown)


def terminate_process(pid):
    """Terminate process by process id

    Arguments:
        pid {number} - - the process id
    """
    # all this shit is because we are stuck with Python 2.5 and python 2.6
    if sys.platform == 'win32':
        import ctypes
        PROCESS_TERMINATE = 1
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
        ctypes.windll.kernel32.TerminateProcess(handle, -1)
        ctypes.windll.kernel32.CloseHandle(handle)
    else:
        os.kill(pid, signal.SIGKILL)


class ProcessExecutor(multiprocessing.Process):
    """The Process executor pool
    """

    def __init__(self, action, name):
        """The Process executor pool

        Arguments:
            action {function} - - the task callable fucntion
            name {String} - - the task name for unique identified the task
        """
        self.ready = False

        self.event = multiprocessing.Event()
        self.action = action

        multiprocessing.Process.__init__(self)
        self.name = name
        self.setup_signal_handle()
        self.start()

    def suspend(self):
        self.event.clear()
        self.event.wait()

    def setup_signal_handle(self):
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Process sinal handle
        """
        self.ready = False
        self.resume()

    def resume(self):
        """Resume prcoess
        """
        self.event.set()

    def is_idle(self):
        """Check the process is running

        Returns:
            [bool] - - it is idel when True
        """
        return not self.event.is_set()

    def run(self):
        """Start the process and calling the action
        """
        self.ready = True
        LOG.debug('Starting process %d', os.getpid())
        while self.ready:
            try:
                self.action()
            except Exception as e:
                cls, e, tb = sys.exc_info()
                LOG.exception('Unhandled Error in thread:%s %s', os.getpid(), e)
            self.suspend()
        LOG.debug('Stoped process %d...', os.getpid())
        self.event.clear()


class ThreadExecutor(threading.Thread):
    """The Thread executor pool
    """

    def __init__(self, action, name):
        """The Thread executor pool

        Arguments:
            action {function} - - the task callable fucntion
            name {String} - - the task name for unique identified the task
        """
        self.ready = False

        self.event = threading.Event()
        self.action = action

        threading.Thread.__init__(self)
        self.name = name
        # self.daemon = True
        self.start()

    def suspend(self):
        """Suspend the thread setting the event wait"""
        self.event.clear()
        self.event.wait()

    def is_idle(self):
        """Check the thread is idle

        Returns:
            [bool] - - it is idel when True
        """
        return not self.event.is_set()

    def resume(self):
        """Resume the current thread, setting the event
        """
        self.event.set()

    def run(self):
        """Start the thread and calling the action
        """
        self.ready = True
        LOG.debug('Starting task  %s in thread %d', self.name, get_ident())

        while self.ready:

            if self.action == _SHUTDOWNTASK:
                # shutdown the worker thread
                self.ready = False
                break
            try:
                self.action()
            except Exception as e:
                cls, e, tb = sys.exc_info()
                LOG.exception('Unhandled Error in thread:%s %s', get_ident(), e)
            self.suspend()

        self.event.clear()


class Chronos(object):

    """Schedule Mannager
    """

    def __init__(self, io_loop=None):
        """Init schedule instance

        Keyword Arguments:
            io_loop {IOLoop} - - the IOLoop instance(default: the tornado default ioloop instance)
        """
        # the tasks dict container
        self._tasks = {}
        # running status
        self.running = False
        self.io_loop = io_loop
        self.lock = threading.RLock()

    def schedule(self, name, timer, func, once=False, start=False, process=False, max_executor=5):
        """Adding task in schedule

        Arguments:
            name {string} - - uniqe task name,
            timer - - every timer object
            func - - the task function

        Keyword Arguments:
            once {bool} - - set True will run only once time(default: {False})
            start {bool} - - when chronos start and schedule a new task, 
            if set to True will add to Tornado IOLoop and schedule to run at time(default: {False})
            process {bool} - - if process is True, then the job will run in on a procees, 
            otherwise defaultly running in thread(default: {False})
            max_executor {number} - - the max threads(or processes) to run a task(default: {5})
        """
        with self.lock:

            if self.io_loop is None:
                raise ChronosError("Must call setup or set io_loop firstly.")

            if name in self._tasks:
                raise ChronosError("Task %s exists in the current chronos." % (name))

            task = Task(name, func, timer, self.io_loop, once, process, max_executor)

            self._tasks[name] = task

            if self.running and start:
                task.start()

    def remove_task(self, task_name):
        """Stop and remove the task from chronos

        Arguments:
            task_name {string} - - uniqe task name
        """
        with self.lock:
            task = self._tasks.pop(task_name, None)
            if task:
                task.stop(clear=True)

    def start_task(self, task_name):
        """Start the task from chronos

        Arguments:
            task_name {string} - - uniqe task name
        """
        with self.lock:
            task = self._tasks[task_name]
            if task:
                task.start()
            else:
                LOG.warning("Doesn't exists task : %s" % (task_name))

    def stop_task(self, task_name):
        """Stop task in ioloop

        If you use chronos in a tornado web server, 
        you can set start_ioloop to "False", then start your custom ioloop later.


        Arguments:
            task_name {[type]} -- [description]
        """
        self.io_loop.add_callback(self._stop_task, task_name)

    def _stop_task(self, task_name):
        with self.lock:
            task = self._tasks[task_name]
            if task:
                task.stop()
            else:
                LOG.warning("Doesn't exists task : %s" % (task_name))

    def start(self, start_ioloop=False):
        """Add tasks in ioloop

        If you use chronos in a tornado web server, you can set start_ioloop to "False", then start your custom ioloop later.

        Keyword Arguments:
            start_ioloop {bool} -- will start the ioloop if set to "True" (default: {False})
        """
        for _, task in self._tasks.items():
            task.start()
        self.running = True
        if start_ioloop:
            self.io_loop.start()

    def stop(self, stop_ioloop=False, clear=True):
        """Stop the chronos

        Keyword Arguments:
            stop_ioloop {bool} -- will stop the ioloop if set to "True" (default: {False})
            clear {bool} -- will remove tasks from chrons if set to "True" (default: {True})
        """
        self.io_loop.add_callback(self._stop, stop_ioloop, clear)

    def _stop(self, stop_ioloop=False, clear=True):
        if not self.running:
            return
        for _, task in self._tasks.items():
            task.stop(clear)

        if clear:
            self._tasks.clear()

        self.running = False
        if stop_ioloop:
            self.io_loop.stop()


class ChronosError(Exception):
    """Chronos Exception
    """
    pass

__chronos = Chronos()


def setup(io_loop=None):
    __chronos.io_loop = io_loop or tornado.ioloop.IOLoop.instance()


def schedule(name, timer, func, once=False, start=False, process=False, max_executor=5):
    __chronos.schedule(name, timer, func, once, start, process, max_executor)


def remove_task(task_name):
    __chronos.remove_task(task_name)


def start_task(task_name):
    __chronos.start_task(task_name)


def stop_task(task_name):
    __chronos.stop_task(task_name)


def start(start_ioloop=False):
    __chronos.start(start_ioloop)


def stop(stop_ioloop=False, clear=True):
    __chronos.stop(stop_ioloop, clear)

if __name__ == '__main__':

    import doctest
    doctest.testmod()
