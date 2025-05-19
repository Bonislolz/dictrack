# -*- coding: utf-8 -*-


import sys
import time
from datetime import timedelta
from os.path import abspath, dirname, join

import pytest
import six

sys.path.insert(0, abspath(join(dirname(__file__), "..")))
from dictrack.limiters.count import CountLimiter
from dictrack.limiters.time import TimeLimiter


class MockTracker(object):
    def __init__(self):
        self.dirtied = True
        self.completed = False


def test_count():
    limiter = CountLimiter(3)
    post_tracker = MockTracker()
    for _ in six.moves.range(3):
        limiter.post_track({}, post_tracker)
    assert limiter.limited is True

    assert limiter.reset() is True
    assert limiter.count == 3
    assert limiter.limited is False

    with pytest.raises(TypeError):
        CountLimiter("3")

    assert limiter.reset(reset_count=5) is True
    assert limiter.count == 5
    for _ in six.moves.range(5):
        limiter.post_track({}, post_tracker)
    assert limiter.limited is True

    assert limiter.reset(reset_count=0) is False
    assert limiter.count == limiter.remaining == 0
    assert limiter.limited is True

    with pytest.raises(ValueError):
        limiter.reset(reset_count=-1)

    limiter = CountLimiter(1)
    post_tracker = MockTracker()
    post_tracker.completed = True
    limiter.post_track({}, post_tracker)
    assert limiter.limited is False

    limiter = CountLimiter(2)
    post_tracker = MockTracker()
    limiter.post_track({}, post_tracker)
    assert limiter.limited is False

    limiter = CountLimiter(3)
    limiter2 = CountLimiter(3)
    assert limiter == limiter2

    set_limiters = set([limiter, limiter2])
    assert len(set_limiters) == 1


def test_time():
    limiter = TimeLimiter(interval=timedelta(seconds=1))
    time.sleep(2)
    limiter.pre_track({}, MockTracker())
    assert limiter.limited is True

    limiter = TimeLimiter(interval=timedelta(days=1))
    time.sleep(2)
    limiter.pre_track({}, MockTracker())
    assert limiter.limited is False

    limiter = TimeLimiter(end_ts=int(time.time()) + 1)
    time.sleep(2)
    limiter.pre_track({}, MockTracker())
    assert limiter.limited is True

    now_ts = int(time.time())
    limiter = TimeLimiter(start_ts=now_ts, end_ts=now_ts + 1)
    time.sleep(2)
    limiter.pre_track({}, MockTracker())
    assert limiter.limited is True

    now_ts = int(time.time())
    limiter = TimeLimiter(start_ts=now_ts, interval=timedelta(seconds=1))
    time.sleep(2)
    limiter.pre_track({}, MockTracker())
    assert limiter.limited is True

    assert limiter.reset() is True
    limiter.pre_track({}, MockTracker())
    assert limiter.limited is False

    now_ts = int(time.time())
    limiter = TimeLimiter(start_ts=now_ts - 86400 * 5, interval=timedelta(days=1))
    limiter.pre_track({}, MockTracker())
    assert limiter.limited is True

    assert limiter.reset() is True
    time.sleep(1)
    limiter.pre_track({}, MockTracker())
    assert limiter.limited is False

    now_ts = int(time.time())
    assert limiter.reset(now_ts=now_ts - 3600 * 12) is True
    limiter.pre_track({}, MockTracker())
    assert limiter.limited is False

    now_ts = int(time.time())
    assert limiter.reset(now_ts=now_ts + 2, reset_seconds=10) is False
    limiter.pre_track({}, MockTracker())
    assert limiter.limited is True
    time.sleep(3)
    limiter.pre_track({}, MockTracker())
    assert limiter.limited is False

    limiter = TimeLimiter(start_ts=int(time.time()) + 2, interval=timedelta(seconds=1))
    limiter.pre_track({}, MockTracker())
    assert limiter.limited is True

    with pytest.raises(TypeError):
        TimeLimiter(start_ts="100")
    with pytest.raises(TypeError):
        TimeLimiter(end_ts="100")
    with pytest.raises(TypeError):
        TimeLimiter(interval="100")

    with pytest.raises(ValueError):
        TimeLimiter(start_ts=now_ts)
    with pytest.raises(ValueError):
        TimeLimiter(end_ts=now_ts, interval=timedelta(seconds=1))
    with pytest.raises(ValueError):
        TimeLimiter(start_ts=now_ts, end_ts=now_ts)

    limiter = TimeLimiter(interval=timedelta(seconds=1))
    limiter2 = TimeLimiter(interval=timedelta(seconds=1))
    assert limiter == limiter2

    set_limiters = set([limiter, limiter2])
    assert len(set_limiters) == 1
