# -*- coding: UTF-8 -*-

from dictrack.trackers.numerics.numeric import NumericTracker
from dictrack.utils.utils import typecheck


class CountTracker(NumericTracker):
    """
    A tracker that increments progress by a count and checks against a defined numeric target.
    """

    def __repr__(self):
        content = "<CountTracker (target={} conditions={} limiters={} group_id={} name={} progress={})>".format(
            self.target,
            self.conditions,
            self.limiters,
            self.group_id,
            self.name,
            self.progress,
        )

        if self.removed:
            return "[REMOVED] " + content
        elif self.completed:
            return "[COMPLETED] " + content
        elif self.limited:
            return "[LIMITED] " + content
        else:
            return content

    @typecheck()
    def _push_progress(self, data, *args, **kwargs):
        self._progress += 1
