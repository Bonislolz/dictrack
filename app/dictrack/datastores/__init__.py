from dictrack.datastores.base import BaseDataStore
from dictrack.datastores.memory import *  # noqa: F403
from dictrack.datastores.redis import *  # noqa: F403
from dictrack.utils.utils import GLOBAL_DEFINES

GLOBAL_DEFINES.update({"datastore": BaseDataStore})
