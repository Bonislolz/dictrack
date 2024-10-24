# -*- coding: utf-8 -*-


import multiprocessing
import os
import random
from datetime import datetime

import six
from dictrack.conditions import KeyValueEQ, KeyValueGE
from dictrack.datastores import RedisDataStore
from dictrack.manager import TrackingManager
from dictrack.trackers import AccumulationTracker, CountTracker
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


manager = TrackingManager(RedisDataStore(host=os.environ.get("REDIS_HOST")))
# manager.add_listener(EVENT_TRACKER_ADDED, print_event)
# manager.reset_all()
users = 50000
batch_size = 5000
total_users = list(six.moves.range(10000001, 10000001 + users))
batched_users = [
    total_users[i : i + batch_size] for i in range(0, len(total_users), batch_size)
]


def insert_trackers(users):
    for user in users:
        trackers = create_trackers(100, 100)
        try:
            manager.add_trackers(str(user), trackers)
        except ConflictingNameError:
            continue


pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
results = pool.map(insert_trackers, batched_users)
pool.close()
pool.join()
logger.info(results)
