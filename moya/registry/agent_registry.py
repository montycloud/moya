"""
AgentRegistry for Moya — enhanced with health checks, TTL, semantic search,
and observability event emission.
"""

from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

from moya.agents.agent import Agent
from moya.agents.agent_info import AgentInfo
from moya.registry.agent_repository import AgentRepository
from moya.registry.in_memory_agent_repository import InMemoryAgentRepository

if TYPE_CHECKING:
    from moya.observability.event_bus import EventBus
    from moya.registry.discovery import HealthChecker, HealthCheckerConfig


@dataclass
class AgentRegistryConfig:
    """Optional configuration for AgentRegistry features."""
    enable_health_checks: bool = False
    health_checker_config: Optional["HealthCheckerConfig"] = None
    prune_expired_on_list: bool = True


class AgentRegistry:
    """
    AgentRegistry holds references to Agent instances in a repository
    and provides methods to register, remove, and discover them at runtime.

    New in this version:

    * **Event emission** — pass an *event_bus* to receive
      ``AgentRegisteredEvent``, ``AgentRemovedEvent``, and
      ``AgentHealthChangedEvent``.
    * **TTL pruning** — agents whose ``AgentInfo.ttl_seconds`` has elapsed
      are automatically excluded from ``list_agents()`` (and optionally
      removed from the repository).
    * **Health checking** — opt-in background health checker via
      ``AgentRegistryConfig(enable_health_checks=True)``.
    * **Keyword search** — ``search_agents()`` ranks by name / description
      relevance.
    """

    def __init__(
        self,
        repository: Optional[AgentRepository] = None,
        event_bus: Optional["EventBus"] = None,
        config: Optional[AgentRegistryConfig] = None,
    ):
        self.repository = repository or InMemoryAgentRepository()
        self._event_bus = event_bus
        self._config = config or AgentRegistryConfig()
        self._health_checker: Optional["HealthChecker"] = None

        if self._config.enable_health_checks:
            self._start_health_checker()

    # ── Core CRUD ─────────────────────────────────────────────────────────────

    def register_agent(self, agent: Agent) -> None:
        self.repository.save_agent(agent)
        if self._health_checker:
            self._health_checker.register(agent)
        self._emit_registered(agent)

    def remove_agent(self, agent_name: str) -> None:
        self.repository.remove_agent(agent_name)
        if self._health_checker:
            self._health_checker.unregister(agent_name)
        self._emit_removed(agent_name)

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        return self.repository.get_agent(agent_name)

    # ── Discovery ─────────────────────────────────────────────────────────────

    def list_agents(self) -> List[AgentInfo]:
        """List all registered agents, excluding expired ones."""
        infos = self.repository.list_agents()
        if not self._config.prune_expired_on_list:
            return infos
        alive = []
        for info in infos:
            if info.is_expired():
                self.repository.remove_agent(info.name)
            else:
                alive.append(info)
        return alive

    def find_agents_by_type(self, agent_type: str) -> List[Agent]:
        return [
            self.repository.get_agent(info.name)
            for info in self.list_agents()
            if info.type == agent_type
            and self.repository.get_agent(info.name) is not None
        ]

    def find_agents_by_description(self, search_text: str) -> List[Agent]:
        """Case-insensitive substring match on description."""
        q = search_text.lower()
        return [
            self.repository.get_agent(info.name)
            for info in self.list_agents()
            if q in info.description.lower()
            and self.repository.get_agent(info.name) is not None
        ]

    def find_agents_with_skill(self, skill_name: str) -> List[Agent]:
        return [
            self.repository.get_agent(info.name)
            for info in self.list_agents()
            if skill_name in info.skills
            and self.repository.get_agent(info.name) is not None
        ]

    def find_agents_by_tag(self, tag: str) -> List[Agent]:
        return [
            self.repository.get_agent(info.name)
            for info in self.list_agents()
            if tag in info.tags
            and self.repository.get_agent(info.name) is not None
        ]

    def search_agents(self, query: str) -> List[Agent]:
        """
        Keyword search over agent name, description, tags, and type.

        Results are ranked by number of matching fields (most matches first).
        """
        q = query.lower()
        scored: List[tuple] = []
        for info in self.list_agents():
            score = 0
            if q in info.name.lower():
                score += 3
            if q in info.description.lower():
                score += 2
            if any(q in t.lower() for t in info.tags):
                score += 1
            if q in info.type.lower():
                score += 1
            if score > 0:
                agent = self.repository.get_agent(info.name)
                if agent:
                    scored.append((score, agent))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [agent for _, agent in scored]

    def find_healthy_agents(self) -> List[Agent]:
        """Return agents whose HealthStatus is 'healthy'."""
        return [
            self.repository.get_agent(info.name)
            for info in self.list_agents()
            if info.health.is_healthy()
            and self.repository.get_agent(info.name) is not None
        ]

    # ── Health checker ────────────────────────────────────────────────────────

    def _start_health_checker(self) -> None:
        from moya.registry.discovery import HealthChecker
        self._health_checker = HealthChecker(
            config=self._config.health_checker_config,
            on_status_change=self._on_health_change,
        )
        # Register any already-known agents
        for info in self.repository.list_agents():
            agent = self.repository.get_agent(info.name)
            if agent:
                self._health_checker.register(agent)
        self._health_checker.start()

    def stop_health_checker(self) -> None:
        if self._health_checker:
            self._health_checker.stop()

    def _on_health_change(self, info: AgentInfo, old_status: str, new_status: str) -> None:
        if self._event_bus is None:
            return
        try:
            from moya.observability.events import AgentHealthChangedEvent
            self._event_bus.publish(AgentHealthChangedEvent(
                source="AgentRegistry",
                agent_name=info.name,
                agent_type=info.type,
                old_status=old_status,
                new_status=new_status,
            ))
        except Exception:
            pass

    # ── Event emission ────────────────────────────────────────────────────────

    def _emit_registered(self, agent: Agent) -> None:
        if self._event_bus is None:
            return
        try:
            from moya.observability.events import AgentRegisteredEvent
            self._event_bus.publish(AgentRegisteredEvent(
                source="AgentRegistry",
                agent_name=agent.agent_name,
                agent_type=agent.agent_type,
            ))
        except Exception:
            pass

    def _emit_removed(self, agent_name: str) -> None:
        if self._event_bus is None:
            return
        try:
            from moya.observability.events import AgentRemovedEvent
            self._event_bus.publish(AgentRemovedEvent(
                source="AgentRegistry",
                agent_name=agent_name,
            ))
        except Exception:
            pass
