# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

try:
    import cPickle as pickle  # type: ignore
except ImportError:
    import pickle


import six


class BaseDataStore(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def add_tracker(self, tracker):
        """_summary_"""

    @abstractmethod
    def get_tracker(self, group_id, name):
        """_summary_"""

    @abstractmethod
    def get_trackers(self, group_id):
        """_summary_"""

    @abstractmethod
    def update_tracker(self, tracker):
        """_summary_"""

    @abstractmethod
    def track(self, group_id, data):
        """_summary_"""

    @abstractmethod
    def remove_tracker(self, group_id, name):
        """_summary_"""

    @abstractmethod
    def reset_all(self):
        """_summary_"""

    def _serialize(self, tracker):
        """
        Serialize tracker for storing to datasource.

        :param `BaseTracker` tracker: The tracker instance to be serialized.
        """
        return pickle.dumps(tracker.__getstate__(), protocol=2)

    def _deserialize(self, b_tracker):
        """
        Deserialize a byte stream into a tracker.

        :param `bytes` b_tracker: The byte stream representing the serialized tracker.
        :return: The deserialized tracker instance.
        :rtype: `BaseTracker`
        """
        state = pickle.loads(b_tracker)
        tracker = state["cls"].__new__(state["cls"])
        tracker.__setstate__(state)

        return tracker

    def _deserialize_list(self, b_trackers):
        """
        Deserialize a list of byte streams into a list of trackers.

        :param `list[bytes]` b_trackers: A list of byte streams representing serialized trackers.
        :return: A list of deserialized tracker instances.
        :rtype: `list[BaseTracker]`
        """
        trackers = []
        for b_tracker in b_trackers:
            trackers.append(self._deserialize(b_tracker))

        return trackers
