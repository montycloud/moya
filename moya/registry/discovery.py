"""
Agent discovery and health-checking for Moya's enhanced registry.
"""

import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from moya.agents.agent import Agent
    from moya.agents.agent_info import AgentInfo


@dataclass
class HealthCheckerConfig:
    interval_seconds: float = 60.0
    timeout_seconds: float = 5.0
    max_failures_before_unhealthy: int = 3


class HealthChecker:
    """
    Background daemon thread that periodically calls each registered agent's
    health probe and updates its HealthStatus.

    Usage::

        checker = HealthChecker(config=HealthCheckerConfig(interval_seconds=30))
        checker.start()
        # ... add agents via register() / unregister() ...
        checker.stop()
    """

    def __init__(
        self,
        config: Optional[HealthCheckerConfig] = None,
        on_status_change: Optional[Callable[["AgentInfo", str, str], None]] = None,
    ) -> None:
        self._config = config or HealthCheckerConfig()
        self._on_status_change = on_status_change
        self._agents: Dict[str, "Agent"] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def register(self, agent: "Agent") -> None:
        with self._lock:
            self._agents[agent.agent_name] = agent

    def unregister(self, agent_name: str) -> None:
        with self._lock:
            self._agents.pop(agent_name, None)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="moya-health-checker",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            self._run_checks()
            self._stop_event.wait(timeout=self._config.interval_seconds)

    def _run_checks(self) -> None:
        with self._lock:
            agents = list(self._agents.values())

        for agent in agents:
            self._check(agent)

    def _check(self, agent: "Agent") -> None:
        info = getattr(agent, "_agent_info", None)
        if info is None:
            return

        old_status = info.health.status
        try:
            # Agents may optionally expose a health_check() method.
            # Fall back to a lightweight handle_message ping.
            if hasattr(agent, "health_check"):
                agent.health_check()
            else:
                agent.handle_message(
                    thread_id="__health__",
                    user_message="ping",
                    stream=False,
                )
            info.health.mark_success()
        except Exception as exc:
            info.health.mark_failure(
                str(exc),
                self._config.max_failures_before_unhealthy,
            )

        new_status = info.health.status
        if new_status != old_status and self._on_status_change:
            try:
                self._on_status_change(info, old_status, new_status)
            except Exception:
                pass
