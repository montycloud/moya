"""Tests for AgentInfo extensions: HealthStatus and TTL."""

import time
import pytest
from datetime import datetime, timezone, timedelta

from moya.agents.agent_info import AgentInfo, HealthStatus


# ── HealthStatus ──────────────────────────────────────────────────────────────

def test_initial_status_unknown():
    h = HealthStatus()
    assert h.status == "unknown"
    assert h.consecutive_failures == 0
    assert not h.is_healthy()


def test_mark_success():
    h = HealthStatus()
    h.mark_success()
    assert h.status == "healthy"
    assert h.is_healthy()
    assert h.consecutive_failures == 0
    assert h.last_error is None
    assert h.last_checked is not None


def test_mark_success_resets_failures():
    h = HealthStatus()
    h.mark_failure("err")
    h.mark_failure("err")
    h.mark_success()
    assert h.consecutive_failures == 0
    assert h.status == "healthy"


def test_mark_failure_degraded_below_threshold():
    h = HealthStatus()
    h.mark_failure("timeout", max_failures_before_unhealthy=3)
    assert h.status == "degraded"
    assert h.consecutive_failures == 1
    assert h.last_error == "timeout"


def test_mark_failure_unhealthy_at_threshold():
    h = HealthStatus()
    for _ in range(3):
        h.mark_failure("err", max_failures_before_unhealthy=3)
    assert h.status == "unhealthy"
    assert h.consecutive_failures == 3


def test_mark_failure_updates_last_checked():
    h = HealthStatus()
    before = datetime.now(timezone.utc)
    h.mark_failure("err")
    assert h.last_checked >= before


# ── AgentInfo backward compatibility ─────────────────────────────────────────

def test_positional_construction():
    info = AgentInfo("agent1", "Does things", "openai")
    assert info.name == "agent1"
    assert info.description == "Does things"
    assert info.type == "openai"


def test_defaults():
    info = AgentInfo("a", "b", "openai")
    assert info.skills == []
    assert info.tags == []
    assert info.endpoint is None
    assert info.version == "1.0.0"
    assert info.modalities == []
    assert info.capability_schema == {}
    assert info.ttl_seconds is None


def test_skills_and_tags():
    info = AgentInfo("a", "b", "openai", skills=["s1"], tags=["t1"])
    assert info.skills == ["s1"]
    assert info.tags == ["t1"]


def test_health_attached():
    info = AgentInfo("a", "b", "openai")
    assert isinstance(info.health, HealthStatus)
    assert info.health.status == "unknown"


def test_registered_at_auto_set():
    before = datetime.now(timezone.utc)
    info = AgentInfo("a", "b", "openai")
    assert info.registered_at >= before


def test_registered_at_custom():
    ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
    info = AgentInfo("a", "b", "openai", registered_at=ts)
    assert info.registered_at == ts


# ── TTL / expiry ──────────────────────────────────────────────────────────────

def test_not_expired_without_ttl():
    info = AgentInfo("a", "b", "openai")
    assert not info.is_expired()


def test_not_expired_within_ttl():
    info = AgentInfo("a", "b", "openai", ttl_seconds=3600)
    assert not info.is_expired()


def test_expired_when_ttl_zero():
    info = AgentInfo("a", "b", "openai", ttl_seconds=0)
    time.sleep(0.01)
    assert info.is_expired()


def test_expired_with_past_registered_at():
    past = datetime.now(timezone.utc) - timedelta(seconds=10)
    info = AgentInfo("a", "b", "openai", ttl_seconds=5, registered_at=past)
    assert info.is_expired()


def test_not_expired_with_future_registration():
    future = datetime.now(timezone.utc) + timedelta(seconds=100)
    info = AgentInfo("a", "b", "openai", ttl_seconds=50, registered_at=future)
    assert not info.is_expired()
