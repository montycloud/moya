"""
Moya Observability — event bus, events, and built-in listeners.

Quick start::

    from moya.observability import get_event_bus, LoggingListener
    bus = get_event_bus()
    bus.subscribe("*", LoggingListener())
"""

from moya.observability.event_bus import EventBus, get_event_bus, set_event_bus
from moya.observability.events import (
    MoyaEvent,
    AgentEvent,
    AgentRegisteredEvent,
    AgentRemovedEvent,
    AgentHealthChangedEvent,
    ToolEvent,
    ToolRegisteredEvent,
    ToolCalledEvent,
    PipelineEvent,
    PipelineStartedEvent,
    PipelineCompletedEvent,
    PipelineErrorEvent,
    StepEvent,
    StepStartedEvent,
    StepCompletedEvent,
    StepErrorEvent,
)
from moya.observability.listeners import (
    EventListener,
    LoggingListener,
    CallbackListener,
    FilteredListener,
)

__all__ = [
    "EventBus",
    "get_event_bus",
    "set_event_bus",
    # Events
    "MoyaEvent",
    "AgentEvent",
    "AgentRegisteredEvent",
    "AgentRemovedEvent",
    "AgentHealthChangedEvent",
    "ToolEvent",
    "ToolRegisteredEvent",
    "ToolCalledEvent",
    "PipelineEvent",
    "PipelineStartedEvent",
    "PipelineCompletedEvent",
    "PipelineErrorEvent",
    "StepEvent",
    "StepStartedEvent",
    "StepCompletedEvent",
    "StepErrorEvent",
    # Listeners
    "EventListener",
    "LoggingListener",
    "CallbackListener",
    "FilteredListener",
]
