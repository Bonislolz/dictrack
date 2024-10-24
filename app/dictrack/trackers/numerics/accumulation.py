# -*- coding: UTF-8 -*-

from dictor import dictor

from dictrack.trackers.numerics.numeric import NumericTracker
from dictrack.utils import logger
from dictrack.utils.utils import numeric, typecheck


class AccumulationTracker(NumericTracker):
    DEFAULT = "_THIS_IS_DEFAULT_VALUE"

    def __init__(self, name, conditions, target, key, *args, **kwargs):
        super(AccumulationTracker, self).__init__(
            name, conditions, target, *args, **kwargs
        )

        self._key = key

    def __eq__(self, other):
        return (
            self.target == other.target
            and self.conditions
            == other.conditions  # This will call __eq__ of the type set
            and self.group_id == other.group_id
            and self.name == other.name
            and self.key == other.key
        )

    def __repr__(self):
        content = "<AccumulationTracker (target={} conditions={} group_id={} name={} progress={} key={})>".format(
            self.target,
            self.conditions,
            self.group_id,
            self.name,
            self.progress,
            self.key,
        )

        if self.removed:
            return "[REMOVED] " + content
        elif self.completed:
            return "[COMPLETED] " + content
        else:
            return content

    @property
    def key(self):
        return self._key

    @typecheck()
    def _push_progress(self, data, *args, **kwargs):
        result = dictor(data, self.key, default=self.DEFAULT)
        if result == self.DEFAULT:
            logger.warning("key ({}) is not exists in data".format(self.key))

            return

        result = numeric(result, allow_empty=True)
        if result is None:
            logger.warning("key ({}) is None".format(self.key))

            return

        self._progress += result

    def __getstate__(self):
        state = super(AccumulationTracker, self).__getstate__()
        state["key"] = self.key

        return state

    def __setstate__(self, state):
        super(AccumulationTracker, self).__setstate__(state)
        self._key = state["key"]
