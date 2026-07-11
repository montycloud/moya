from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class HealthStatus:
    """Tracks the live health of a registered agent."""
    status: str = "unknown"          # "healthy" | "degraded" | "unhealthy" | "unknown"
    last_checked: Optional[datetime] = None
    consecutive_failures: int = 0
    last_error: Optional[str] = None

    def is_healthy(self) -> bool:
        return self.status == "healthy"

    def mark_success(self) -> None:
        self.status = "healthy"
        self.last_checked = _utcnow()
        self.consecutive_failures = 0
        self.last_error = None

    def mark_failure(self, error: str, max_failures_before_unhealthy: int = 3) -> None:
        self.consecutive_failures += 1
        self.last_checked = _utcnow()
        self.last_error = error
        if self.consecutive_failures >= max_failures_before_unhealthy:
            self.status = "unhealthy"
        else:
            self.status = "degraded"


@dataclass
class AgentInfo:
    """Metadata about a registered agent, used for discovery and routing."""

    name: str
    description: str
    type: str
    skills: List[str] = None       # skill names this agent supports
    tags: List[str] = None         # free-form labels for filtering
    endpoint: Optional[str] = None # URL for remote agents (A2A / HTTP)

    def __init__(
        self,
        name: str,
        description: str,
        type: str,
        skills: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        endpoint: Optional[str] = None,
        # Extended metadata
        version: str = "1.0.0",
        modalities: Optional[List[str]] = None,
        capability_schema: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[int] = None,
        registered_at: Optional[datetime] = None,
    ):
        self.name = name
        self.description = description
        self.type = type
        self.skills = skills or []
        self.tags = tags or []
        self.endpoint = endpoint
        self.version = version
        self.modalities = modalities or []
        self.capability_schema = capability_schema or {}
        self.ttl_seconds = ttl_seconds
        self.registered_at = registered_at or _utcnow()
        self.health: HealthStatus = HealthStatus()

    def is_expired(self) -> bool:
        """Return True if TTL has elapsed since registration."""
        if self.ttl_seconds is None:
            return False
        elapsed = (_utcnow() - self.registered_at).total_seconds()
        return elapsed > self.ttl_seconds
