# -*- coding: utf-8 -*-

import copy
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from logging import getLogger

import six

from dictrack.conditions.base import BaseCondition
from dictrack.events import (
    EVENT_ALL,
    EVENT_TRACKER_ALL_COMPLETED,
    EVENT_TRACKER_LIMITED,
    EVENT_TRACKER_RESET,
    EVENT_TRACKER_STAGE_COMPLETED,
    BaseEvent,
    LimitedTrackerEvent,
    TrackerEvent,
)
from dictrack.limiters.base import BaseLimiter
from dictrack.utils.errors import (
    GroupIdAlreadySetError,
    GroupIdDuplicateSetError,
    TrackerAlreadyCompletedError,
    TrackerAlreadyRemovedError,
)
from dictrack.utils.utils import (
    typecheck,
    valid_callable,
    valid_elements_type,
    valid_obj,
    valid_type,
)

try:
    import cPickle as pickle  # type: ignore
except ImportError:
    import pickle


logger = getLogger("dictrack.trackers.base")


class ResetPolicy(object):
    NONE = 0
    PROGRESS = 1
    LIMITER = 2
    ALL = PROGRESS | LIMITER
    DEFAULT = LIMITER


class BaseTracker(six.with_metaclass(ABCMeta)):
    DEFAULT_GROUP_ID = "_THIS_IS_DEFAULT_GID"

    def __init__(
        self,
        name,
        conditions,
        target,
        group_id=None,
        limiters=None,
        reset_policy=ResetPolicy.DEFAULT,
        loop_forever=False,
        *args,
        **kwargs
    ):
        """
        A base class for tracking data and maintaining progress based on conditions, limiters, and targets.

        Attributes
        ----------
        DEFAULT_GROUP_ID : str
            Default group ID used when none is specified.

        Parameters
        ----------
        name : str
            Name of the tracker.
        conditions : iterable of BaseCondition
            Conditions that must be met for progress to be tracked.
        target : int, float, list, or tuple
            The target(s) the tracker aims to achieve.
        group_id : str, optional
            ID of the group to which the tracker belongs. Defaults to `DEFAULT_GROUP_ID`.
        limiters : iterable of BaseLimiter, optional
            Limiters applied to the tracker. Defaults to an empty set if not provided.
        reset_policy : int, optional
            Policy defining the conditions under which progress resets. Defaults to `ResetPolicy.DEFAULT`.
            Supports bitwise combination using `|` to apply multiple reset policies simultaneously
            (e.g., `ResetPolicy.PROGRESS | ResetPolicy.LIMITER`).
        loop_forever : bool, optional
            Whether the tracker loops indefinitely through targets. Defaults to `False`.
        *args : tuple
            Additional positional arguments.
        **kwargs : dict
            Additional keyword arguments.

        Raises
        ------
        ValueError
            If any attribute fails validation.
        """
        self._validate(
            name, conditions, target, group_id, limiters, reset_policy, loop_forever
        )

        # Required
        self._name = name
        self._conditions = set(conditions)
        self._init_target(target)

        # Optional
        self._group_id = (
            group_id if group_id is not None else BaseTracker.DEFAULT_GROUP_ID
        )
        self._limiters = set(limiters) if limiters is not None else set()
        self._reset_policy = reset_policy
        self._loop_forever = loop_forever

        # Private
        self._progress = 0
        self._completed = False
        self._removed = False
        self._dirtied = (
            False  # Indicate whether tracker had been modified since initialization
        )
        self._limited = False  # Indicate whether limiter is limited
        self._listeners = defaultdict(list)

    def __eq__(self, other):
        valid_type(other, BaseTracker)
        return (
            self.name == other.name
            and self.conditions == other.conditions
            and self.limiters == other.limiters
            and self.target == other.target
            and self.multi_target == other.multi_target
            and self.current_stage == other.current_stage
            and self.group_id == other.group_id
            and self.progress == other.progress
            and self.completed == other.completed
            and self.removed == other.removed
            and self.dirtied == other.dirtied
            and self.limited == other.limited
            and self._listeners == other._listeners
            and self.loop_forever == other.loop_forever
            and self.reset_policy == other.reset_policy
        )

    def __getstate__(self):
        # Serialize conditions
        serialized_conditions = []
        for condition in self.conditions:
            serialized_conditions.append(condition.__getstate__())

        return {
            "cls": self.__class__,
            "name": self.name,
            "conditions": serialized_conditions,
            "limiters": self.limiters,
            "target": self.target,
            "multi_target": self.multi_target,
            "current_stage": self.current_stage,
            "group_id": self.group_id,
            "progress": self.progress,
            "completed": self.completed,
            "removed": self.removed,
            "limited": self.limited,
            "reset_policy": self.reset_policy,
            "loop_forever": self.loop_forever,
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
        self._limiters = state["limiters"]
        self._target = state["target"]
        self._multi_target = state["multi_target"]
        self._current_stage = state["current_stage"]
        self._group_id = state["group_id"]
        self._progress = state["progress"]
        self._completed = state["completed"]
        self._removed = state["removed"]
        self._limited = state["limited"]
        self._dirtied = False
        self._listeners = defaultdict(list)
        self._reset_policy = state["reset_policy"]
        self._loop_forever = state["loop_forever"]

    @property
    def name(self):
        return self._name

    @property
    def conditions(self):
        return self._conditions

    @property
    def limiters(self):
        return self._limiters

    @property
    def reset_policy(self):
        return self._reset_policy

    @reset_policy.setter
    def reset_policy(self, value):
        valid_obj(value, list(six.moves.range(ResetPolicy.ALL + 1)))
        self._reset_policy = value

    @property
    def target(self):
        return self._target

    @property
    def multi_target(self):
        return self._multi_target

    @property
    def current_stage(self):
        return self._current_stage

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
    def limited(self):
        return self._limited

    @property
    def progress(self):
        return self._progress

    @property
    def loop_forever(self):
        return self._loop_forever

    @loop_forever.setter
    def loop_forever(self, value):
        valid_type(value, bool)
        self._loop_forever = value

    @typecheck()
    def track(self, data, *args, **kwargs):
        if self.removed:
            raise TrackerAlreadyRemovedError(self.group_id, self.name)

        if self.completed:
            raise TrackerAlreadyCompletedError(self.group_id, self.name)

        if self.dirtied:
            logger.warning(
                "This tracker ({} - {}) had been modified, make sure data has "
                "already been stored to data store".format(self.group_id, self.name)
            )

        if self.limited:
            logger.debug(
                "This tracker's ({} - {}) limiter is limited, check `limiters` for more details.".format(
                    self.group_id, self.name
                )
            )
            return

        # Pre-track limiter check procedure
        for limiter in self.limiters:
            if not limiter.pre_track(data, self, *args, **kwargs):
                self._limited = True
                self._dirtied = True
                self._dispatch_event(
                    LimitedTrackerEvent(
                        EVENT_TRACKER_LIMITED, self.group_id, self.name, self, limiter
                    )
                )

        if self.limited:
            return

        self._do_track(data, *args, **kwargs)

        # Post-track limiter check procedure
        for limiter in self.limiters:
            if not limiter.post_track(data, self, *args, **kwargs):
                self._limited = True
                self._dirtied = True
                self._dispatch_event(
                    LimitedTrackerEvent(
                        EVENT_TRACKER_LIMITED, self.group_id, self.name, self, limiter
                    )
                )

    def add_listener(self, code, cb):
        valid_obj(code, EVENT_ALL)
        valid_callable(cb)

        self._listeners[code].append(cb)

    def forward_event(self, cb):
        valid_callable(cb)

        for code in EVENT_ALL:
            self.add_listener(code, cb)

    def reset(self, reset_policy=None):
        valid_obj(
            reset_policy, list(six.moves.range(ResetPolicy.ALL + 1)), allow_empty=True
        )

        if self.removed:
            raise TrackerAlreadyRemovedError(self.group_id, self.name)

        if reset_policy is None:
            reset_policy = self.reset_policy

        if ResetPolicy.PROGRESS & reset_policy:
            self._progress = 0
        if ResetPolicy.LIMITER & reset_policy:
            for limiter in self.limiters:
                limiter.reset()

            self._limited = False

        self._completed = False

        self._dispatch_event(
            TrackerEvent(EVENT_TRACKER_RESET, self.group_id, self.name, self)
        )

    def _validate(
        self, name, conditions, target, group_id, limiters, reset_policy, loop_forever
    ):
        valid_type(name, six.string_types)
        valid_elements_type(conditions, BaseCondition)
        valid_type(target, (six.integer_types, float, list, tuple))
        valid_type(group_id, six.string_types, allow_empty=True)
        valid_elements_type(limiters, BaseLimiter, allow_empty=True)
        valid_obj(reset_policy, list(six.moves.range(ResetPolicy.ALL + 1)))
        valid_type(loop_forever, bool)

    def _init_target(self, target):
        self._current_stage = 0
        self._multi_target = target if isinstance(target, (list, tuple)) else [target]
        self._target = self._get_new_target()

    def _get_new_target(self):
        new_target = self._multi_target.pop(0) if self._multi_target else None
        # Move to next stage target
        if new_target is not None:
            self._current_stage += 1
        # Activate loop forever
        elif new_target is None and self.loop_forever:
            new_target = self.target

        # All stage targets are completed
        return new_target

    def _do_track(self, data, *args, **kwargs):
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
            self._check_progress()

    @abstractmethod
    def _push_progress(self, data, *args, **kwargs):
        """Implement for pushing progress updates with given data.

        Parameters
        ----------
        `data` : `dict`
            Data required for updating the progress (description of what the data represents).
        `*args` : `tuple`, optional
            Additional positional arguments for extended functionality.
        `**kwargs` : `dict`, optional
            Additional keyword arguments for further customization.
        """

    @abstractmethod
    def _check_progress(self):
        """Implement for checking the current progress status."""

    def _complete(self):
        if self.removed:
            raise TrackerAlreadyRemovedError(self.group_id, self.name)

        # Only for event
        snapshot_tracker = copy.deepcopy(self)
        snapshot_tracker._completed = True

        # Change to next stage target
        new_target = self._get_new_target()
        # All stage targets are completed
        if new_target is None:
            event_code = EVENT_TRACKER_ALL_COMPLETED
            self._completed = True
        # Move to next stage target
        else:
            event_code = EVENT_TRACKER_STAGE_COMPLETED
            self._target = new_target
            self.reset()

        self._dispatch_event(
            TrackerEvent(
                event_code,
                snapshot_tracker.group_id,
                snapshot_tracker.name,
                snapshot_tracker,
            )
        )

    def _dispatch_event(self, event):
        valid_type(event, BaseEvent)

        for cb in self._listeners[event.code]:
            try:
                cb(event)
            except Exception as e:
                logger.exception(
                    "Notify listener ({}) failed, {}".format(cb.__name__, e)
                )

    @staticmethod
    @typecheck()
    def serialize(tracker):
        """
        Serialize tracker for storing to datasource.

        :param `BaseTracker` tracker: The tracker instance to be serialized.
        """
        return pickle.dumps(tracker.__getstate__(), protocol=2)

    @staticmethod
    @typecheck()
    def deserialize(b_tracker):
        """
        Deserialize a byte stream into a tracker.

        :param `bytes` b_tracker: The byte stream representing the serialized tracker.
        :return: The deserialized tracker instance.
        :rtype: `BaseTracker`
        """
        state = pickle.loads(b_tracker)
        tracker = state["cls"].__new__(state["cls"])
        tracker.__setstate__(state)

        return tracker

    @staticmethod
    def deserialize_list(b_trackers):
        """
        Deserialize a list of byte streams into a list of trackers.

        :param `list[bytes]` b_trackers: A list of byte streams representing serialized trackers.
        :return: A list of deserialized tracker instances.
        :rtype: `list[BaseTracker]`
        """
        valid_type(b_trackers, (list, tuple))
        return [BaseTracker.deserialize(b_tracker) for b_tracker in b_trackers]
