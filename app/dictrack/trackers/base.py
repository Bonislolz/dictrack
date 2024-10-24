# -*- coding: UTF-8 -*-

from abc import ABCMeta, abstractmethod
from collections import defaultdict

import six

from dictrack.conditions import BaseCondition
from dictrack.events import (
    EVENT_ALL,
    EVENT_TRACKER_COMPLETED,
    EVENT_TRACKER_MODIFIED,
    EVENT_TRACKER_RESET,
    BaseEvent,
    TrackerEvent,
)
from dictrack.utils.errors import (
    GroupIdAlreadySetError,
    GroupIdDuplicateSetError,
    TrackerAlreadyCompletedError,
    TrackerAlreadyRemovedError,
)
from dictrack.utils.logger import logger
from dictrack.utils.utils import (
    typecheck,
    valid_callable,
    valid_obj,
    valid_type,
)


# Only dispatch completed, reset and modified event
class BaseTracker(six.with_metaclass(ABCMeta)):
    DEFAULT_GROUP_ID = "_THIS_IS_DEFAULT_GID"

    def __init__(self, name, conditions, target, group_id=None, *args, **kwargs):
        self._name = name
        self._conditions = set(conditions)
        self._target = target
        self._group_id = (
            group_id if group_id is not None else BaseTracker.DEFAULT_GROUP_ID
        )

        self._progress = 0
        self._completed = False
        self._removed = False
        self._dirtied = False
        self._listeners = defaultdict(list)

    def __getstate__(self):
        # Serialize conditions
        serialized_conditions = []
        for condition in self.conditions:
            serialized_conditions.append(condition.__getstate__())

        return {
            "cls": self.__class__,
            "name": self.name,
            "conditions": serialized_conditions,
            "target": self.target,
            "group_id": self.group_id,
            "progress": self.progress,
            "completed": self.completed,
            "removed": self.removed,
        }

    def __setstate__(self, state):
        # Deserialize conditions
        conditions = []
        for condition_state in state["conditions"]:
            condition = condition_state["cls"].__new__(condition_state["cls"])
            condition.__setstate__(condition_state)
            conditions.append(condition)

        self._name = state["name"]
        self._conditions = set(conditions)
        self._target = state["target"]
        self._group_id = state["group_id"]
        self._progress = state["progress"]
        self._completed = state["completed"]
        self._removed = state["removed"]
        self._dirtied = False
        self._listeners = defaultdict(list)

    @property
    def name(self):
        return self._name

    @property
    def conditions(self):
        return self._conditions

    @property
    def target(self):
        return self._target

    @property
    def group_id(self):
        return self._group_id

    @group_id.setter
    def group_id(self, value):
        valid_type(value, six.string_types)

        if self.group_id == value:
            raise GroupIdDuplicateSetError(self.group_id)

        if self.group_id != BaseTracker.DEFAULT_GROUP_ID:
            raise GroupIdAlreadySetError(self.group_id, value)

        self._group_id = value

    @property
    def completed(self):
        return self._completed

    @property
    def removed(self):
        return self._removed

    @removed.setter
    def removed(self, value):
        valid_type(value, bool)

        if self._removed:
            raise TrackerAlreadyRemovedError(self.group_id, self.name)

        self._removed = value

    @property
    def dirtied(self):
        return self._dirtied

    @dirtied.setter
    def dirtied(self, value):
        valid_type(value, bool)

        self._dirtied = value

    @property
    def progress(self):
        return self._progress

    @typecheck()
    def track(self, data, *args, **kwargs):
        if self.removed:
            raise TrackerAlreadyRemovedError(self.group_id, self.name)

        if self.completed:
            raise TrackerAlreadyCompletedError(self.group_id, self.name)

        if self.dirtied:
            logger.warning(
                "this tracker ({} - {}) has been modified, make sure data has "
                "already been stored to data store".format(self.group_id, self.name)
            )

        cache = kwargs.get("cache", {})
        for condition in self.conditions:
            # Using cache and cache result is False, early return
            if cache and condition in cache and not cache[condition]:
                break
            # No cache
            else:
                # Store to cache
                cache[condition] = condition.check(data, *args, **kwargs)

                # Condition result is False, early return
                if not cache[condition]:
                    break
        # All conditions passed
        else:
            self._dirtied = True
            self._push_progress(data, *args, **kwargs)
            self._dispatch_event(
                TrackerEvent(EVENT_TRACKER_MODIFIED, self.group_id, self.name, self)
            )
            self._check_progress()

    def add_listener(self, code, cb):
        valid_obj(code, EVENT_ALL)
        valid_callable(cb)

        self._listeners[code].append(cb)

    def reset(self):
        if self.removed:
            raise TrackerAlreadyRemovedError(self.group_id, self.name)

        self._progress = 0
        self._completed = False

        self._dispatch_event(
            TrackerEvent(EVENT_TRACKER_RESET, self.group_id, self.name, self)
        )

    def _validate(self, name, conditions):
        valid_type(name, six.string_types)

        if not conditions:
            raise ValueError("Conditions must include at least one condition.")

        if not all(isinstance(c, BaseCondition) for c in conditions):
            raise TypeError("Conditions must contain instances of BaseCondition")

    @abstractmethod
    def _push_progress(self, data, *args, **kwargs):
        """_summary_

        :param _type_ data: _description_
        :return _type_: _description_
        """

    @abstractmethod
    def _check_progress(self):
        """_summary_

        :return _type_: _description_
        """

    def _complete(self):
        if self.removed:
            raise TrackerAlreadyRemovedError(self.group_id, self.name)

        self._completed = True

        self._dispatch_event(
            TrackerEvent(EVENT_TRACKER_COMPLETED, self.group_id, self.name, self)
        )

    def _dispatch_event(self, event):
        valid_type(event, BaseEvent)

        for cb in self._listeners[event.code]:
            try:
                cb(event)
            except Exception as e:
                logger.exception(
                    "notify listener ({}) failed, {}".format(cb.__name__, e)
                )
