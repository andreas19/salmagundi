"""Stop watch.

.. versionadded:: 0.12.0
"""

import time

__all__ = ['StopWatch', 'StopWatchError']


class StopWatchError(Exception):
    """Raised by :class:`StopWatch` if an action is not allowed.

    .. versionadded:: 0.12.0
    """


class StopWatch:
    """Simple stop watch.

    :param bool start: if ``True`` the stop watch starts immediately

    .. versionadded:: 0.12.0
    """

    def __init__(self, start=True):
        self._diff = None
        self._start = None
        if start:
            self.start()

    @property
    def started(self):
        """Return whether the stop watch has been started."""
        return self._diff is not None

    @property
    def running(self):
        """Return whether the stop watch is running."""
        return self._start is not None

    def start(self):
        """Start or restart the stop watch.

        :raises StopWatchError: if the stop watch is running
        """
        if self.running:
            raise StopWatchError('stop watch is running')
        if not self.started:
            self._diff = 0
        self._start = time.time()

    def pause(self):
        """Pause the stop watch.

        Does not reset the stop watch.

        :return: the elapsed time in seconds
        :rtype: float
        :raises StopWatchError: if the stop watch is not running
        """
        if not self.running:
            raise StopWatchError('stop watch is not running')
        self._diff += time.time() - self._start
        self._start = None
        return self._diff

    def stop(self):
        """Stop and reset the stop watch.

        :return: the elapsed time in seconds
        :rtype: float
        :raises StopWatchError: if the stop watch is not running
        """
        diff = self.pause()
        self.reset()
        return diff

    def reset(self):
        """Reset the stop watch.

        :raises StopWatchError: if the stop watch is running
        """
        if self.running:
            raise StopWatchError('stop watch is running')
        self._diff = None
        self._start = None

    def time(self):
        """Get elapsed time from the stop watch.

        :return: the currently elapsed time in seconds
        :rtype: float
        :raises StopWatchError: if the stop watch has not been started
        """
        if not self.started:
            raise StopWatchError('stop watch has not been started')
        if self.running:
            return self._diff + (time.time() - self._start)
        return self._diff
