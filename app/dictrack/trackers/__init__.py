from dictrack.trackers.base import BaseTracker
from dictrack.trackers.numerics import *  # noqa: F403
from dictrack.utils.utils import GLOBAL_DEFINES

GLOBAL_DEFINES.update({"tracker": BaseTracker})
