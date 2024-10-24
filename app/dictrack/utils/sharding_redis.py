# -*- coding: utf-8 -*-


from dictrack.utils.utils import valid_type


class ShardedRedisClient(object):
    def __init__(self, connects):
        valid_type(connects, (list, tuple))

        # self._redis_clients = [StrictRedis() fo]
