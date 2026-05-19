"""
Moya observability events.

All events are plain dataclasses — no imports from other moya modules
to keep the dependency graph clean.

Note: all fields have defaults so that subclasses can safely override
``event_type`` without triggering the dataclass "non-default follows default"
constraint.  Required fields should be passed as keyword arguments.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class MoyaEvent:
    """Base class for all Moya observability events."""
    event_type: str = ""
    source: str = ""
    timestamp: datetime = field(default_factory=_now)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ── Agent events ──────────────────────────────────────────────────────────────

@dataclass
class AgentEvent(MoyaEvent):
    agent_name: str = ""
    agent_type: str = ""


@dataclass
class AgentRegisteredEvent(AgentEvent):
    event_type: str = "agent.registered"


@dataclass
class AgentRemovedEvent(AgentEvent):
    event_type: str = "agent.removed"


@dataclass
class AgentHealthChangedEvent(AgentEvent):
    old_status: str = ""
    new_status: str = ""
    event_type: str = "agent.health_changed"


# ── Tool events ───────────────────────────────────────────────────────────────

@dataclass
class ToolEvent(MoyaEvent):
    tool_name: str = ""


@dataclass
class ToolRegisteredEvent(ToolEvent):
    event_type: str = "tool.registered"


@dataclass
class ToolCalledEvent(ToolEvent):
    arguments: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    event_type: str = "tool.called"


# ── Pipeline / step events ────────────────────────────────────────────────────

@dataclass
class PipelineEvent(MoyaEvent):
    pipeline_id: str = ""
    thread_id: str = ""


@dataclass
class PipelineStartedEvent(PipelineEvent):
    event_type: str = "pipeline.started"


@dataclass
class PipelineCompletedEvent(PipelineEvent):
    duration_ms: float = 0.0
    event_type: str = "pipeline.completed"


@dataclass
class PipelineErrorEvent(PipelineEvent):
    error: str = ""
    event_type: str = "pipeline.error"


@dataclass
class StepEvent(PipelineEvent):
    step_name: str = ""
    step_type: str = ""


@dataclass
class StepStartedEvent(StepEvent):
    event_type: str = "step.started"


@dataclass
class StepCompletedEvent(StepEvent):
    duration_ms: float = 0.0
    event_type: str = "step.completed"


@dataclass
class StepErrorEvent(StepEvent):
    error: str = ""
    event_type: str = "step.error"
