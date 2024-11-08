# -*- coding: UTF-8 -*-


from abc import ABCMeta, abstractmethod

import six
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from dictrack.utils.utils import typecheck


class BaseDataStore(six.with_metaclass(ABCMeta)):
    @typecheck()
    def __init__(self, scheduler_class=BackgroundScheduler, check_interval=60 * 60 * 2):
        self.check_interval = check_interval

        self.scheduler = scheduler_class()
        self.scheduler.add_job(
            self._check_expire, IntervalTrigger(seconds=self.check_interval)
        )

        self.data_cache = None

    def start_scheduler(self):
        self.scheduler.start()

    @abstractmethod
    def store(self, group_id, tracker, expire=None, expire_at=None, **kwargs):
        """Implement for storing a single data item under the specified
        `group_id` in the data store.
        """

    @abstractmethod
    def store_all(self, group_id, trackers, expire=None, expire_at=None, **kwargs):
        """Implement for storing multiple data items under the specified
        `group_id` in the data store.
        """

    @abstractmethod
    def load(self, group_id, name=None, **kwargs):
        """Implement for retrieving data from the data store under the
        specified `group_id`.
        If `name` is None, retrieve all data under `group_id`;
        if `name` is provided, retrieve only the specified data.
        """

    @abstractmethod
    def remove(self, group_id, name=None, **kwargs):
        """Implement for removing data from the data store under the
        specified `group_id`.
        If `name` is None, removes all data under `group_id`;
        if `name` is provided, removes only the specified data.
        """

    @abstractmethod
    def flush(self):
        """Implement for clearing all data from the data store."""

    @abstractmethod
    def _check_expire(self):
        """"""
