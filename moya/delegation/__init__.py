"""
moya.delegation — sub-agent task delegation.

Route tasks from a parent agent to specialised sub-agents, with depth
tracking to prevent infinite loops.

Quick start::

    from moya.delegation import DelegationManager

    manager = DelegationManager(agent_registry, max_depth=3)

    # Programmatic
    result = manager.delegate("Summarise the report", agent_name="summariser")

    # Parallel
    results = manager.delegate_parallel([
        ("Analyse risk",   "risk_agent"),
        ("Analyse market", "market_agent"),
    ])

    # LLM-driven (add tools so the agent can delegate itself)
    manager.setup_tools(parent_tool_registry)
"""

from moya.delegation.manager import (
    AgentNotFoundError,
    DelegationManager,
    MaxDelegationDepthError,
)
from moya.delegation.aggregation import aggregate, STRATEGIES
from moya.delegation.spawner import SubAgentSpawner, SubAgentSpec

__all__ = [
    "DelegationManager",
    "MaxDelegationDepthError",
    "AgentNotFoundError",
    "aggregate",
    "STRATEGIES",
    "SubAgentSpawner",
    "SubAgentSpec",
]
