# -*- coding: UTF-8 -*-

import time

EVENT_TRACKER_ADDED = 1001
EVENT_TRACKER_MODIFIED = 1002
EVENT_TRACKER_REMOVED = 1003
EVENT_TRACKER_COMPLETED = 1004
EVENT_TRACKER_RESET = 1005
# Collect all event constants that start with 'EVENT_'
EVENT_ALL = [value for key, value in globals().items() if key.startswith("EVENT_")]


class BaseEvent(object):
    def __init__(self, code):
        self.code = code
        self.event_ts = time.time()

    def __repr__(self):
        return "<BaseEvent (code={})>".format(self.code)


class TrackerEvent(BaseEvent):
    def __init__(self, code, group_id, name, tracker):
        super(TrackerEvent, self).__init__(code)

        self.group_id = group_id
        self.name = name
        self.tracker = tracker

    def __repr__(self):
        return "<TrackerEvent (code={} group_id={} name={} tracker={})>".format(
            self.code, self.group_id, self.name, self.tracker
        )
