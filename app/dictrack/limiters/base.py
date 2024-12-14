# -*- coding: UTF-8 -*-


from abc import ABCMeta

import six


class BaseLimiter(six.with_metaclass(ABCMeta)):
    def __init__(self):
        self.limited = False

    def pre_track(self, data, pre_tracker, *args, **kwargs):
        """"""
        return True

    def post_track(self, data, post_tracker, *args, **kwargs):
        """"""
        return True

    def reset(self, *args, **kwargs):
        """"""
        self.limited = False
