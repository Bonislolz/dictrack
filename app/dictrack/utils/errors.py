# -*- coding: utf-8 -*-


class GroupIdAlreadySetError(ValueError):
    def __init__(self, old, new):
        super(GroupIdAlreadySetError, self).__init__(
            "Failed to set group id of tracker to {}, it's already assigned to {}.".format(
                new, old
            )
        )


class GroupIdDuplicateSetError(ValueError):
    def __init__(self, group_id):
        super(GroupIdDuplicateSetError, self).__init__(
            "The id of group ({}) is being redundantly set to the same value.".format(
                group_id
            )
        )


class TrackerLookupError(KeyError):
    def __init__(self, group_id, name):
        super(TrackerLookupError, self).__init__(
            "Tracker with name ({}) not found in group ({})".format(name, group_id)
        )


class GroupIdLookupError(KeyError):
    def __init__(self, group_id):
        super(GroupIdLookupError, self).__init__(
            "No group by the id of {} was found.".format(group_id)
        )


class NameLookupError(KeyError):
    def __init__(self, name):
        super(NameLookupError, self).__init__(
            "No tracker by the name of {} was found.".format(name)
        )


class ConflictingNameError(KeyError):
    def __init__(self, group_id, name):
        super(ConflictingNameError, self).__init__(
            "Tracker name ({}) conflicts with an existing tracker in the group ({}).".format(
                name, group_id
            )
        )


class TrackerAlreadyRemovedError(ValueError):
    def __init__(self, group_id, name):
        super(TrackerAlreadyRemovedError, self).__init__(
            "Tracker ({}) already removed in the group ({})".format(name, group_id)
        )


class TrackerAlreadyCompletedError(ValueError):
    def __init__(self, group_id, name):
        super(TrackerAlreadyCompletedError, self).__init__(
            "Tracker ({}) already completed in the group ({})".format(name, group_id)
        )


class DataStoreOperationError(IOError):
    pass


class RedisOperationError(DataStoreOperationError):
    def __init__(self, message):
        super(RedisOperationError, self).__init__("Redis: {}".format(message))
