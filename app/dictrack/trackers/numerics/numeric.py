# -*- coding: UTF-8 -*-

from dictrack.trackers.base import BaseTracker


class NumericTracker(BaseTracker):
    def _check_progress(self):
        # Not yet
        if self.progress < self.target:
            return False

        # Completed
        self._complete()

        return True
