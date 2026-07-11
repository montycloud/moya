"""
Skill definitions for the Startup Idea Validator.

Call make_skills(bus) to get a dict of Skill objects with tool functions
wrapped to emit ToolCalledEvent into the EventBus.
"""

from __future__ import annotations

import time
from typing import Any

from moya.skills.skill import Skill
from moya.tools.tool import Tool


def _wrap_tool(fn, bus, tool_name: str):
    """Wrap a tool function to publish ToolCalledEvent on every call."""
    from moya.observability.events import ToolCalledEvent

    def wrapper(**kwargs):
        t0 = time.monotonic()
        try:
            result = fn(**kwargs)
            if bus:
                bus.publish(ToolCalledEvent(
                    source="tool_wrapper",
                    tool_name=tool_name,
                    arguments=kwargs,
                    duration_ms=(time.monotonic() - t0) * 1000,
                    success=True,
                ))
            return result
        except Exception as exc:
            if bus:
                bus.publish(ToolCalledEvent(
                    source="tool_wrapper",
                    tool_name=tool_name,
                    arguments=kwargs,
                    duration_ms=(time.monotonic() - t0) * 1000,
                    success=False,
                    error=str(exc),
                ))
            raise

    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper


def make_skills(bus=None) -> dict[str, Skill]:
    """
    Build all five Skill objects, with tool functions wrapped to emit
    ToolCalledEvent into *bus* (pass None to disable event emission).
    """
    from examples.startup_validator.tools import (
        estimate_tam,
        score_tech_complexity,
        lookup_competitors,
        estimate_financials,
    )

    w_tam       = _wrap_tool(estimate_tam,           bus, "estimate_tam")
    w_tech      = _wrap_tool(score_tech_complexity,  bus, "score_tech_complexity")
    w_comp      = _wrap_tool(lookup_competitors,     bus, "lookup_competitors")
    w_finance   = _wrap_tool(estimate_financials,    bus, "estimate_financials")

    market_analysis_skill = Skill(
        name="market_analysis",
        description="Evaluates startup market size, TAM, target customer segments.",
        version="1.0.0",
        tags=["market", "tam", "customer", "startup"],
        prompt_snippet=(
            "You are a startup market analyst. You have access to the 'estimate_tam' tool.\n"
            "Steps:\n"
            "1. Identify the industry vertical and target region from the startup idea.\n"
            "2. Call estimate_tam(industry, region) to get TAM data.\n"
            "3. Provide a market opportunity analysis covering: market size, growth rate, "
            "target customer segments, and addressable opportunity.\n"
            "End your response with EXACTLY one of these on its own line:\n"
            "VERDICT: GO\nVERDICT: CAUTION\nVERDICT: NO-GO"
        ),
        tools_factory=lambda: [Tool(name="estimate_tam", function=w_tam)],
    )

    tech_feasibility_skill = Skill(
        name="tech_feasibility",
        description="Evaluates technical complexity, recommended stack, and build timeline.",
        version="1.0.0",
        tags=["tech", "stack", "build-time", "startup"],
        prompt_snippet=(
            "You are a CTO-level technical evaluator. You have access to the 'score_tech_complexity' tool.\n"
            "Steps:\n"
            "1. Extract technology domain keywords from the startup idea "
            "(e.g. 'ai, real-time, mobile, payments, blockchain').\n"
            "2. Call score_tech_complexity(keywords) with a comma-separated keyword string.\n"
            "3. Provide a technical feasibility assessment covering: complexity level, "
            "estimated build time, recommended stack, key engineering risks.\n"
            "End your response with EXACTLY one of these on its own line:\n"
            "VERDICT: GO\nVERDICT: CAUTION\nVERDICT: NO-GO"
        ),
        tools_factory=lambda: [Tool(name="score_tech_complexity", function=w_tech)],
    )

    competitor_scout_skill = Skill(
        name="competitor_scout",
        description="Identifies key competitors, market gaps, and potential moat.",
        version="1.0.0",
        tags=["competition", "moat", "differentiation", "startup"],
        prompt_snippet=(
            "You are a competitive intelligence analyst. You have access to the 'lookup_competitors' tool.\n"
            "Steps:\n"
            "1. Identify the market category of this startup "
            "(e.g. saas, fintech, healthtech, edtech, legaltech, ai, logistics, cleantech).\n"
            "2. Call lookup_competitors(category) to retrieve known players.\n"
            "3. Provide a competitive landscape analysis covering: key competitors, "
            "differentiation opportunities, and potential defensible moat.\n"
            "End your response with EXACTLY one of these on its own line:\n"
            "VERDICT: GO\nVERDICT: CAUTION\nVERDICT: NO-GO"
        ),
        tools_factory=lambda: [Tool(name="lookup_competitors", function=w_comp)],
    )

    financial_estimation_skill = Skill(
        name="financial_estimation",
        description="Estimates burn rate, revenue potential, and runway.",
        version="1.0.0",
        tags=["finance", "burn-rate", "runway", "startup"],
        prompt_snippet=(
            "You are a startup financial modeller and former VC. "
            "You have access to the 'estimate_financials' tool.\n"
            "Steps:\n"
            "1. Estimate team size (default 3 if not stated) and monthly revenue (default 0 if pre-revenue).\n"
            "2. Call estimate_financials(team_size, monthly_revenue_usd) with integer values.\n"
            "3. Provide a financial analysis covering: burn rate, runway, break-even projection, "
            "and unit economics commentary.\n"
            "End your response with EXACTLY one of these on its own line:\n"
            "VERDICT: GO\nVERDICT: CAUTION\nVERDICT: NO-GO"
        ),
        tools_factory=lambda: [Tool(name="estimate_financials", function=w_finance)],
    )

    quick_take_skill = Skill(
        name="quick_take",
        description="Fast angel investor gut-check — no tool overhead.",
        version="1.0.0",
        tags=["summary", "quick", "startup"],
        prompt_snippet=(
            "You are a seasoned angel investor who has seen thousands of pitches. "
            "Give a gut-check reaction to this startup idea in 3–4 sentences. "
            "Identify the single biggest risk and the single most exciting opportunity. "
            "Be direct, specific, and opinionated. No hedging."
        ),
        # No tools_factory — pure LLM response keeps the async path fast
    )

    return {
        "market_analysis":      market_analysis_skill,
        "tech_feasibility":     tech_feasibility_skill,
        "competitor_scout":     competitor_scout_skill,
        "financial_estimation": financial_estimation_skill,
        "quick_take":           quick_take_skill,
    }
