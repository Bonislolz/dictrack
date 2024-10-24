# -*- coding: utf-8 -*-

from collections import defaultdict

from dictrack.events import (
    EVENT_ALL,
    EVENT_TRACKER_ADDED,
    EVENT_TRACKER_COMPLETED,
    EVENT_TRACKER_MODIFIED,
    EVENT_TRACKER_REMOVED,
    BaseEvent,
    TrackerEvent,
)
from dictrack.trackers.base import BaseTracker
from dictrack.utils.logger import logger
from dictrack.utils.utils import typecheck, valid_callable, valid_obj, valid_type


# Only dispatch added and removed
class TrackingManager(object):
    @typecheck()
    def __init__(self, datastore):
        self._datastore = datastore

        self._listeners = defaultdict(list)

    def add_listener(self, code, cb):
        valid_obj(code, EVENT_ALL)
        valid_callable(cb)

        self._listeners[code].append(cb)

    @typecheck()
    def add_tracker(self, group_id, tracker):
        tracker.group_id = group_id
        self._datastore.add_tracker(tracker)

        self._dispatch_event(
            TrackerEvent(EVENT_TRACKER_ADDED, group_id, tracker.name, tracker)
        )

    @typecheck()
    def add_trackers(self, group_id, trackers):
        if not all(isinstance(t, BaseTracker) for t in trackers):
            raise TypeError("Trackers must contain instances of BaseTracker")

        for tracker in trackers:
            self.add_tracker(group_id, tracker)

    def get_trackers(self, group_id):
        return self._datastore.get_trackers(group_id)

    def update_tracker(self, tracker):
        self._datastore.update_tracker(tracker)

    @typecheck()
    def remove_tracker(self, group_id, name):
        removed_tracker = self._datastore.remove_tracker(group_id, name)

        self._dispatch_event(
            TrackerEvent(EVENT_TRACKER_REMOVED, group_id, name, removed_tracker)
        )

        return removed_tracker

    @typecheck()
    def track(self, group_id, data):
        dirtied_trackers, completed_trackers = self._datastore.track(group_id, data)
        for tracker in dirtied_trackers:
            self._dispatch_event(
                TrackerEvent(
                    EVENT_TRACKER_MODIFIED, tracker.group_id, tracker.name, tracker
                )
            )

        for tracker in completed_trackers:
            self._dispatch_event(
                TrackerEvent(
                    EVENT_TRACKER_COMPLETED, tracker.group_id, tracker.name, tracker
                )
            )

            self._dispatch_event(
                TrackerEvent(
                    EVENT_TRACKER_REMOVED, tracker.group_id, tracker.name, tracker
                )
            )

        return dirtied_trackers, completed_trackers

    def reset_all(self):
        self._datastore.reset_all()

    def _dispatch_event(self, event):
        valid_type(event, BaseEvent)

        for cb in self._listeners[event.code]:
            try:
                cb(event)
            except Exception as e:
                logger.exception(
                    "notify listener ({}) failed, {}".format(cb.__name__, e)
                )
