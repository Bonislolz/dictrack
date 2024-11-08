# -*- coding: utf-8 -*-


import logging
import os
import time
from datetime import datetime

import gevent
import gevent.monkey

gevent.monkey.patch_all()

from apscheduler.schedulers.gevent import GeventScheduler  # noqa: E402
from dictrack.conditions.keys import (  # noqa: E402, F401
    KeyExists,
    KeyValueEQ,
    KeyValueGE,
    KeyValueGT,
    KeyValueLE,
    KeyValueLT,
)
from dictrack.data_caches.memory import MemoryDataCache  # noqa: E402, F401
from dictrack.data_caches.redis import RedisDataCache  # noqa: E402, F401
from dictrack.data_stores.mongodb import MongoDBDataStore  # noqa: E402, F401
from dictrack.events import (  # noqa: E402
    EVENT_TRACKER_ALL_COMPLETED,
    EVENT_TRACKER_LIMITED,
    EVENT_TRACKER_RESET,
    EVENT_TRACKER_STAGE_COMPLETED,
)
from dictrack.limiters.count import CountLimiter  # noqa: E402, F401
from dictrack.limiters.time import TimeLimiter  # noqa: E402, F401
from dictrack.manager import TrackingManager  # noqa: E402
from dictrack.trackers.numerics.accumulation import (  # noqa: E402, F401
    AccumulationTracker,
)
from dictrack.trackers.numerics.count import CountTracker  # noqa: E402, F401
from dictrack.utils.logger import logger  # noqa: E402
from flask import Flask, jsonify, request  # noqa: E402

logger.disabled = False
logger.setLevel(logging.DEBUG)


logging.getLogger("apscheduler").addHandler(logging.StreamHandler())
logging.getLogger("werkzeug").setLevel(logging.WARNING)

app = Flask(__name__)

manager = TrackingManager(
    # MemoryDataCache(
    #     scheduler_class=GeventScheduler, check_interval=1, stale_threshold=10
    # ),
    RedisDataCache(scheduler_class=GeventScheduler, host=os.environ.get("REDIS_HOST")),
    MongoDBDataStore(
        scheduler_class=GeventScheduler, host=os.environ.get("MONGODB_HOST")
    ),
)


@app.route("/track", methods=["POST"])
def on_track():
    data = request.get_json()
    if "group_id" not in data:
        return jsonify({"message": "missing parameter `group_id`", "data": None}), 400

    manager.track(str(data["group_id"]), data, now_ts=int(time.time()))

    return jsonify({"message": "ok", "data": []})


CONDITION_CODE_TO_CLASS_MAPPING = {
    "ke": KeyExists,
    "kveq": KeyValueEQ,
    "kvle": KeyValueLE,
    "kvlt": KeyValueLT,
    "kvge": KeyValueGE,
    "kvgt": KeyValueGT,
}


@app.route("/reset", methods=["POST"])
def on_reset():
    data = request.get_json()
    if "group_id" not in data:
        return jsonify({"message": "missing parameter `group_id`", "data": None}), 400
    if "name" not in data:
        return jsonify({"message": "missing parameter `name`", "data": None}), 400

    manager.reset_tracker(str(data["group_id"]), data["name"], data.get("reset_policy"))

    return jsonify({"message": "ok", "data": []})


CODE_TO_STR_MAPPING = {
    EVENT_TRACKER_ALL_COMPLETED: "ALL COMPLETED",
    EVENT_TRACKER_RESET: "RESET",
    EVENT_TRACKER_LIMITED: "LIMITED",
    EVENT_TRACKER_STAGE_COMPLETED: "STAGE COMPLETED",
}


def print_event(event):
    readable_code = CODE_TO_STR_MAPPING[event.code]
    readable_time = datetime.fromtimestamp(event.event_ts).strftime("%Y-%m-%d %H:%M:%S")

    if event.code in CODE_TO_STR_MAPPING:
        logger.info("{} {} at {}".format(event, readable_code, readable_time))


manager.add_listener(EVENT_TRACKER_ALL_COMPLETED, print_event)
manager.add_listener(EVENT_TRACKER_STAGE_COMPLETED, print_event)
manager.add_listener(EVENT_TRACKER_RESET, print_event)
manager.add_listener(EVENT_TRACKER_LIMITED, print_event)


if __name__ == "__main__":
    app.run("0.0.0.0", 5000)
