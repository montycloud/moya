"""
Thread-safe event bus for Moya observability.

Usage::

    from moya.observability.event_bus import get_event_bus
    bus = get_event_bus()
    bus.subscribe("tool.called", my_listener)
    bus.publish(ToolCalledEvent(...))
"""

import threading
from typing import Callable, Dict, List, Optional

from moya.observability.events import MoyaEvent

_bus_lock = threading.Lock()
_default_bus: Optional["EventBus"] = None


class EventBus:
    """
    Publish/subscribe bus for MoyaEvent instances.

    Listeners are called synchronously in the publishing thread.
    Exceptions inside a listener are swallowed so one bad listener
    cannot break others or the calling code.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._typed: Dict[str, List[Callable[[MoyaEvent], None]]] = {}
        self._global: List[Callable[[MoyaEvent], None]] = []

    def subscribe(self, event_type: str, listener: Callable[[MoyaEvent], None]) -> None:
        """
        Subscribe *listener* to *event_type*.

        Use ``"*"`` to receive every event regardless of type.
        Subscribing the same listener twice is a no-op.
        """
        with self._lock:
            if event_type == "*":
                if listener not in self._global:
                    self._global.append(listener)
            else:
                bucket = self._typed.setdefault(event_type, [])
                if listener not in bucket:
                    bucket.append(listener)

    def unsubscribe(self, event_type: str, listener: Callable[[MoyaEvent], None]) -> None:
        """Remove a previously registered listener."""
        with self._lock:
            if event_type == "*":
                self._global = [l for l in self._global if l is not listener]
            elif event_type in self._typed:
                self._typed[event_type] = [
                    l for l in self._typed[event_type] if l is not listener
                ]

    def publish(self, event: MoyaEvent) -> None:
        """
        Deliver *event* to all matching listeners.

        Typed listeners (matching ``event.event_type``) are called first,
        then global (``"*"``) listeners.  Errors are isolated.
        """
        with self._lock:
            typed = list(self._typed.get(event.event_type, []))
            glob = list(self._global)

        for listener in typed + glob:
            try:
                listener(event)
            except Exception:
                pass

    def clear(self) -> None:
        """Remove all listeners — mainly useful in tests."""
        with self._lock:
            self._typed.clear()
            self._global.clear()


def get_event_bus() -> EventBus:
    """Return (and lazily create) the process-wide default EventBus."""
    global _default_bus
    with _bus_lock:
        if _default_bus is None:
            _default_bus = EventBus()
        return _default_bus


def set_event_bus(bus: EventBus) -> None:
    """Replace the process-wide default EventBus (useful for testing)."""
    global _default_bus
    with _bus_lock:
        _default_bus = bus
