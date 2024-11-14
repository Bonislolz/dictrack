# -*- coding: utf-8 -*-

from __future__ import absolute_import

import time
from logging import getLogger

import six
from apscheduler.schedulers.background import BackgroundScheduler
from redis_lock import Lock, reset_all

from dictrack.data_caches.base import BaseDataCache
from dictrack.trackers.base import BaseTracker
from dictrack.utils.errors import ConflictingNameError
from dictrack.utils.utils import typecheck, valid_type

try:
    from redis import ConnectionPool, StrictRedis
except ImportError:
    raise ImportError("RedisDataCache must install `redis`")


logger = getLogger("dictrack.data_caches.redis")


class RedisDataCache(BaseDataCache):
    def __init__(
        self,
        scheduler_class=BackgroundScheduler,
        check_interval=60 * 30,
        stale_threshold=60 * 60 * 6,
        data_key="dictrack.data_cache",
        last_cached_key="dictrack.last_cached",
        check_flag_key="dictrack.check_flag",
        batch_size=200,
        data_expire=60 * 60 * 24,
        client=None,
        pool=None,
        strict=True,
        **connect_kwargs
    ):
        """
        Initialize a Redis data cache with prioritized connection options.
        Support three methods to establish Redis connection:
            1. Pass a ConnectPool object via pool.
            2. Pass a StrictRedis object via client.
            3. Pass Redis connection kwargs directly.
            Priority order: 1 > 2 > 3.

        Parameters
        ----------
        scheduler_class : type, optional
            The scheduler class to use for periodic tasks. Defaults to `BackgroundScheduler`.
        check_interval : int, optional
            Interval in seconds to check for stale data. Defaults to `60 * 30`.
        stale_threshold : int, optional
            Threshold in seconds beyond which data is considered stale. Defaults to `60 * 60 * 6`.
        data_key : str, optional
            The key used for caching data in Redis. Defaults to `"dictrack.data_cache"`.
        last_cached_key : str, optional
            The sorted set key used to track last cache updates in Redis. Defaults to `"dictrack.cache_zset"`.
        check_flag_key : str, optional
            The key used to record the last checked timestamp for stale data. Defaults to `"dictrack.check_flag"`.
        batch_size : int, optional
            The size of data to process per track or fetch operation. Defaults to `200`.
        data_expire : int, optional
            Expiration time for cached data in seconds. Defaults to `60 * 60 * 24`.
        client : StrictRedis, optional
            An optional Redis client instance.
        pool : ConnectionPool, optional
            An optional connection pool for Redis.
        strict : bool, optional
            If `True`, performs strict type checking for `client` (`redis.StrictRedis`) and
            `pool` (`redis.ConnectionPool`). Defaults to `True`.
        connect_kwargs : dict, optional
            Additional connection arguments if neither `client` nor `pool` is provided.

        Raises
        ------
        ValueError
            If `batch_size` is not a positive integer or if `decode_responses` is not `False` in the provided `client`.
        TypeError
            If `data_key`, `last_cached_key`, `check_flag_key`, `batch_size`, `client`, or `pool` types are invalid.
        IOError
            If Redis client initialization fails due to invalid `pool`, `client`, or `connect_kwargs`.

        Notes
        -----
        When `strict` is `True`, `client` must be an instance of `redis.StrictRedis`,
        and `pool` must be an instance of `redis.ConnectionPool`.
        If no `client` or `pool` is provided, `connect_kwargs` are used to create a new Redis client.
        """
        super(RedisDataCache, self).__init__(
            scheduler_class, check_interval, stale_threshold
        )

        valid_type(data_key, six.string_types)
        valid_type(last_cached_key, six.string_types)
        valid_type(check_flag_key, six.string_types)
        valid_type(batch_size, six.integer_types)
        if strict:
            valid_type(client, StrictRedis, allow_empty=True)
            valid_type(pool, ConnectionPool, allow_empty=True)

        self._data_key = data_key
        self._last_cached_key = last_cached_key
        self._check_flag_key = check_flag_key
        self._batch_size = batch_size
        self._data_expire = data_expire
        if self._batch_size <= 0:
            raise ValueError("`batch_size` must be a positive integer")

        if pool is not None:
            self._redis_client = StrictRedis(connection_pool=pool)
        elif client is not None:
            self._redis_client = client
            if self._redis_client.connection_pool.connection_kwargs["decode_responses"]:
                raise ValueError(
                    "`decode_responses` must be set to `False` in `client`"
                )
        else:
            self._redis_client = StrictRedis(
                connection_pool=ConnectionPool(**connect_kwargs)
            )

        # Try redis connection
        try:
            self._redis_client.set(
                self._get_check_flag_key(),
                int(time.time()),
                ex=int(self.check_interval * 1.2),
                nx=True,
            )
        except Exception as e:
            raise IOError(
                "redis client initialization failed: either `pool`, `client`, "
                "or `connect_kwargs` must be provided, {}".format(e.__repr__())
            )

    @typecheck()
    def cache(self, group_id, tracker, lock_expire=1, force=False, **kwargs):
        client = self._get_client()

        # Tracker already exists in the group
        if not force and client.hexists(
            self._get_data_key(tracker=tracker), tracker.name
        ):
            raise ConflictingNameError(group_id, tracker.name)

        with Lock(client, name=self._get_lock_key(tracker=tracker), expire=lock_expire):
            b_tracker = tracker.serialize(tracker)
            with client.pipeline() as pipe:
                pipe.hset(self._get_data_key(tracker=tracker), tracker.name, b_tracker)
                pipe.expire(self._get_data_key(tracker=tracker), self._data_expire)
                pipe.zadd(self._get_last_cached_key(), {group_id: int(time.time())})
                pipe.expire(self._get_last_cached_key(), self._data_expire)
                pipe.execute()

        return tracker

    @typecheck()
    def cache_all(self, group_id, trackers, lock_expire=2, force=False, **kwargs):
        added_trackers = []
        for tracker in trackers:
            try:
                added_trackers.append(
                    self.cache(group_id, tracker, lock_expire=lock_expire)
                )
            except ConflictingNameError as e:
                logger.debug(
                    "Tracker already cached, skip this one, {}".format(e.__repr__())
                )
            except Exception as e:
                logger.exception(
                    "Cache tracker failed, abort this one, {}".format(e.__repr__())
                )

        return added_trackers

    @typecheck()
    def fetch(self, group_id, name=None, **kwargs):
        valid_type(name, six.string_types + (list,), allow_empty=True)

        client = self._get_client()
        # Specified one data
        if isinstance(name, six.string_types):
            b_tracker = client.hget(self._get_data_key(group_id=group_id), name)
            # Not found tracker by the id of group and name
            if b_tracker is None:
                return []

            return [BaseTracker.deserialize(b_tracker)]
        # All data
        elif name is None:
            b_trackers = [
                b_tracker
                for _, b_tracker in client.hscan_iter(
                    self._get_data_key(group_id=group_id), count=self._batch_size
                )
            ]

            return BaseTracker.deserialize_list(b_trackers)
        # Specified multi data
        else:
            b_trackers = [
                b_tracker
                for b_tracker in client.hmget(
                    self._get_data_key(group_id=group_id), name
                )
                if b_tracker is not None
            ]

            return BaseTracker.deserialize_list(b_trackers)

    @typecheck()
    def is_cached(self, group_id, name=None, **kwargs):
        valid_type(name, six.string_types, allow_empty=True)

        client = self._get_client()
        if not client.exists(self._get_data_key(group_id=group_id)):
            return False

        if name is not None:
            return client.hexists(self._get_data_key(group_id=group_id), name)

        return True

    @typecheck()
    def remove(self, group_id, name=None, lock_expire=1, **kwargs):
        valid_type(name, six.string_types + (list,), allow_empty=True)

        client = self._get_client()

        with Lock(
            client, name=self._get_lock_key(group_id=group_id), expire=lock_expire
        ):
            removed_trackers = self.fetch(group_id, name=name)
            if not removed_trackers:
                return []

            # Specified one
            if isinstance(name, six.string_types):
                client.hdel(self._get_data_key(group_id=group_id), name)
                if not client.exists(self._get_data_key(group_id=group_id)):
                    client.zrem(self._get_last_cached_key(), group_id)
            # All data
            elif name is None:
                with client.pipeline() as pipe:
                    pipe.delete(self._get_data_key(group_id=group_id))
                    pipe.zrem(self._get_last_cached_key(), group_id)
                    pipe.execute()
            # Specified multi data
            else:
                client.hdel(self._get_data_key(group_id=group_id), *name)
                if not client.exists(self._get_data_key(group_id=group_id)):
                    client.zrem(self._get_last_cached_key(), group_id)

        for tracker in removed_trackers:
            tracker.removed = True

        return removed_trackers

    def flush(self):
        client = self._get_client()
        reset_all(client)

        keys = []
        for key in client.scan_iter(
            self._get_data_key(group_id="*"), count=self._batch_size
        ):
            keys.append(key)

        if keys:
            client.delete(*keys)

        client.delete(self._get_last_cached_key())

    @typecheck()
    def track(self, group_id, data, lock_expire=10, *args, **kwargs):
        client = self._get_client()
        with Lock(
            client,
            name=self._get_lock_key(group_id=group_id),
            expire=lock_expire,
            auto_renewal=True,
        ):
            dirtied_trackers, completed_trackers, limited_trackers = [], [], []
            conditions_cache = {}
            with client.pipeline() as pipe:
                for _, b_tracker in client.hscan_iter(
                    self._get_data_key(group_id=group_id), count=self._batch_size
                ):
                    tracker = BaseTracker.deserialize(b_tracker)
                    tracker.forward_event(self.forward_cb)
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
                        pipe.hdel(self._get_data_key(tracker=tracker), tracker.name)
                        self.data_store.remove(group_id, tracker.name)
                        tracker.removed = True
                    # Modified, execute updating process
                    else:
                        b_tracker = tracker.serialize(tracker)
                        pipe.hset(
                            self._get_data_key(tracker=tracker), tracker.name, b_tracker
                        )
                        pipe.expire(
                            self._get_data_key(tracker=tracker), self._data_expire
                        )

                pipe.execute()

            if not client.exists(self._get_data_key(group_id=group_id)):
                client.delete(self._get_last_cached_key())

            del conditions_cache

            return dirtied_trackers, completed_trackers, limited_trackers

    def _get_client(self):
        return self._redis_client

    @typecheck(allow_empty=True)
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

    def _get_last_cached_key(self):
        return self._last_cached_key

    def _get_check_flag_key(self):
        return self._check_flag_key

    @typecheck(allow_empty=True)
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

    def _check_stale(self):
        client = self._get_client()
        now_ts = int(time.time())

        last_check_ts = client.get(self._get_check_flag_key())
        # No need to check
        if (
            last_check_ts is not None
            and int(last_check_ts) > now_ts - self.check_interval
        ):
            logger.debug("The next check time has not been reached yet")
            return

        # Acquire lock with non-blocking
        lock = Lock(
            client, name=self._get_check_flag_key(), expire=10, auto_renewal=True
        )
        is_locked = lock.acquire(blocking=False)
        if not is_locked:
            logger.info(
                "The check procedure is already being executed by another server"
            )
            return

        # Do check procedure
        logger.info("Starting the check procedure")

        for group_id in client.zrangebyscore(
            self._get_last_cached_key(), 0, now_ts - self.stale_threshold
        ):
            self.data_store.store_all(group_id, self.fetch(group_id))
            self.remove(group_id)
        else:
            client.set(
                self._get_check_flag_key(), now_ts, ex=int(self.check_interval * 1.2)
            )

        # Release lock
        lock.release()

        logger.info("Finished the check procedure")
