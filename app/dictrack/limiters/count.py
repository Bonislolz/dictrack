# -*- coding: UTF-8 -*-

from __future__ import absolute_import

import six

from dictrack.limiters.base import BaseLimiter
from dictrack.utils.utils import valid_type


class CountLimiter(BaseLimiter):
    def __init__(self, count):
        """
        A limiter based on a specified count, tracking the number of remaining allowed operations.

        Attributes
        ----------
        count : int
            The maximum number of allowed operations.
        remaining : int
            The number of operations left before reaching the limit.

        Parameters
        ----------
        count : int
            The maximum number of allowed operations or actions. Must be a positive non-zero integer.

        Raises
        ------
        TypeError
            If `count` is not of an integer type.
        ValueError
            If `count` is not a positive non-zero integer.
        """
        super(CountLimiter, self).__init__()

        valid_type(count, six.integer_types)

        if count <= 0:
            raise ValueError("`count` must be a positive non-zero integer")

        self.count = self.remaining = count

    def __eq__(self, other):
        return self.count == other.count

    def __hash__(self):
        return hash(self.count)

    def __repr__(self):
        return "<CountLimiter (count={})>".format(self.count)

    def post_track(self, data, post_tracker, *args, **kwargs):
        self.remaining -= 1

        if self.remaining <= 0 and post_tracker.dirtied and not post_tracker.completed:
            self.limited = True

            return False

        return True

    def reset(self, *args, **kwargs):
        super(CountLimiter, self).reset()

        self.remaining = self.count
