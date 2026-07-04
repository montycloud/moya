"""
Pretty-printer for the Startup Idea Validator final report.
"""

from __future__ import annotations

import textwrap
from typing import List


# ── ANSI ──────────────────────────────────────────────────────────────────────
_R = "\033[0m"
_B = "\033[1m"
_D = "\033[2m"
_RED     = "\033[91m"
_GREEN   = "\033[92m"
_YELLOW  = "\033[93m"
_BLUE    = "\033[94m"
_CYAN    = "\033[96m"
_WHITE   = "\033[97m"


_VERDICT_COLOUR = {
    "GO":       _GREEN,
    "CAUTION":  _YELLOW,
    "NO-GO":    _RED,
}

_VERDICT_STAR = {
    "GO":      "★  GO  ★",
    "CAUTION": "⚠  CAUTION  ⚠",
    "NO-GO":   "✗  NO-GO  ✗",
}

_WIDTH = 72


def _hr(char: str = "─") -> str:
    return char * _WIDTH


def _verdict_str(v: str) -> str:
    c = _VERDICT_COLOUR.get(v, _WHITE)
    return f"{c}{_B}{v}{_R}"


def _wrap(text: str, indent: int = 2) -> str:
    prefix = " " * indent
    return "\n".join(
        textwrap.fill(line, width=_WIDTH - indent, initial_indent=prefix, subsequent_indent=prefix)
        if line.strip() else ""
        for line in text.splitlines()
    )


def print_report(
    idea: str,
    raw_results: List[str],
    agent_names: List[str],
    verdicts: List[str],
    overall_verdict: str,
    full_brief: str,
    quick_take: str,
) -> None:
    W = _WIDTH

    # ── Header ────────────────────────────────────────────────────────────────
    print()
    print(f"{_B}{_BLUE}╔{'═' * (W - 2)}╗{_R}")
    title = "MOYA STARTUP IDEA VALIDATOR — Multi-Agent Analysis"
    pad = (W - 2 - len(title)) // 2
    print(f"{_B}{_BLUE}║{' ' * pad}{title}{' ' * (W - 2 - pad - len(title))}║{_R}")
    print(f"{_B}{_BLUE}╚{'═' * (W - 2)}╝{_R}")

    # ── Startup idea ──────────────────────────────────────────────────────────
    print(f"\n{_B}STARTUP IDEA{_R}")
    print(_hr())
    print(_wrap(idea))

    # ── Quick take ────────────────────────────────────────────────────────────
    print(f"\n{_B}QUICK TAKE{_R}  {_D}(async gut-check — angel investor){_R}")
    print(_hr())
    print(_wrap(quick_take or "(not available)"))

    # ── Specialist results ────────────────────────────────────────────────────
    labels = {
        "market_analyst":     "MARKET ANALYST",
        "tech_feasibility":   "TECH FEASIBILITY",
        "competitor_scout":   "COMPETITOR SCOUT",
        "financial_estimator":"FINANCIAL ESTIMATOR",
    }

    print(f"\n{_B}SPECIALIST ANALYSIS{_R}")
    print(_hr())

    for agent_name, verdict, result in zip(agent_names, verdicts, raw_results):
        label = labels.get(agent_name, agent_name.upper())
        print(f"\n  {_B}{_CYAN}[{label}]{_R}   Verdict: {_verdict_str(verdict)}")
        print(f"  {'─' * (W - 4)}")
        for line in result.splitlines():
            print(f"  {line}")

    # ── Vote summary ──────────────────────────────────────────────────────────
    print(f"\n{_B}OVERALL VERDICT{_R}  {_D}(majority vote across 4 specialist judges){_R}")
    print(_hr("═"))

    vote_parts = "  |  ".join(
        f"{labels.get(n, n.upper()).split()[0]}→{_verdict_str(v)}"
        for n, v in zip(agent_names, verdicts)
    )
    print(f"  Votes:  {vote_parts}")

    go_count = verdicts.count("GO")
    caution_count = verdicts.count("CAUTION")
    nogo_count = verdicts.count("NO-GO")
    total = len(verdicts)
    winning_count = max(go_count, caution_count, nogo_count)

    vc = _VERDICT_COLOUR.get(overall_verdict, _WHITE)
    star = _VERDICT_STAR.get(overall_verdict, overall_verdict)
    print(f"\n  Result:  {vc}{_B}{star}{_R}   ({winning_count}/{total} agents agreed)")
    print(_hr("═"))

    # ── Investor brief ────────────────────────────────────────────────────────
    print(f"\n{_B}AGGREGATED INVESTOR BRIEF{_R}  {_D}(concat strategy — all 4 analyses){_R}")
    print(_hr())
    for line in full_brief.splitlines():
        print(f"  {line}")

    print()
