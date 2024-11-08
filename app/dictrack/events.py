# -*- coding: UTF-8 -*-

import time

EVENT_TRACKER_ADDED = 1001  # TrackingManager level
EVENT_TRACKER_STAGE_COMPLETED = 1002  # Tracker level
EVENT_TRACKER_ALL_COMPLETED = 1003  # Tracker level
EVENT_TRACKER_RESET = 1004  # Tracker level
EVENT_TRACKER_LIMITED = 1005  # Tracker level
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


class LimitedTrackerEvent(TrackerEvent):
    def __init__(self, code, group_id, name, tracker, limiter):
        super(LimitedTrackerEvent, self).__init__(code, group_id, name, tracker)

        self.limiter = limiter

    def __repr__(self):
        return "<LimitedTrackerEvent (code={} group_id={} name={} tracker={} limiter={})>".format(
            self.code, self.group_id, self.name, self.tracker, self.limiter
        )
