"""
Live console tracer for the Startup Idea Validator.

Subscribes to EventBus events and prints a colourised trace to stdout
so you can watch the multi-agent pipeline execute in real time.
"""

from __future__ import annotations

import time as _time
from datetime import timezone


# ── ANSI colour helpers ───────────────────────────────────────────────────────

_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_RED    = "\033[91m"
_GREEN  = "\033[92m"
_YELLOW = "\033[93m"
_BLUE   = "\033[94m"
_MAGENTA= "\033[95m"
_CYAN   = "\033[96m"
_WHITE  = "\033[97m"
_ORANGE = "\033[33m"


def _ts(event) -> str:
    try:
        dt = event.timestamp.astimezone(timezone.utc)
        return dt.strftime("%H:%M:%S.") + f"{dt.microsecond // 1000:03d}"
    except Exception:
        return "??:??:??.???"


def _line(colour: str, label: str, body: str, event) -> None:
    print(f"{_DIM}{_ts(event)}{_RESET}  {colour}{_BOLD}{label:<12}{_RESET}  {body}")


# ── Individual event handlers ─────────────────────────────────────────────────

def _on_agent_registered(e) -> None:
    _line(_DIM + _WHITE, "[REGISTRY]", f"agent_registered  name={e.agent_name}  type={e.agent_type}", e)


def _on_agent_spawned(e) -> None:
    _line(_CYAN, "[SPAWN]",
          f"agent_spawned  name={_BOLD}{e.agent_name}{_RESET}{_CYAN}  "
          f"parent={e.parent_agent or '(none)'}  "
          f"tools={'✓' if e.inherited_tools else '✗'}  "
          f"skills={'✓' if e.inherited_skills else '✗'}", e)


def _on_spawn_error(e) -> None:
    _line(_RED, "[SPAWN-ERR]", f"agent_spawn_error  name={e.agent_name}  error={e.error}", e)


def _on_delegation_started(e) -> None:
    preview = e.task_preview[:60].replace("\n", " ")
    _line(_YELLOW, "[DELEGATE>]",
          f"delegation_started  to={_BOLD}{e.delegating_to}{_RESET}{_YELLOW}  "
          f"depth={e.depth}  task=\"{preview}...\"", e)


def _on_delegation_completed(e) -> None:
    _line(_GREEN, "[DELEGATE<]",
          f"delegation_completed  to={_BOLD}{e.delegating_to}{_RESET}{_GREEN}  "
          f"depth={e.depth}  duration={e.duration_ms:.0f}ms", e)


def _on_delegation_error(e) -> None:
    _line(_RED, "[DELEG-ERR]", f"delegation_error  to={e.delegating_to}  error={e.error}", e)


def _on_tool_registered(e) -> None:
    _line(_DIM, "[TOOL-REG]", f"tool_registered  name={e.tool_name}", e)


def _on_tool_called(e) -> None:
    status = f"{_GREEN}ok{_RESET}" if e.success else f"{_RED}FAIL{_RESET}"
    _line(_MAGENTA, "[TOOL]",
          f"tool_called  name={_BOLD}{e.tool_name}{_RESET}{_MAGENTA}  "
          f"status={status}  duration={e.duration_ms:.1f}ms", e)


def _on_health_changed(e) -> None:
    _line(_ORANGE, "[HEALTH]",
          f"health_changed  name={e.agent_name}  {e.old_status}->{e.new_status}", e)


# ── Public setup ──────────────────────────────────────────────────────────────

def setup_tracer(bus) -> None:
    """Subscribe all typed listeners to *bus*."""
    bus.subscribe("agent.registered",    _on_agent_registered)
    bus.subscribe("agent.spawned",       _on_agent_spawned)
    bus.subscribe("agent.spawn_error",   _on_spawn_error)
    bus.subscribe("delegation.started",  _on_delegation_started)
    bus.subscribe("delegation.completed",_on_delegation_completed)
    bus.subscribe("delegation.error",    _on_delegation_error)
    bus.subscribe("tool.registered",     _on_tool_registered)
    bus.subscribe("tool.called",         _on_tool_called)
    bus.subscribe("agent.health_changed",_on_health_changed)


def print_section(title: str) -> None:
    """Print a section divider."""
    width = 70
    print(f"\n{_BOLD}{_BLUE}{'─' * width}{_RESET}")
    print(f"{_BOLD}{_BLUE}  {title}{_RESET}")
    print(f"{_BOLD}{_BLUE}{'─' * width}{_RESET}\n")
