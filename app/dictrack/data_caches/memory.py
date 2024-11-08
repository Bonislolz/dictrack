# -*- coding: utf-8 -*-

import copy
import time
from collections import defaultdict
from logging import getLogger
from threading import RLock

import six
from apscheduler.schedulers.background import BackgroundScheduler
from sortedcontainers import SortedDict

from dictrack.data_caches.base import BaseDataCache
from dictrack.utils.errors import ConflictingNameError
from dictrack.utils.utils import typecheck, valid_type

logger = getLogger("dictrack.data_caches.memory")


class MemoryDataCache(BaseDataCache):
    def __init__(
        self,
        scheduler_class=BackgroundScheduler,
        check_interval=60 * 30,
        stale_threshold=60 * 60 * 6,
    ):
        """
        A memory-based data cache with methods for caching, retrieving, and tracking in-memory data.
        STANDALONE ONLY!!!

        Parameters
        ----------
        scheduler_class : type, optional
            The scheduler class for periodic tasks. Defaults to `BackgroundScheduler`.
        check_interval : int, optional
            Interval in seconds for checking stale data. Defaults to `60 * 30`.
        stale_threshold : int, optional
            Threshold in seconds beyond which data is considered stale. Defaults to `60 * 60 * 6`.
        """
        super(MemoryDataCache, self).__init__(
            scheduler_class, check_interval, stale_threshold
        )

        self._group_pool = defaultdict(defaultdict)
        self._last_cache_accessed = InMemoryZSet()
        self._memory_lock = RLock()

    @typecheck()
    def cache(self, group_id, tracker, force=False, **kwargs):
        # Tracker already exists in the group
        if not force and tracker.name in self._group_pool[group_id]:
            raise ConflictingNameError(group_id, tracker.name)

        with self._memory_lock:
            tracker.forward_event(self.forward_cb)
            self._group_pool[group_id][tracker.name] = tracker
            self._last_cache_accessed.add(group_id, int(time.time()))

        return tracker

    @typecheck()
    def cache_all(self, group_id, trackers, force=False, **kwargs):
        added_trackers = []
        for tracker in trackers:
            try:
                tracker = self.cache(group_id, tracker)
            except ConflictingNameError as e:
                logger.debug(
                    "Tracker already cached, skip this one, {}".format(e.__repr__())
                )
            except Exception as e:
                logger.exception(
                    "Cache tracker failed, abort this one, {}".format(e.__repr__())
                )

            added_trackers.append(tracker)

        return added_trackers

    @typecheck()
    def fetch(self, group_id, name=None, **kwargs):
        valid_type(name, six.string_types + (list,), allow_empty=True)

        # Not found group by the id
        if group_id not in self._group_pool:
            return []

        # Specified one data
        if isinstance(name, six.string_types):
            return [copy.deepcopy(self._group_pool[group_id][name])]
        # All data
        elif name is None:
            return list(six.itervalues(self._group_pool[group_id]))
        # Specified multi data
        else:
            trackers = [
                copy.deepcopy(self._group_pool[group_id][n])
                for n in name
                if n in self._group_pool[group_id]
            ]
            return trackers

    @typecheck()
    def is_cached(self, group_id, name=None, **kwargs):
        valid_type(name, six.string_types, allow_empty=True)

        # Not found group by the id
        if group_id not in self._group_pool:
            return False

        if name is not None:
            return name in self._group_pool[group_id]

        # Found cache by the group id and name
        return True

    @typecheck()
    def remove(self, group_id, name=None, **kwargs):
        valid_type(name, six.string_types + (list,), allow_empty=True)

        removed_trackers = self.fetch(group_id, name=name)
        if not removed_trackers:
            return []

        with self._memory_lock:
            # Specified one data
            if isinstance(name, six.string_types):
                del self._group_pool[group_id][removed_trackers.pop().name]

                if not self._group_pool[group_id]:
                    del self._group_pool[group_id]
                    self._last_cache_accessed.remove(group_id)
            # All data
            elif name is None:
                del self._group_pool[group_id]
                self._last_cache_accessed.remove(group_id)
            # Specified multi data
            else:
                for tracker in removed_trackers:
                    del self._group_pool[group_id][tracker.name]

        for tracker in removed_trackers:
            tracker.removed = True

        return removed_trackers

    def flush(self):
        with self._memory_lock:
            del self._group_pool
            self._group_pool = defaultdict(defaultdict)

            del self._last_cache_accessed
            self._last_cache_accessed = InMemoryZSet()

    @typecheck()
    def track(self, group_id, data, *args, **kwargs):
        dirtied_trackers, completed_trackers, limited_trackers = [], [], []
        conditions_cache = {}
        with self._memory_lock:
            self._last_cache_accessed.add(group_id, int(time.time()))
            for tracker in self.fetch(group_id):
                tracker.track(data, cache=conditions_cache, *args, **kwargs)

                # Limiter limited
                if tracker.limited:
                    limited_trackers.append(tracker)

                # No modification, pass
                if not tracker.dirtied:
                    continue

                dirtied_trackers.append(tracker)
                # Completed, execute removing process
                if tracker.completed:
                    completed_trackers.append(tracker)
                    self.remove(group_id, tracker.name)
                    self.data_store.remove(group_id, tracker.name)
                    tracker.removed = True
                # Modified, execute updating process
                else:
                    tracker.dirtied = False

        return dirtied_trackers, completed_trackers, limited_trackers

    def _check_stale(self):
        now_ts = int(time.time())
        with self._memory_lock:
            for group_id in self._last_cache_accessed.range_by_score(
                0, now_ts - self.stale_threshold
            ):
                self.data_store.store_all(group_id, self.fetch(group_id))
                self.remove(group_id)


class InMemoryZSet:
    def __init__(self):
        self._zset = SortedDict()
        self._member_score_map = {}

    def add(self, member, score):
        """Add a member with a score to the zset, updating if it already exists."""
        if member in self._member_score_map:
            old_score = self._member_score_map[member]
            self._zset[old_score].remove(member)
            if not self._zset[old_score]:
                del self._zset[old_score]

        if score not in self._zset:
            self._zset[score] = set()
        self._zset[score].add(member)
        self._member_score_map[member] = score

    def remove(self, member):
        """Remove a member from the zset."""
        if member in self._member_score_map:
            score = self._member_score_map.pop(member)
            self._zset[score].remove(member)
            if not self._zset[score]:
                del self._zset[score]

    def score(self, member):
        """Retrieve the score of a specific member."""
        return self._member_score_map.get(member)

    def range_by_score(self, min_score, max_score):
        """Retrieve members within the specified score range."""
        result = []
        for score in self._zset.irange(min_score, max_score):
            result.extend(self._zset[score])
        return result
