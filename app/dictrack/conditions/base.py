# -*- coding: UTF-8 -*-

from abc import ABCMeta, abstractmethod

import six


class BaseCondition(six.with_metaclass(ABCMeta)):
    DEFAULT = "_THIS_IS_DEFAULT_VALUE"

    @abstractmethod
    def __eq__(self, other):
        """_summary_

        :param `BaseCondition` other: _description_
        """

    @abstractmethod
    def __hash__(self):
        """_summary_"""

    @abstractmethod
    def __repr__(self):
        """_summary_"""

    @abstractmethod
    def __getstate__(self):
        """_summary_"""

    @abstractmethod
    def __setstate__(self, state):
        """_summary_"""

    @abstractmethod
    def check(self, data, *args, **kwargs):
        """_summary_

        :param _type_ data: _description_
        """
