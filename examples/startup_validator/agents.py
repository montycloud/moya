"""
Coordinator agent factory and SubAgentSpec template registration.
"""

from __future__ import annotations

from moya.agents.agent import Agent
from moya.delegation.spawner import SubAgentSpawner, SubAgentSpec
from moya.registry.agent_registry import AgentRegistry
from moya.skills import SkillRegistry, attach_skills
from moya.tools.tool_registry import ToolRegistry

from examples.startup_validator.config import (
    AGENT_TYPE,
    MAX_DELEGATION_DEPTH,
    USE_OPENAI,
    agent_extra_kwargs,
)


_COORDINATOR_PROMPT = (
    "You are a startup validation coordinator. "
    "You orchestrate specialist analysis agents to evaluate startup ideas. "
    "You do not evaluate ideas yourself — you delegate to specialists and synthesize their verdicts."
)

_MARKET_ANALYST_PROMPT = (
    "You are a senior market analyst specialising in startup market opportunity. "
    "Evaluate the startup idea for market potential. "
    "Use the estimate_tam tool with appropriate industry and region values. "
    "Be specific: name the industry vertical, region assumption, target customer profile, "
    "and justify your verdict."
)

_TECH_FEASIBILITY_PROMPT = (
    "You are a senior software architect and CTO advisor. "
    "Evaluate the technical feasibility of the startup idea. "
    "Extract technology keywords from the idea and call score_tech_complexity. "
    "Report the complexity level, estimated build timeline, recommended technology stack, "
    "and the top 2 engineering risks."
)

_COMPETITOR_SCOUT_PROMPT = (
    "You are a competitive intelligence analyst specialising in startup landscapes. "
    "Identify the market category of this startup and call lookup_competitors. "
    "Provide a competitive landscape summary, identify the key differentiator opportunity, "
    "and assess whether a defensible moat is achievable."
)

_FINANCIAL_ESTIMATOR_PROMPT = (
    "You are a startup financial analyst and former venture capitalist. "
    "Estimate realistic financials for this startup. "
    "Assume a 3-person founding team and $0 initial monthly revenue unless stated otherwise. "
    "Call estimate_financials and provide a burn/runway/break-even analysis with "
    "commentary on unit economics and fundraising implications."
)

_QUICK_TAKE_PROMPT = (
    "You are a busy angel investor who has seen thousands of pitches. "
    "Give a direct, opinionated 3–4 sentence gut-check on this startup idea. "
    "Pick one specific risk and one specific opportunity. No hedging."
)


def build_coordinator(tool_registry: ToolRegistry) -> Agent:
    """Create the coordinator agent (not spawned — created directly)."""
    extra = agent_extra_kwargs()

    if USE_OPENAI:
        from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
        config = OpenAIAgentConfig(
            agent_name="coordinator",
            agent_type="openai",
            description="Startup validation coordinator — orchestrates specialist sub-agents.",
            system_prompt=_COORDINATOR_PROMPT,
            tool_registry=tool_registry,
            is_tool_caller=True,
            **extra,
        )
        return OpenAIAgent(config)
    else:
        from moya.agents.ollama_agent import OllamaAgent, OllamaAgentConfig
        config = OllamaAgentConfig(
            agent_name="coordinator",
            agent_type="ollama",
            description="Startup validation coordinator — orchestrates specialist sub-agents.",
            system_prompt=_COORDINATOR_PROMPT,
            tool_registry=tool_registry,
            is_tool_caller=True,
            **extra,
        )
        return OllamaAgent(config)


def register_templates(spawner: SubAgentSpawner) -> None:
    """Register all five SubAgentSpec templates on the spawner."""
    extra = agent_extra_kwargs()

    spawner.register_template("market_analyst_tmpl", SubAgentSpec(
        agent_type=AGENT_TYPE,
        agent_name="market_analyst",
        description="Evaluates startup market size, TAM, and target customer segments.",
        system_prompt=_MARKET_ANALYST_PROMPT,
        inherit_tools=True,
        inherit_skills=False,
        inherit_system_prompt_prefix=True,
        extra_kwargs=extra,
    ))

    spawner.register_template("tech_feasibility_tmpl", SubAgentSpec(
        agent_type=AGENT_TYPE,
        agent_name="tech_feasibility",
        description="Evaluates technical complexity, recommended stack, and build timeline.",
        system_prompt=_TECH_FEASIBILITY_PROMPT,
        inherit_tools=True,
        inherit_skills=False,
        inherit_system_prompt_prefix=True,
        extra_kwargs=extra,
    ))

    spawner.register_template("competitor_scout_tmpl", SubAgentSpec(
        agent_type=AGENT_TYPE,
        agent_name="competitor_scout",
        description="Identifies key competitors, market gaps, and potential moat.",
        system_prompt=_COMPETITOR_SCOUT_PROMPT,
        inherit_tools=True,
        inherit_skills=False,
        inherit_system_prompt_prefix=True,
        extra_kwargs=extra,
    ))

    spawner.register_template("financial_estimator_tmpl", SubAgentSpec(
        agent_type=AGENT_TYPE,
        agent_name="financial_estimator",
        description="Estimates burn rate, revenue potential, and runway.",
        system_prompt=_FINANCIAL_ESTIMATOR_PROMPT,
        inherit_tools=True,
        inherit_skills=False,
        inherit_system_prompt_prefix=True,
        extra_kwargs=extra,
    ))

    spawner.register_template("quick_take_tmpl", SubAgentSpec(
        agent_type=AGENT_TYPE,
        agent_name="quick_take_agent",
        description="Fast gut-check angel investor perspective.",
        system_prompt=_QUICK_TAKE_PROMPT,
        inherit_tools=False,
        inherit_skills=False,
        inherit_system_prompt_prefix=False,
        extra_kwargs=extra,
    ))


def spawn_specialists(
    spawner: SubAgentSpawner,
    skill_registry: SkillRegistry,
    skills: dict,
    coordinator: Agent,
) -> dict[str, Agent]:
    """Spawn all five specialist agents and attach their skills."""
    specialists = {}

    market_analyst = spawner.spawn_from_template("market_analyst_tmpl", parent_agent=coordinator)
    attach_skills(market_analyst, [skills["market_analysis"]], registry=skill_registry)
    specialists["market_analyst"] = market_analyst

    tech_feasibility = spawner.spawn_from_template("tech_feasibility_tmpl", parent_agent=coordinator)
    attach_skills(tech_feasibility, [skills["tech_feasibility"]], registry=skill_registry)
    specialists["tech_feasibility"] = tech_feasibility

    competitor_scout = spawner.spawn_from_template("competitor_scout_tmpl", parent_agent=coordinator)
    attach_skills(competitor_scout, [skills["competitor_scout"]], registry=skill_registry)
    specialists["competitor_scout"] = competitor_scout

    financial_estimator = spawner.spawn_from_template("financial_estimator_tmpl", parent_agent=coordinator)
    attach_skills(financial_estimator, [skills["financial_estimation"]], registry=skill_registry)
    specialists["financial_estimator"] = financial_estimator

    quick_take_agent = spawner.spawn_from_template("quick_take_tmpl", parent_agent=coordinator)
    attach_skills(quick_take_agent, [skills["quick_take"]], registry=skill_registry)
    specialists["quick_take_agent"] = quick_take_agent

    return specialists
