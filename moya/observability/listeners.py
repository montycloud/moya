"""
Built-in EventListener implementations for Moya observability.
"""

import logging
from typing import Callable, Optional, runtime_checkable, Protocol

from moya.observability.events import MoyaEvent


@runtime_checkable
class EventListener(Protocol):
    """Protocol satisfied by any callable that accepts a MoyaEvent."""
    def __call__(self, event: MoyaEvent) -> None: ...


class LoggingListener:
    """
    Logs every event through Python's logging module.

    Usage::

        bus = get_event_bus()
        bus.subscribe("*", LoggingListener())
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        level: int = logging.DEBUG,
    ) -> None:
        self._logger = logger or logging.getLogger("moya.observability")
        self._level = level

    def __call__(self, event: MoyaEvent) -> None:
        self._logger.log(
            self._level,
            "[%s] source=%s ts=%s meta=%s",
            event.event_type,
            event.source,
            event.timestamp.isoformat(),
            event.metadata or {},
        )


class CallbackListener:
    """
    Wraps a plain callable as an EventListener.

    Usage::

        bus.subscribe("tool.called", CallbackListener(lambda e: print(e)))
    """

    def __init__(self, callback: Callable[[MoyaEvent], None]) -> None:
        self._callback = callback

    def __call__(self, event: MoyaEvent) -> None:
        self._callback(event)


class FilteredListener:
    """
    Wraps another listener and only forwards events that pass *predicate*.

    Usage::

        bus.subscribe("*", FilteredListener(
            predicate=lambda e: e.source == "my_agent",
            listener=LoggingListener(),
        ))
    """

    def __init__(
        self,
        predicate: Callable[[MoyaEvent], bool],
        listener: Callable[[MoyaEvent], None],
    ) -> None:
        self._predicate = predicate
        self._listener = listener

    def __call__(self, event: MoyaEvent) -> None:
        if self._predicate(event):
            self._listener(event)
