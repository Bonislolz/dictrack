# -*- coding: utf-8 -*-


import multiprocessing
import os
import random
from datetime import datetime

import six
from dictrack.conditions.keys import KeyValueEQ, KeyValueGE
from dictrack.data_caches.memory import MemoryDataCache  # noqa: F401
from dictrack.data_caches.redis import RedisDataCache  # noqa: F401
from dictrack.data_stores.mongodb import MongoDBDataStore
from dictrack.events import EVENT_TRACKER_ADDED
from dictrack.manager import TrackingManager
from dictrack.trackers.numerics.accumulation import AccumulationTracker  # noqa: F401
from dictrack.trackers.numerics.count import CountTracker  # noqa: F401
from dictrack.utils.errors import ConflictingNameError
from dictrack.utils.logger import logger

logger.disabled = False


def create_trackers(n_count, n_accumulation):
    trackers = []
    # Count
    for i in six.moves.range(n_count):
        target = random.randint(10, 50)
        conditions = [
            KeyValueEQ("game", random.choice(["a", "b", "c"])),
            KeyValueGE("bet", random.choice(six.moves.range(100, 501, 10))),
        ]
        trackers.append(CountTracker("Count-{}".format(i), conditions, target))

    # Accumulation
    for i in six.moves.range(n_accumulation):
        target = random.randint(1000, 5000)
        conditions = [
            KeyValueEQ("game", random.choice(["a", "b", "c"])),
            KeyValueGE("bet", random.choice(six.moves.range(100, 501, 10))),
        ]
        trackers.append(
            AccumulationTracker(
                "Accumulation-{}".format(i), conditions, target, key="bet"
            )
        )

    return trackers


def print_event(event):
    readable_time = datetime.fromtimestamp(event.event_ts).strftime("%Y-%m-%d %H:%M:%S")

    logger.info(
        "[{}] - {} ADDED at {}".format(event.group_id, event.name, readable_time)
    )


manager = TrackingManager(
    RedisDataCache(host=os.environ.get("REDIS_HOST")),
    MongoDBDataStore(host=os.environ.get("MONGODB_HOST")),
)
manager.flush(confirm=True)

users = 1000
batch_size = 1000
total_users = list(six.moves.range(10000001, 10000001 + users))
batched_users = [
    total_users[i : i + batch_size] for i in range(0, len(total_users), batch_size)
]


def insert_trackers(users):
    manager = TrackingManager(
        RedisDataCache(host=os.environ.get("REDIS_HOST")),
        MongoDBDataStore(host=os.environ.get("MONGODB_HOST")),
    )
    manager.add_listener(EVENT_TRACKER_ADDED, print_event)

    for user in users:
        trackers = create_trackers(50, 50)
        try:
            manager.add_trackers(str(user), trackers, expire=random.randint(60, 100))
        except ConflictingNameError:
            continue


pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
results = pool.map(insert_trackers, batched_users)
pool.close()
pool.join()
