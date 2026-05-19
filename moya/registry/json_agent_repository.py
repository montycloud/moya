"""
JSON-backed agent metadata catalog for Moya.

Persists AgentInfo records to a JSON file so the catalog survives
process restarts.  Agent *objects* (which contain non-serialisable
callables) are still held in memory; only their metadata is on disk.
"""

import json
import os
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

from moya.agents.agent import Agent
from moya.agents.agent_info import AgentInfo, HealthStatus
from moya.registry.agent_repository import AgentRepository


def _isoparse(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _info_to_dict(info: AgentInfo) -> dict:
    return {
        "name": info.name,
        "description": info.description,
        "type": info.type,
        "skills": info.skills,
        "tags": info.tags,
        "endpoint": info.endpoint,
        "version": info.version,
        "modalities": info.modalities,
        "capability_schema": info.capability_schema,
        "ttl_seconds": info.ttl_seconds,
        "registered_at": info.registered_at.isoformat() if info.registered_at else None,
    }


def _dict_to_info(d: dict) -> AgentInfo:
    return AgentInfo(
        name=d["name"],
        description=d.get("description", ""),
        type=d.get("type", "unknown"),
        skills=d.get("skills", []),
        tags=d.get("tags", []),
        endpoint=d.get("endpoint"),
        version=d.get("version", "1.0.0"),
        modalities=d.get("modalities", []),
        capability_schema=d.get("capability_schema", {}),
        ttl_seconds=d.get("ttl_seconds"),
        registered_at=_isoparse(d.get("registered_at")),
    )


class JsonAgentRepository(AgentRepository):
    """
    Stores live Agent objects in memory *and* persists their metadata
    to a JSON file.

    :param path: Path to the JSON catalog file. Created if absent.
    """

    def __init__(self, path: str = "agents_catalog.json") -> None:
        self._path = path
        self._lock = threading.RLock()
        self._agents: Dict[str, Agent] = {}
        self._catalog: Dict[str, AgentInfo] = {}
        self._load()

    # ── AgentRepository interface ─────────────────────────────────────────────

    def save_agent(self, agent: Agent) -> None:
        skill_names = [s.name for s in getattr(agent, "skills", [])]
        tags = getattr(agent, "tags", [])

        with self._lock:
            existing = self._catalog.get(agent.agent_name)
            if existing:
                # Preserve extended fields if already catalogued
                info = existing
                info.description = agent.description
                info.type = agent.agent_type
                info.skills = skill_names
                info.tags = tags
            else:
                info = AgentInfo(
                    name=agent.agent_name,
                    description=agent.description,
                    type=agent.agent_type,
                    skills=skill_names,
                    tags=tags,
                )
            self._agents[agent.agent_name] = agent
            self._catalog[agent.agent_name] = info
            # Attach info to agent for health-checker access
            agent._agent_info = info
        self._persist()

    def remove_agent(self, agent_name: str) -> None:
        with self._lock:
            self._agents.pop(agent_name, None)
            self._catalog.pop(agent_name, None)
        self._persist()

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        with self._lock:
            return self._agents.get(agent_name)

    def list_agents(self) -> List[AgentInfo]:
        with self._lock:
            return list(self._catalog.values())

    # ── Persistence ───────────────────────────────────────────────────────────

    def _persist(self) -> None:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self._path)), exist_ok=True)
            with self._lock:
                data = {name: _info_to_dict(info) for name, info in self._catalog.items()}
            with open(self._path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, default=str)
        except Exception:
            pass  # Persistence failures must not break the registry

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                data: dict = json.load(fh)
            for name, d in data.items():
                self._catalog[name] = _dict_to_info(d)
        except Exception:
            pass
