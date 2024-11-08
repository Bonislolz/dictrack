# -*- coding: UTF-8 -*-

from logging import getLogger

import six
from dictor import dictor

from dictrack.trackers.base import ResetPolicy
from dictrack.trackers.numerics.numeric import NumericTracker
from dictrack.utils.utils import numeric, typecheck, valid_type

logger = getLogger("dictrack.trackers.numerics.accumulation")


class AccumulationTracker(NumericTracker):
    DEFAULT = "_THIS_IS_DEFAULT_VALUE"

    def __init__(
        self,
        name,
        conditions,
        target,
        key,
        group_id=None,
        limiters=None,
        reset_policy=ResetPolicy.DEFAULT,
        loop_forever=False,
        *args,
        **kwargs
    ):
        """
        A tracker that accumulates progress based on a specific key's value in incoming data.

        Attributes
        ----------
        DEFAULT : str
            Default placeholder value when the key is not found in data.

        Parameters
        ----------
        name : str
            Name of the tracker.
        conditions : iterable of BaseCondition
            Conditions that must be met for progress to be tracked.
        target : int, float, list, or tuple
            The target value(s) for the tracker.
        key : str
            The key in incoming data used to accumulate progress.
        group_id : str, optional
            ID of the group to which the tracker belongs. Defaults to `BaseTracker.DEFAULT_GROUP_ID`.
        limiters : iterable of BaseLimiter, optional
            Limiters applied to the tracker. Defaults to an empty set if not provided.
        reset_policy : int, optional
            Policy defining conditions under which progress resets. Defaults to `ResetPolicy.DEFAULT`.
        loop_forever : bool, optional
            If `True`, tracker loops through targets indefinitely. Defaults to `False`.
        *args : tuple
            Additional positional arguments.
        **kwargs : dict
            Additional keyword arguments.

        Raises
        ------
        ValueError
            If `key` is not a string.
        """
        super(AccumulationTracker, self).__init__(
            name,
            conditions,
            target,
            group_id=group_id,
            limiters=limiters,
            reset_policy=reset_policy,
            loop_forever=loop_forever,
            *args,
            **kwargs
        )

        valid_type(key, six.string_types)
        self._key = key

    def __eq__(self, other):
        valid_type(other, AccumulationTracker)
        super_eq = super(AccumulationTracker, self).__eq__(other)
        return super_eq and self.key == other.key

    def __repr__(self):
        content = "<AccumulationTracker (target={} conditions={} limiters={} group_id={} name={} progress={} key={})>".format(
            self.target,
            self.conditions,
            self.limiters,
            self.group_id,
            self.name,
            self.progress,
            self.key,
        )

        if self.removed:
            return "[REMOVED] " + content
        elif self.completed:
            return "[COMPLETED] " + content
        elif self.limited:
            return "[LIMITED] " + content
        else:
            return content

    def __getstate__(self):
        state = super(AccumulationTracker, self).__getstate__()
        state["key"] = self.key

        return state

    def __setstate__(self, state):
        super(AccumulationTracker, self).__setstate__(state)
        self._key = state["key"]

    @property
    def key(self):
        return self._key

    @typecheck()
    def _push_progress(self, data, *args, **kwargs):
        result = dictor(data, self.key, default=self.DEFAULT)
        if result == self.DEFAULT:
            logger.warning("`key` ({}) is not exists in data".format(self.key))

            return

        result = numeric(result, allow_empty=True)
        if result is None:
            logger.warning("`key` ({}) is None".format(self.key))

            return

        self._progress += result
