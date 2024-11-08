# -*- coding: utf-8 -*-

from collections import defaultdict
from logging import getLogger

import six

from dictrack.events import EVENT_ALL, EVENT_TRACKER_ADDED, BaseEvent, TrackerEvent
from dictrack.trackers import BaseTracker, ResetPolicy
from dictrack.utils.utils import (
    typecheck,
    valid_callable,
    valid_elements_type,
    valid_obj,
    valid_type,
)

logger = getLogger("dictrack.tracking_manager")


class TrackingManager(object):
    @typecheck()
    def __init__(self, data_cache, data_store):
        """
        Manages tracking operations across data cache and data store, handling trackers and tracking events.

        Parameters
        ----------
        data_cache : BaseDataCache
            The data cache instance for managing cached trackers.
        data_store : BaseDataStore
            The data store instance for permanent tracker storage.
        """
        self.data_cache = data_cache
        self.data_cache.data_store = data_store
        self.data_cache.forward_cb = self._dispatch_event
        self.data_store = data_store
        self.data_store.data_cache = data_cache
        self.data_cache.start_scheduler()
        self.data_store.start_scheduler()

        self._listeners = defaultdict(list)

    def add_listener(self, code, cb):
        """
        Add a listener callback for a specific event code.

        Parameters
        ----------
        code : int
            The event code that the listener will respond to. Must be a valid value within `EVENT_ALL`.
        cb : callable
            The callback function to execute when the specified event occurs.

        Raises
        ------
        ValueError
            If `code` is not within the valid event codes in `EVENT_ALL`.
        TypeError
            If `cb` is not a callable function or object.

        Notes
        -----
        Multiple listeners can be registered for the same event code, and each will be called
        when the event is dispatched.
        """
        valid_obj(code, EVENT_ALL)
        valid_callable(cb)

        self._listeners[code].append(cb)

    @typecheck()
    def add_tracker(self, group_id, tracker, expire=None, expire_at=None, **kwargs):
        """
        Add a single tracker to a specified group and store it in both cache and data store.

        Parameters
        ----------
        group_id : str
            The ID of the group to which the tracker belongs.
        tracker : BaseTracker
            The tracker instance to add.
        expire : int, optional
            Expiration time for the tracker in seconds. Defaults to `None`.
        expire_at : int, optional
            Specific expiration timestamp for the tracker. Defaults to `None`.
        **kwargs : dict
            Additional keyword arguments for customization.

        Raises
        ------
        TypeError
            If `expire` or `expire_at` is not an integer or `None`.

        Notes
        -----
        Dispatches a `TrackerEvent` with `EVENT_TRACKER_ADDED` after adding the tracker.
        """
        valid_type(expire, six.integer_types, allow_empty=True)
        valid_type(expire_at, six.integer_types, allow_empty=True)

        tracker.group_id = group_id

        self.data_store.store(
            group_id, tracker, expire=expire, expire_at=expire_at, **kwargs
        )
        # Group already cached, sync tracker immediately
        if self.data_cache.is_cached(group_id):
            self.data_cache.cache(group_id, tracker, **kwargs)

        self._dispatch_event(
            TrackerEvent(EVENT_TRACKER_ADDED, group_id, tracker.name, tracker)
        )

    @typecheck()
    def add_trackers(self, group_id, trackers, expire=None, expire_at=None, **kwargs):
        """
        Add multiple trackers to a specified group and store them in both cache and data store.

        Parameters
        ----------
        group_id : str
            The ID of the group to which the trackers belongs.
        trackers : list of BaseTracker
            List of tracker instances to add.
        expire : int, optional
            Expiration time for the trackers in seconds. Defaults to `None`.
        expire_at : int, optional
            Specific expiration timestamp for the trackers. Defaults to `None`.
        **kwargs : dict
            Additional keyword arguments for customization.

        Raises
        ------
        TypeError
            If any tracker in `trackers` is not an instance of `BaseTracker`,
            or if `expire` or `expire_at` are not integers.

        Notes
        -----
        Dispatches a `TrackerEvent` with `EVENT_TRACKER_ADDED` for each tracker after adding.
        """
        valid_elements_type(trackers, BaseTracker)
        valid_type(expire, six.integer_types, allow_empty=True)
        valid_type(expire_at, six.integer_types, allow_empty=True)

        for tracker in trackers:
            tracker.group_id = group_id

        self.data_store.store_all(
            group_id, trackers, expire=expire, expire_at=expire_at, **kwargs
        )
        # Group already cached, sync trackers immediately
        if self.data_cache.is_cached(group_id):
            self.data_cache.cache_all(group_id, trackers, **kwargs)

        for tracker in trackers:
            self._dispatch_event(
                TrackerEvent(EVENT_TRACKER_ADDED, group_id, tracker.name, tracker)
            )

    @typecheck()
    def get_trackers(self, group_id, name=None):
        """
        Retrieve tracker(s) by group ID and optional tracker name(s).

        Parameters
        ----------
        group_id : str
            The ID of the group from which to retrieve trackers.
        name : str or list of str, optional
            Name(s) of specific trackers to retrieve. If `None`, retrieves all trackers in the group.
            Defaults to `None`.

        Returns
        -------
        list of BaseTracker
            List of retrieved tracker instances. Returns an empty list if retrieval fails.

        Raises
        ------
        TypeError
            If `name` is not a string, list, or `None`.
        """
        valid_type(name, six.string_types + (list,), allow_empty=True)

        if self.data_cache.is_cached(group_id):
            return self.data_cache.fetch(group_id, name=name)
        else:
            is_ok, trackers = self.data_store.load(group_id, name=name)
            if not is_ok:
                logger.error("Get trackers failed in group ({})".format(group_id))

                return []
            else:
                return trackers

    @typecheck()
    def update_tracker(self, group_id, tracker):
        """
        Update a tracker in both the cache and data store. If the tracker is already cached,
        it will be updated in the cache with `force=True`. Otherwise, it is stored directly
        in the data store.

        Parameters
        ----------
        group_id : str
            The ID of the group to which the tracker belongs.
        tracker : BaseTracker
            The tracker instance to be updated.

        Raises
        ------
        TypeError
            If `tracker` is not an instance of `BaseTracker`.
        """
        if self.data_cache.is_cached(group_id, name=tracker.name):
            self.data_cache.cache(group_id, tracker, force=True)
        else:
            self.data_store.store(group_id, tracker)

    @typecheck()
    def remove_tracker(self, group_id, name=None):
        """
        Remove a tracker or multiple trackers from both the cache and data store.

        Parameters
        ----------
        group_id : str
            The ID of the group from which to remove the tracker(s).
        name : str or list of str, optional
            Name(s) of specific trackers to remove. If `None`, removes all trackers in the group.
            Defaults to `None`.

        Raises
        ------
        TypeError
            If `name` is not a string, list, or `None`.
        """
        valid_type(name, six.string_types + (list,), allow_empty=True)

        self.data_cache.remove(group_id, name=name)
        self.data_store.remove(group_id, name=name)

    @typecheck()
    def reset_tracker(self, group_id, name, reset_policy=None):
        """
        Reset a tracker in a specified group according to the provided reset policy.

        Parameters
        ----------
        group_id : str
            The ID of the group to which the tracker belongs.
        name : str
            The name of the tracker to reset.
        reset_policy : int, optional
            The reset policy to apply, controlling which aspects of the tracker to reset.
            Must be a valid value within the `ResetPolicy` range. Defaults to `None`,
            using the tracker's default policy.
            Supports bitwise combination using `|` to apply multiple reset policies simultaneously
            (e.g., `ResetPolicy.PROGRESS | ResetPolicy.LIMITER`).

        Returns
        -------
        bool
            `True` if the tracker was found and reset successfully; `False` if the tracker was not found.

        Raises
        ------
        TypeError
            If `name` is not a string or if `reset_policy` is not a valid integer within `ResetPolicy` range.

        Notes
        -----
        Dispatches reset events through the tracker's `forward_event` method and updates the tracker after reset.
        """
        valid_type(name, six.string_types)
        valid_obj(reset_policy, list(six.moves.range(ResetPolicy.ALL + 1)))

        tracker = self.get_tracker(group_id, name)
        if tracker is None:
            return False

        tracker.forward_event(self._dispatch_event)
        tracker.reset(reset_policy=reset_policy)
        self.update_tracker(group_id, tracker)

        return True

    @typecheck()
    def track(self, group_id, data, **kwargs):
        """
        Tracking for a specified group, updating cached trackers with provided data.

        Parameters
        ----------
        group_id : str
            The ID of the group for which to track the event.
        data : dict
            The data associated with the event to be tracked.
        **kwargs : dict
            Additional keyword arguments for customization.

        Returns
        -------
        tuple
            A tuple containing:
            - `bool`: `True` if tracking was successful; `False` if loading trackers failed.
            - `list of BaseTracker`: Trackers that were modified (dirtied) during tracking.
            - `list of BaseTracker`: Trackers that were completed during tracking.
            - `list of BaseTracker`: Trackers that hit a limit during tracking.

        Notes
        -----
        If the group is not already cached, trackers are loaded from the data store and cached before tracking.
        """
        if not self.data_cache.is_cached(group_id):
            is_ok, trackers = self.data_store.load(group_id, **kwargs)
            if not is_ok:
                logger.error(
                    "Load from data store failed in group_id ({})".format(group_id)
                )

                return False, [], [], []

            self.data_cache.cache_all(group_id, trackers, **kwargs)

        dirtied_trackers, completed_trackers, limited_trackers = self.data_cache.track(
            group_id, data, **kwargs
        )

        return True, dirtied_trackers, completed_trackers, limited_trackers

    def flush(self, confirm=False):
        """
        Clear all cached and stored data permanently.

        Parameters
        ----------
        confirm : bool, optional
            Confirmation flag to execute flush. Must be `True` to proceed. Defaults to `False`.

        Returns
        -------
        None

        Notes
        -----
        This action is irreversible and will remove all data from both cache and data store.
        """
        if not confirm:
            logger.warning(
                "This action is irreversible; please proceed with caution. "
                "If you are sure, pass `confirm=True` to proceed"
            )
            return

        logger.info("Starting FLUSH procedure")

        self.data_cache.flush()
        self.data_store.flush()

        logger.info("Finished FLUSH procedure")

    def _dispatch_event(self, event):
        valid_type(event, BaseEvent)

        for cb in self._listeners[event.code]:
            try:
                cb(event)
            except Exception as e:
                logger.exception(
                    "Notify listener ({}) failed, {}".format(cb.__name__, e.__repr__())
                )
