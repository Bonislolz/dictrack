# -*- coding: UTF-8 -*-


import time
from datetime import datetime
from logging import getLogger

import six
from apscheduler.schedulers.background import BackgroundScheduler
from tzlocal import get_localzone

from dictrack.data_stores.base import BaseDataStore
from dictrack.trackers.base import BaseTracker
from dictrack.utils.utils import typecheck, valid_type

try:
    from bson.binary import Binary
    from pymongo import ASCENDING, DESCENDING, MongoClient, UpdateOne
except ImportError:
    raise ImportError("MongoDBDataStore must install `pymongo`")

logger = getLogger("dictrack.data_stores.mongodb")


class MongoDBDataStore(BaseDataStore):
    def __init__(
        self,
        scheduler_class=BackgroundScheduler,
        check_interval=60 * 60 * 2,
        collection="data_store",
        database="dictrack",
        client=None,
        strict=True,
        **connect_kwargs
    ):
        """
        Initialize a MongoDB data store with prioritized connection options.
        Supports two methods to establish MongoDB connection:
            1. Pass a MongoClient object via `client`.
            2. Pass MongoDB connection kwargs directly.
        Priority order: 1 > 2.

        Parameters
        ----------
        scheduler_class : type, optional
            The scheduler class for periodic tasks. Defaults to `BackgroundScheduler`.
        check_interval : int, optional
            Interval in seconds to check for updates. Defaults to `60 * 60 * 2`.
        collection : str, optional
            The name of the MongoDB collection used for data storage. Defaults to `"data_store"`.
        database : str, optional
            The name of the MongoDB database used for data storage. Defaults to `"dictrack"`.
        client : MongoClient, optional
            An optional MongoDB client instance for direct connection.
        strict : bool, optional
            If `True`, performs strict type checking for `client` (`pymongo.mongo_client.MongoClient`).
            Defaults to `True`.
        connect_kwargs : dict, optional
            Additional connection arguments if `client` is not provided.

        Raises
        ------
        TypeError
            If `collection`, `database`, or `client` types are invalid when `strict` is `True`.
        ConnectionError
            If MongoDB client initialization fails due to invalid `client` or `connect_kwargs`.

        Notes
        -----
        When `strict` is `True`, `client` must be an instance of `pymongo.mongo_client.MongoClient`.
        If no client is provided, `connect_kwargs` are used to create a new MongoDB client.
        """
        super(MongoDBDataStore, self).__init__(
            scheduler_class=scheduler_class, check_interval=check_interval
        )

        valid_type(collection, six.string_types)
        valid_type(database, six.string_types)
        if strict:
            valid_type(client, MongoClient, allow_empty=True)

        if client is not None:
            self._mongo_client = client
        else:
            self._mongo_client = MongoClient(**connect_kwargs)

        self._data_collection = self._mongo_client[database][collection]
        self._admin_collection = self._mongo_client[database]["admin"]

        # Try mongodb connection
        try:
            self._data_collection.create_index(
                [("group_id", ASCENDING), ("name", ASCENDING)], unique=True
            )
            self._data_collection.create_index([("name", ASCENDING)])
            self._data_collection.create_index([("last_store_ts", DESCENDING)])
            self._data_collection.create_index([("expire_ts", ASCENDING)], sparse=True)

            self._admin_collection.update_one(
                {"name": "check_flag"},
                {"$setOnInsert": {"ts": int(time.time())}},
                upsert=True,
            )
        except Exception as e:
            raise IOError(
                "mongodb client initialization failed: either `client, "
                "or `connect_kwargs` must be provided, {}".format(e.__repr__())
            )

    @typecheck()
    def store(self, group_id, tracker, expire=None, expire_at=None, **kwargs):
        valid_type(expire, six.integer_types, allow_empty=True)
        valid_type(expire_at, six.integer_types, allow_empty=True)

        now_ts = int(time.time())
        update = {
            "$set": {
                "b_tracker": Binary(BaseTracker.serialize(tracker)),
                "last_store_ts": now_ts,
                "last_store_ts_human": datetime.fromtimestamp(
                    now_ts, tz=get_localzone()
                ),
            },
            "$setOnInsert": {},
        }
        # Process expire timestamp
        if expire is not None:
            update["$setOnInsert"]["expire_ts"] = now_ts + expire
        if expire_at is not None:
            update["$setOnInsert"]["expire_ts"] = expire_at
        if "expire_ts" in update["$setOnInsert"]:
            update["$setOnInsert"]["expire_ts_human"] = datetime.fromtimestamp(
                update["$setOnInsert"]["expire_ts"], tz=get_localzone()
            )

        try:
            self._data_collection.update_one(
                {"group_id": group_id, "name": tracker.name}, update, upsert=True
            )
        except Exception as e:
            logger.exception("Store tracker failed, {}".format(e.__repr__()))

            return False

        return True

    @typecheck()
    def store_all(self, group_id, trackers, expire=None, expire_at=None, **kwargs):
        valid_type(expire, six.integer_types, allow_empty=True)
        valid_type(expire_at, six.integer_types, allow_empty=True)

        now_ts = int(time.time())
        common_update = {"$setOnInsert": {}}
        # Process expire timestamp
        if expire is not None:
            common_update["$setOnInsert"]["expire_ts"] = now_ts + expire
        if expire_at is not None:
            common_update["$setOnInsert"]["expire_ts"] = expire_at
        if "expire_ts" in common_update["$setOnInsert"]:
            common_update["$setOnInsert"]["expire_ts_human"] = datetime.fromtimestamp(
                common_update["$setOnInsert"]["expire_ts"], tz=get_localzone()
            )

        requests = []
        for tracker in trackers:
            tracker_update = {
                "$set": {
                    "b_tracker": Binary(BaseTracker.serialize(tracker)),
                    "last_store_ts": now_ts,
                    "last_store_ts_human": datetime.fromtimestamp(now_ts),
                }
            }
            tracker_update.update(common_update)

            requests.append(
                UpdateOne(
                    {"group_id": group_id, "name": tracker.name},
                    tracker_update,
                    upsert=True,
                )
            )

        try:
            self._data_collection.bulk_write(requests, ordered=False)
        except Exception as e:
            logger.exception("Store trackers failed, {}".format(e.__repr__()))

            return False

        return True

    @typecheck()
    def load(self, group_id, name=None, **kwargs):
        valid_type(name, six.string_types + (list,), allow_empty=True)

        filter = {"group_id": group_id}
        # Specified one data
        if isinstance(name, six.string_types):
            filter["name"] = name
        # All data
        elif name is None:
            pass
        # Specified multi data
        else:
            filter["name"] = {"$in": name}

        try:
            cursor = self._data_collection.find(filter)
        except Exception as e:
            logger.exception("Load tracker failed, {}".format(e.__repr__()))

            return False, []

        return True, [
            BaseTracker.deserialize(document["b_tracker"]) for document in cursor
        ]

    @typecheck()
    def remove(self, group_id, name=None, **kwargs):
        valid_type(name, six.string_types + (list,), allow_empty=True)

        removed_trackers = []
        try:
            # Specified one data
            if isinstance(name, six.string_types):
                document = self._data_collection.find_one_and_delete(
                    {"group_id": group_id, "name": name}
                )
                if document is not None:
                    removed_trackers.append(
                        BaseTracker.deserialize(document["b_tracker"])
                    )
            # All data/Specified multi data
            else:
                filter = {"group_id": group_id}
                if isinstance(name, list):
                    filter["name"] = {"$in": name}
                cursor = self._data_collection.find(filter)
                self._data_collection.delete_many(filter)
                removed_trackers = [
                    BaseTracker.deserialize(document["b_tracker"])
                    for document in cursor
                ]
        except Exception as e:
            logger.exception("Remove tracker failed, {}".format(e.__repr__()))

            return False, []

        for tracker in removed_trackers:
            tracker.removed = True

        return True, removed_trackers

    def flush(self):
        try:
            self._data_collection.delete_many({})
        except Exception as e:
            logger.exception("Flush all data failed, {}".format(e.__repr__()))

            return False

        return True

    def _check_expire(self):
        now_ts = int(time.time())

        # Use atomic operation to perform lock
        try:
            document = self._admin_collection.find_one_and_update(
                {"ts": {"$lte": now_ts - self.check_interval}}, {"$set": {"ts": now_ts}}
            )
            if document is None:
                logger.debug("The next check time has not been reached yet")
                return
        except Exception as e:
            logger.exception("Find last check time failed, {}".format(e.__repr__()))
            return

        # Do check procedure
        logger.info("Starting the check procedure")

        removed_trackers = []
        filter = {"expire_ts": {"$lte": now_ts}}
        try:
            for document in self._data_collection.find(filter):
                removed_trackers.append(BaseTracker.deserialize(document["b_tracker"]))
            self._data_collection.delete_many(filter)
        except Exception as e:
            logger.exception("Remove expired tracker failed, {}".format(e.__repr__()))

        # Mark removed and check cache
        for tracker in removed_trackers:
            self.data_cache.remove(tracker.group_id, tracker.name)
            tracker.removed = True

        logger.info("Finished the check procedure")
