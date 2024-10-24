# -*- coding: UTF-8 -*-

from dictrack.trackers.numerics.numeric import NumericTracker
from dictrack.utils.utils import typecheck


class CountTracker(NumericTracker):
    def __eq__(self, other):
        return (
            self.target == other.target
            and self.conditions
            == other.conditions  # This will call __eq__ of the type set
            and self.group_id == other.group_id
            and self.name == other.name
        )

    def __repr__(self):
        content = "<CountTracker (target={} conditions={} group_id={} name={} progress={})>".format(
            self.target, self.conditions, self.group_id, self.name, self.progress
        )

        if self.removed:
            return "[REMOVED] " + content
        elif self.completed:
            return "[COMPLETED] " + content
        else:
            return content

    @typecheck()
    def _push_progress(self, data, *args, **kwargs):
        self._progress += 1
