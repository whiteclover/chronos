#!/usr/bin/env python

import datetime
import unittest

from chronos import every_second, every_at, every
import chronos


class StubDate1(datetime.datetime):

    @classmethod
    def now(cls):
        return cls(2015, 3, 1, 0, 0, 0)


class StubDate2(datetime.datetime):

    @classmethod
    def now(cls):
        return cls(2015, 5, 1, 6, 15, 0)


class StubDatetime(object):

    def __init__(self, new_datetime):
        self.old_datetime = datetime.datetime
        self.new_datetime_cls = new_datetime

    def __enter__(self):
        datetime.datetime = self.new_datetime_cls
        setattr(chronos, 'datetime', datetime.datetime)
        return self

    def __exit__(self, type, value, traceback):
        datetime.datetime = self.old_datetime
        setattr(chronos, 'datetime', self.old_datetime)


def current(t):
    return datetime.datetime.now() + t


class EveryTest(unittest.TestCase):

    def test_builtin_timer_second(self):
        assert every_second(2).next().total_seconds() == 2
        assert every_second(3600).next().total_seconds() == 3600

    def test_builtin_timer_at1(self):
        with StubDatetime(StubDate1):
            timer = every_at(minute=10, second=0)
            # First time
            delay1 = timer.next().total_seconds()
            assert delay1 == 10 * 60, 'Actual %s' % str(delay1)
            assert timer.next().total_seconds() == 60 * 60

    def test_builtin_timer_at2(self):
        with StubDatetime(StubDate1):
            timer = every_at(hour=1, minute=10, second=0)
            # First time
            delay1 = timer.next().total_seconds()
            assert delay1 == 60 * 60 + 10 * 60, 'Actual %s' % str(delay1)
            assert timer.next().total_seconds() == 24 * 60 * 60


class EveryTests(unittest.TestCase):

    def test_time_units(self):
        assert every().seconds.unit == 'seconds'
        assert every().minutes.unit == 'minutes'
        assert every().hours.unit == 'hours'
        assert every().days.unit == 'days'
        assert every().weeks.unit == 'weeks'

    def test_singular_time_units_match_plural_units(self):
        assert every().second.unit == every().seconds.unit
        assert every().minute.unit == every().minutes.unit
        assert every().hour.unit == every().hours.unit
        assert every().day.unit == every().days.unit
        assert every().week.unit == every().weeks.unit

    def test_at_time(self):
        assert current(every().day.at('10:30').next()).hour == 10
        assert current(every().day.at('10:30').next()).minute == 30

    def test_at_time_hour(self):
        with StubDatetime(StubDate2):
            assert current(every().hour.at(':30').next()).hour == 6
            assert current(every().hour.at(':30').next()).minute == 30
            assert current(every().hour.at(':10').next()).hour == 7
            assert current(every().hour.at(':10').next()).minute == 10
            assert current(every().hour.at(':00').next()).hour == 7
            assert current(every().hour.at(':00').next()).minute == 0

    def test_next_time(self):
        with StubDatetime(StubDate2):
            assert current(every().minute.next()).minute == 16
            assert current(every(5).minutes.next()).minute == 20
            assert current(every().hour.next()).hour == 7
            assert current(every().day.next()).day == 2
            assert current(every().day.at('04:00').next()).day == 2
            assert current(every().day.at('12:30').next()).day == 1

            assert current(every().week.next()).day == 8
            assert current(every().monday.next()).day == 4
            assert current(every().tuesday.next()).day == 5
            assert current(every().wednesday.next()).day == 6
            assert current(every().thursday.next()).day == 7
            assert current(every().friday.next()).day == 8
            assert current(every().saturday.next()).day == 2
            assert current(every().sunday.next()).day == 3



import os

def test_proc(word="hello chronos"):
    LOG.info("%s :%s" % ,word, os.getpid())        

class ChronosTest(unittest.TestCase):

    def setUp(self):
        chronos.setup()

    def tearDown(self):
        chronos.stop(True)

    def test_schedule_thread(self):
        import threading
        lock = threading.Lock()
        def say(word="hello chronos"):
            LOG.info("%s: %d" % (word, say.count))
            with lock:
                if say.count == 5:
                    chronos.remove_task('say2')
                    chronos.stop(True)
                else:
                    say.count += 1
        say.count = 1

        def say2(word):
            LOG.info("%s: %d" % (word, say.count))

        chronos.schedule('say', every_second(1), lambda: say("test"))
        chronos.schedule('say2', every_second(1), lambda: say2("test2"))
        chronos.start(True)

        assert say.count == 5


    def test_schedule_process(self):
        import threading
        lock = threading.Lock()
        def say(word="hello chronos"):
            LOG.info("%s: %d" % (word, say.count))
            with lock:
                if say.count == 5:
                    chronos.stop(True)
                else:
                    say.count += 1
        say.count = 1


        chronos.schedule('stop', every_second(1), lambda: say("test"))
        chronos.schedule('test_proc', every_second(1), test_proc, process=True)
        chronos.start(True)
        assert say.count == 5


    def test_schedule_once(self):

        import threading
        lock = threading.Lock()
        def say(word="hello chronos"):
            LOG.info("%s: %d" % (word, say.count))
            with lock:
                if say.count == 5:
                    chronos.stop(True)
                else:
                    say.count += 1
        say.count = 1



        chronos.schedule('test_proc', every_second(1), test_proc, once=True, process=True)
        chronos.schedule('test_thread', every_second(1), lambda:test_proc("once thread"), once=True, process=False)
        chronos.schedule('stop', every_second(2), lambda: say("test"))
        chronos.start(True)
        assert say.count == 5


if __name__ == '__main__':
    

    global LOG

    import logging
    import time 


    debug = True
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level,
                            format='%(asctime)s %(levelname)-8s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', filemode='a+')
    LOG = logging.getLogger("test")

    unittest.main()
