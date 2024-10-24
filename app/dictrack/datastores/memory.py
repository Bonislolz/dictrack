# -*- coding: utf-8 -*-

from collections import defaultdict
from threading import Lock

import six

from dictrack.datastores.base import BaseDataStore
from dictrack.utils.errors import (
    ConflictingNameError,
    GroupIdLookupError,
    NameLookupError,
)
from dictrack.utils.utils import typecheck


class MemoryDataStore(BaseDataStore):
    def __init__(self):
        self._group_pool = defaultdict(defaultdict)

        self._group_pool_lock = Lock()

    @typecheck()
    def add_tracker(self, tracker):
        # Tracker already exists in the group
        if tracker.name in self._group_pool[tracker.group_id]:
            raise ConflictingNameError(tracker.group_id, tracker.name)

        with self._group_pool_lock:
            self._group_pool[tracker.group_id][tracker.name] = tracker

    @typecheck()
    def get_tracker(self, group_id, name):
        # Not found group by the id
        if group_id not in self._group_pool:
            raise GroupIdLookupError(group_id)

        # Not found tracker by the name
        if name not in self._group_pool[group_id]:
            raise NameLookupError(name)

        return self._group_pool[group_id][name]

    @typecheck()
    def get_trackers(self, group_id):
        # Not found group by the id
        if group_id not in self._group_pool:
            raise GroupIdLookupError(group_id)

        return list(six.itervalues(self._group_pool[group_id]))

    @typecheck()
    def update_tracker(self, tracker):
        # Data is already stored in memory;
        # modifying the tracker’s data will take effect immediately
        pass

    @typecheck()
    def track(self, group_id, data):
        dirtied_trackers = []
        completed_trackers = []
        for tracker in self.get_trackers(group_id):
            tracker.track(data)

            # No modification, pass
            if not tracker.dirtied:
                continue

            dirtied_trackers.append(tracker)
            # Completed, execute removing process
            if tracker.completed:
                completed_trackers.append(tracker)
                self.remove_tracker(tracker.group_id, tracker.name)
                tracker.removed = True
            # Modified, execute updating process
            else:
                self.update_tracker(tracker)
                tracker.dirtied = False

        return dirtied_trackers, completed_trackers

    @typecheck()
    def remove_tracker(self, group_id, name):
        removed_tracker = self.get_tracker(group_id, name)

        with self._group_pool_lock:
            del self._group_pool[group_id][name]

        return removed_tracker

    def reset_all(self):
        with self._group_pool_lock:
            del self._group_pool
            self._group_pool = defaultdict(defaultdict)
