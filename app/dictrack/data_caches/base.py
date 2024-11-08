# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

import six
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from dictrack.utils.utils import typecheck


class BaseDataCache(six.with_metaclass(ABCMeta)):
    @typecheck()
    def __init__(
        self,
        scheduler_class=BackgroundScheduler,
        check_interval=60 * 30,
        stale_threshold=60 * 60 * 6,
    ):
        self.check_interval = check_interval
        self.stale_threshold = stale_threshold

        self.scheduler = scheduler_class()
        self.scheduler.add_job(
            self._check_stale, IntervalTrigger(seconds=self.check_interval)
        )

        self.data_store = None
        self.forward_cb = None

    def start_scheduler(self):
        self.scheduler.start()

    @abstractmethod
    def cache(self, group_id, tracker, force=False, **kwargs):
        """Implement for storing a single data item under the specified
        `group_id` in the data cache.
        """

    @abstractmethod
    def cache_all(self, group_id, trackers, force=False, **kwargs):
        """Implement for storing multiple data items under the specified
        `group_id` in the data cache.
        """

    @abstractmethod
    def fetch(self, group_id, name=None, **kwargs):
        """Implement for retrieving data from the cache under the specified
        `group_id`.
        If `name` is None, retrieve all data under `group_id`;
        if `name` is provided, retrieve only the specified data.
        """

    @abstractmethod
    def is_cached(self, group_id, name=None, **kwargs):
        """Implement for checking if data exists in the data cache.
        If `name` is None, checks all data under `group_id`;
        if `name` is provided, checks only the specified data.
        """

    @abstractmethod
    def remove(self, group_id, name=None, **kwargs):
        """Implement for removing data from the data cache.
        If `name` is None, removes all data under `group_id`;
        if `name` is provided, removes only the specified data.
        """

    @abstractmethod
    def flush(self):
        """Implement for clearing all data from the data cache."""

    @abstractmethod
    def track(self, group_id, data, *args, **kwargs):
        """Implement for tracking and updating the cache with the specified
        data under the given `group_id`.
        Ensure proper handling of race conditions in a distributed architecture,
        for example, by using a distributed lock.
        """

    @abstractmethod
    def _check_stale(self):
        """Implement for checking if there are expired data in the cache.
        Executes the check every `self.check_interval` seconds; if data exceeds
        `self.stale_threshold` seconds, it is saved back to the data store
        from the cache.
        """
