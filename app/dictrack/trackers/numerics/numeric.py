# -*- coding: UTF-8 -*-

from dictrack.trackers import BaseTracker


class NumericTracker(BaseTracker):
    """
    A tracker that monitors numeric progress towards a defined target.
    """

    def _check_progress(self):
        # Not yet
        if self.progress < self.target:
            return False

        # Completed
        self._complete()

        return True
