# -*- coding: UTF-8 -*-

import random

from locust import HttpUser, between, task


class GameUser(HttpUser):
    wait_time = between(3.0, 5.0)

    @task
    def send_track(self):
        data = {
            "group_id": str(random.randint(10000001, 10001000)),
            # "group_id": "10000001",
            "bet": random.randint(100, 500),
            "game": random.choice(["a", "b", "c"]),
        }
        self.client.post("/track", json=data)
