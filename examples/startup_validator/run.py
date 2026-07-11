"""
Startup Idea Validator — Moya Multi-Agent Demo

Showcases Phase 1 + Phase 2 framework capabilities:
  Phase 1: Skills (versioned, with tools), SkillRegistry, AgentRegistry,
           GlobalToolRegistry, EventBus observability
  Phase 2: SubAgentSpawner (templates + context inheritance),
           DelegationManager (parallel, async, depth guard),
           Aggregation strategies (vote + concat)

Usage:
    # Interactive
    python -m examples.startup_validator.run

    # With idea argument
    python -m examples.startup_validator.run --idea "An AI legal document review tool for SMBs"

    # Or run directly
    cd /path/to/moya-main
    python examples/startup_validator/run.py
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter

# ── Moya core ─────────────────────────────────────────────────────────────────
from moya.delegation import (
    DelegationManager,
    MaxDelegationDepthError,
    SubAgentSpawner,
    aggregate,
)
from moya.observability.event_bus import EventBus
from moya.registry.agent_registry import AgentRegistry, AgentRegistryConfig
from moya.skills import SkillRegistry
from moya.tools.tool_registry import ToolRegistry

# ── Demo modules ──────────────────────────────────────────────────────────────
from examples.startup_validator.agents import (
    build_coordinator,
    register_templates,
    spawn_specialists,
)
from examples.startup_validator.config import MAX_DELEGATION_DEPTH, USE_OPENAI, MODEL_NAME, AGENT_TYPE
from examples.startup_validator.report import print_report
from examples.startup_validator.skills import make_skills
from examples.startup_validator.tracer import print_section, setup_tracer


# ── Verdict extraction ────────────────────────────────────────────────────────

_VERDICT_RE = re.compile(r"VERDICT:\s*(GO|CAUTION|NO-GO)", re.IGNORECASE)

# Conservative tie-break order: NO-GO > CAUTION > GO
_VERDICT_PRIORITY = {"NO-GO": 0, "CAUTION": 1, "GO": 2}


def _extract_verdict(response: str) -> str:
    """Extract the last VERDICT: token from an agent response."""
    matches = _VERDICT_RE.findall(response)
    if matches:
        return matches[-1].upper()
    return "CAUTION"  # conservative fallback


def _conservative_vote(verdicts: list[str]) -> str:
    """Majority vote with conservative tie-breaking (NO-GO > CAUTION > GO)."""
    if not verdicts:
        return "CAUTION"
    counts = Counter(verdicts)
    max_count = max(counts.values())
    tied = [v for v, c in counts.items() if c == max_count]
    # Among tied, pick the most conservative
    return min(tied, key=lambda v: _VERDICT_PRIORITY.get(v, 1))


# ── Banner ────────────────────────────────────────────────────────────────────

def _print_banner(skill_registry: SkillRegistry) -> None:
    print("\n" + "=" * 72)
    print("  MOYA STARTUP IDEA VALIDATOR")
    backend = f"OpenAI ({MODEL_NAME})" if USE_OPENAI else f"Ollama ({MODEL_NAME})"
    print(f"  Backend: {backend}  |  Agent type: {AGENT_TYPE}  |  Max depth: {MAX_DELEGATION_DEPTH}")
    print("=" * 72)

    skills = skill_registry.list_skills()
    print(f"\nRegistered skills ({len(skills)}):")
    for s in skills:
        tools_str = f"{len(s.tools_factory() if s.tools_factory else [])} tool(s)" if s.tools_factory else "no tools"
        print(f"  • {s.name} v{s.version}  [{', '.join(s.tags)}]  — {tools_str}")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main(idea: str | None = None) -> None:

    # ── 1. Parse args ─────────────────────────────────────────────────────────
    if idea is None:
        parser = argparse.ArgumentParser(description="Moya Startup Idea Validator")
        parser.add_argument("--idea", type=str, default=None,
                            help="Startup idea to validate (quoted string)")
        args = parser.parse_args()
        idea = args.idea

    if not idea:
        print("Describe your startup idea (press Enter twice when done):")
        lines = []
        while True:
            line = input()
            if line == "" and lines:
                break
            lines.append(line)
        idea = " ".join(lines).strip()

    if not idea:
        print("No idea provided. Exiting.")
        sys.exit(1)

    # ── 2. Infrastructure setup ───────────────────────────────────────────────
    print_section("SETUP — Wiring framework components")

    bus = EventBus()
    setup_tracer(bus)

    # SkillRegistry — Phase 1 showcase
    skill_registry = SkillRegistry()
    skills = make_skills(bus)
    for skill in skills.values():
        skill_registry.register(skill)

    # ToolRegistry for the coordinator (inherited by sub-agents)
    tool_registry = ToolRegistry()

    # AgentRegistry with observability
    agent_registry = AgentRegistry(
        event_bus=bus,
        config=AgentRegistryConfig(enable_health_checks=False),
    )

    _print_banner(skill_registry)

    # ── 3. Build coordinator and spawner ──────────────────────────────────────
    coordinator = build_coordinator(tool_registry)
    agent_registry.register_agent(coordinator)

    spawner = SubAgentSpawner(agent_registry, event_bus=bus)
    register_templates(spawner)

    delegation_manager = DelegationManager(
        agent_registry,
        max_depth=MAX_DELEGATION_DEPTH,
        event_bus=bus,
    )

    # ── 4. Spawn specialist sub-agents ───────────────────────────────────────
    print_section("SPAWN — Dynamically creating specialist sub-agents")

    specialists = spawn_specialists(spawner, skill_registry, skills, coordinator)

    all_agent_names = list(agent_registry.list_agents())
    print(f"\nAgents now in registry ({len(all_agent_names)}):")
    for info in all_agent_names:
        skills_str = ", ".join(info.skills) if info.skills else "none"
        print(f"  • {info.name}  [{info.type}]  skills=[{skills_str}]")

    # ── 5. Depth guard demonstration ──────────────────────────────────────────
    print_section("DEPTH GUARD — Demonstrating MaxDelegationDepthError")

    delegation_manager._local.depth = MAX_DELEGATION_DEPTH  # simulate already at limit
    try:
        delegation_manager.delegate("test task", agent_name="market_analyst")
    except MaxDelegationDepthError as e:
        print(f"  ✓ MaxDelegationDepthError raised as expected:")
        print(f"    {e}")
    finally:
        delegation_manager._local.depth = 0  # reset before real work

    # ── 6. Async quick-take (fire-and-forget) ─────────────────────────────────
    print_section("ASYNC — Dispatching quick-take in background")

    qt_future = delegation_manager.delegate_async(
        task=f"Startup idea for quick gut-check: {idea}",
        agent_name="quick_take_agent",
        thread_id="qt-thread",
    )
    print("  Quick-take dispatched asynchronously — continuing with parallel analysis...")

    # ── 7. Parallel delegation ────────────────────────────────────────────────
    print_section("PARALLEL DELEGATION — 4 specialists analysing concurrently")

    agent_names = ["market_analyst", "tech_feasibility", "competitor_scout", "financial_estimator"]
    tasks = [
        (f"Analyse the market opportunity for this startup: {idea}", "market_analyst"),
        (f"Evaluate the technical feasibility of this startup: {idea}", "tech_feasibility"),
        (f"Scout the competitive landscape for this startup: {idea}", "competitor_scout"),
        (f"Estimate the financials for this startup: {idea}", "financial_estimator"),
    ]

    raw_results = delegation_manager.delegate_parallel(
        tasks=tasks,
        thread_id="validator-session",
    )

    # ── 8. Aggregation ────────────────────────────────────────────────────────
    print_section("AGGREGATION — Vote on verdict, Concat for investor brief")

    verdicts = [_extract_verdict(r) for r in raw_results]
    overall_verdict = _conservative_vote(verdicts)

    print(f"  Individual verdicts: {dict(zip(agent_names, verdicts))}")
    print(f"  Overall verdict (conservative vote): {overall_verdict}")

    full_brief = aggregate(raw_results, strategy="concat")

    # ── 9. Collect async result ───────────────────────────────────────────────
    print_section("COLLECTING — Quick-take async result")

    try:
        quick_take_text = qt_future.result(timeout=120)
        print("  Quick-take collected successfully.")
    except Exception as e:
        quick_take_text = f"[Quick-take unavailable: {e}]"
        print(f"  Quick-take failed: {e}")

    # ── 10. Final report ──────────────────────────────────────────────────────
    print_section("REPORT")

    print_report(
        idea=idea,
        raw_results=raw_results,
        agent_names=agent_names,
        verdicts=verdicts,
        overall_verdict=overall_verdict,
        full_brief=full_brief,
        quick_take=quick_take_text,
    )


if __name__ == "__main__":
    main()
