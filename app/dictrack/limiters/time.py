# -*- coding: UTF-8 -*-


from __future__ import absolute_import

import time
from datetime import timedelta
from logging import getLogger

import six

from dictrack.limiters.base import BaseLimiter
from dictrack.utils.utils import valid_type

logger = getLogger("dictrack.limiters.time")


class TimeLimiter(BaseLimiter):
    def __init__(self, start_ts=None, end_ts=None, interval=None):
        """
        A time-based limiter to control the duration within which actions are allowed.

        Attributes
        ----------
        start : int
            The start timestamp in seconds since the epoch.
        end : int
            The end timestamp in seconds since the epoch.
        interval : timedelta
            The duration of the limiter's active period.

        Parameters
        ----------
        start_ts : int, optional
            The start timestamp in seconds. Defaults to the current timestamp if `None`.
        end_ts : int, optional
            The end timestamp in seconds. Either `end_ts` or `interval` must be specified.
        interval : timedelta, optional
            Duration for which the limiter is active. Either `end_ts` or `interval` must be specified.

        Raises
        ------
        TypeError
            If `start_ts`, `end_ts`, or `interval` are of invalid types.
        ValueError
            If neither `end_ts` nor `interval` is specified, if both are specified, or if `start_ts` and `end_ts` are identical.
        Warning
            If `start_ts` is greater than `end_ts`, they are swapped to ensure logical order.
        """
        super(TimeLimiter, self).__init__()

        valid_type(start_ts, six.integer_types, allow_empty=True)
        valid_type(end_ts, six.integer_types, allow_empty=True)
        valid_type(interval, timedelta, allow_empty=True)

        if end_ts is None and interval is None:
            raise ValueError(
                "At least one of `end_ts`, or `interval` must be specified; "
                "otherwise, this limiter will have no effect."
            )

        if end_ts is not None and interval is not None:
            raise ValueError(
                "Only one of `end_ts` or `interval` can be specified, not both"
            )

        if start_ts is None:
            start_ts = int(time.time())

        # Use end_ts
        if end_ts is not None:
            if start_ts > end_ts:
                logger.warning("`start_ts` is greater than `end_ts`, swapping them")
                start_ts, end_ts = end_ts, start_ts

            interval = timedelta(seconds=end_ts - start_ts)
        # Use interval
        else:
            end_ts = start_ts + interval.seconds

        if start_ts == end_ts:
            raise ValueError(
                "`start_ts` and `end_ts` cannot be the same; "
                "having them equal will cause the limiter to always be in a limited state."
            )

        self.start = start_ts
        self.end = end_ts
        self.interval = interval

    def __eq__(self, other):
        return (
            self.start == other.start
            and self.end == other.end
            and self.interval == other.interval
        )

    def __hash__(self):
        start_hash = hash(self.start)
        end_hash = hash(self.end)
        interval_hash = hash(self.interval)

        return hash(str(start_hash) + str(end_hash) + str(interval_hash))

    def __repr__(self):
        return "<TimeLimiter (start={} end={} interval={})>".format(
            self.start, self.end, self.interval
        )

    def pre_track(self, data, pre_tracker, *args, **kwargs):
        now_ts = int(time.time()) if "now_ts" not in kwargs else kwargs["now_ts"]

        if not (self.start <= now_ts <= self.end):
            self.limited = True

            return False

        return True

    def reset(self, *args, **kwargs):
        super(TimeLimiter, self).reset()

        now_ts = int(time.time()) if "now_ts" not in kwargs else kwargs["now_ts"]
        delta_seconds = (
            self.interval.seconds
            if "reset_seconds" not in kwargs
            else kwargs["reset_seconds"]
        )

        self.interval = timedelta(seconds=delta_seconds)
        self.start = now_ts
        self.end = now_ts + delta_seconds
