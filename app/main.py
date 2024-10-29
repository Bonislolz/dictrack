# -*- coding: utf-8 -*-


import logging
import os
from datetime import datetime

import gevent
import gevent.monkey
from dictrack.datastores.redis import RedisDataStore
from dictrack.events import (
    EVENT_TRACKER_COMPLETED,
    EVENT_TRACKER_MODIFIED,
)
from dictrack.manager import TrackingManager
from dictrack.utils.logger import logger
from flask import Flask, jsonify, request

logger.disabled = False
gevent.monkey.patch_all()


app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.WARNING)
manager = TrackingManager(RedisDataStore(host=os.environ.get("REDIS_HOST")))


@app.route("/track", methods=["POST"])
def on_track():
    data = request.get_json()
    if "group_id" not in data:
        return jsonify({"message": "missing parameter `group_id`", "data": None}), 400

    manager.track(data["group_id"], data)

    return jsonify({"message": "ok", "data": []})


CODE_TO_STR_MAPPING = {
    EVENT_TRACKER_MODIFIED: "MODIFIED",
    EVENT_TRACKER_COMPLETED: "COMPLETED",
}


def print_event(event):
    readable_code = CODE_TO_STR_MAPPING[event.code]
    readable_time = datetime.fromtimestamp(event.event_ts).strftime("%Y-%m-%d %H:%M:%S")

    if event.code in (EVENT_TRACKER_COMPLETED,):
        logger.info(
            "[{}] - {} {} at {}".format(
                event.group_id, event.name, readable_code, readable_time
            )
        )


manager.add_listener(EVENT_TRACKER_MODIFIED, print_event)
manager.add_listener(EVENT_TRACKER_COMPLETED, print_event)


if __name__ == "__main__":
    app.run("0.0.0.0", 5000)
