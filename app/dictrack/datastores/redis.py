# -*- coding: utf-8 -*-

from __future__ import absolute_import

import six
from redis import ConnectionPool, StrictRedis
from redis_lock import Lock, reset_all

from dictrack.datastores.base import BaseDataStore
from dictrack.utils.errors import (
    ConflictingNameError,
    GroupIdLookupError,
    RedisOperationError,
    TrackerLookupError,
)
from dictrack.utils.utils import typecheck, valid_type


class RedisDataStore(BaseDataStore):
    def __init__(self, data_key="dictrack.data", batch_size=200, **connect_args):
        valid_type(data_key, six.string_types)

        self._data_key = data_key
        self._batch_size = batch_size
        self._connection_pool = ConnectionPool(**connect_args)
        self._redis_client = StrictRedis(
            connection_pool=self._connection_pool, decode_responses=True
        )

    @typecheck()
    def add_tracker(self, tracker):
        client = self._get_client()

        # Tracker already exists in the group
        if client.hexists(self._get_data_key(tracker=tracker), tracker.name):
            raise ConflictingNameError(tracker.group_id, tracker.name)

        with Lock(client, name=self._get_lock_key(tracker=tracker), expire=1):
            b_tracker = self._serialize(tracker)
            client.hset(self._get_data_key(tracker=tracker), tracker.name, b_tracker)

    @typecheck()
    def get_tracker(self, group_id, name):
        client = self._get_client()
        with Lock(client, name=self._get_lock_key(group_id=group_id), expire=1):
            b_tracker = client.hget(self._get_data_key(group_id=group_id), name)
            # Not found tracker by the id of group and name
            if b_tracker is None:
                raise TrackerLookupError(group_id, name)

            return self._deserialize(b_tracker)

    @typecheck()
    def get_trackers(self, group_id):
        client = self._get_client()
        with Lock(client, name=self._get_lock_key(group_id=group_id), expire=1):
            b_trackers_tree = client.hgetall(self._get_data_key(group_id=group_id))
            # Not found group by the id
            if not b_trackers_tree:
                raise GroupIdLookupError(group_id)

            return self._deserialize_list((list(six.itervalues(b_trackers_tree))))

    @typecheck()
    def update_tracker(self, tracker):
        client = self._get_client()
        with Lock(client, name=self._get_lock_key(tracker=tracker), expire=1):
            b_tracker = self._serialize(tracker)
            client.hset(self._get_data_key(tracker=tracker), tracker.name, b_tracker)

    @typecheck()
    def track(self, group_id, data):
        client = self._get_client()
        with Lock(client, name=self._get_lock_key(group_id=group_id), expire=2):
            dirtied_trackers = []
            completed_trackers = []
            conditions_cache = {}
            with client.pipeline() as pipe:
                for _, b_tracker in client.hscan_iter(
                    self._get_data_key(group_id=group_id), count=self._batch_size
                ):
                    tracker = self._deserialize(b_tracker)
                    tracker.track(data, cache=conditions_cache)

                    # No modification, pass
                    if not tracker.dirtied:
                        continue

                    dirtied_trackers.append(tracker)
                    # Completed, execute removing process
                    if tracker.completed:
                        completed_trackers.append(tracker)
                        pipe.hdel(self._get_data_key(tracker=tracker), tracker.name)
                        tracker.removed = True
                    # Modified, execute updating process
                    else:
                        b_tracker = self._serialize(tracker)
                        pipe.hset(
                            self._get_data_key(tracker=tracker), tracker.name, b_tracker
                        )

            del conditions_cache

            return dirtied_trackers, completed_trackers

    @typecheck()
    def remove_tracker(self, group_id, name):
        client = self._get_client()
        with Lock(client, name=self._get_lock_key(group_id=group_id), expire=1):
            with client.pipeline() as pipe:
                pipe.hget(self._get_data_key(group_id=group_id), name)
                pipe.hdel(self._get_data_key(group_id=group_id), name)

                result = pipe.execute()

        b_tracker, is_deleted = result
        # Not found tracker by the id of group and name
        if b_tracker is None:
            raise TrackerLookupError(group_id, name)
        # Operation HDEL is failed
        if not is_deleted:
            raise RedisOperationError(
                "Remove tracker by id of group ({}) and name ({}) failed".format(
                    group_id, name
                )
            )

        tracker = self._deserialize(b_tracker)
        tracker.removed = True

        return tracker

    def reset_all(self):
        client = self._get_client()
        reset_all(client)

        keys = []
        for key in client.scan_iter(
            self._get_data_key(group_id="*"), count=self._batch_size
        ):
            keys.append(key)

        client.delete(*keys)

    def _get_client(self):
        return self._redis_client

    def _get_data_key(self, tracker=None, group_id=None):
        """
        Generate a data key based on the `tracker` or the provided `group_id`.

        :param `BaseTracker` tracker: Optional tracker object containing `group_id`.
        If provided, it takes precedence over the group_id argument.
        :param `str` group_id: The group ID to use if `tracker` is not provided.
        :return: Concatenated data key as a string.
        :rtype: `str`
        :raises `ValueError`: If both `tracker` is `None` and `group_id` is not provided.
        """
        if tracker:
            group_id = tracker.group_id

        if not group_id:
            raise ValueError("group_id must be specified if tracker is not provided")

        return ":".join([self._data_key, group_id])

    def _get_lock_key(self, tracker=None, group_id=None):
        """
        Generate a lock key based on the tracker or the provided group_id.

        :param `object` tracker: Optional tracker object containing `group_id`.
        If provided, it takes precedence over `group_id`.
        :param `str` group_id: The group ID to use if `tracker` is not provided.
        :return: Concatenated lock key as a string.
        :rtype: `str`
        :raises `ValueError`: If both `tracker` is `None` and `group_id` is not provided.
        """
        if tracker:
            group_id = tracker.group_id

        if not group_id:
            raise ValueError("group_id must be specified if tracker is not provided")

        return ":".join([self._data_key, group_id])
