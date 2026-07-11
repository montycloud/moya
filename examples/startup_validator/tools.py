"""
Pure Python tool functions used by specialist agent skills.

All functions operate on static lookup tables so the demo runs fully
offline without any external API calls.
"""

from __future__ import annotations

# ── TAM lookup ────────────────────────────────────────────────────────────────

_TAM_DATA: dict = {
    ("saas", "global"):      {"tam": "$650B", "cagr": "12%", "segments": ["Enterprise IT", "SMB software", "Developer tools"]},
    ("saas", "us"):          {"tam": "$280B", "cagr": "11%", "segments": ["Enterprise SaaS", "Vertical SaaS", "SMB platforms"]},
    ("healthtech", "global"):{"tam": "$390B", "cagr": "18%", "segments": ["Remote patient monitoring", "EHR/EMR", "Mental health apps"]},
    ("healthtech", "us"):    {"tam": "$145B", "cagr": "16%", "segments": ["Telehealth", "Digital therapeutics", "Health data platforms"]},
    ("edtech", "global"):    {"tam": "$230B", "cagr": "14%", "segments": ["K-12 online learning", "Corporate L&D", "Higher education"]},
    ("edtech", "us"):        {"tam": "$90B",  "cagr": "13%", "segments": ["Tutoring platforms", "LMS", "Coding bootcamps"]},
    ("fintech", "global"):   {"tam": "$550B", "cagr": "20%", "segments": ["Digital payments", "Neobanking", "InsurTech"]},
    ("fintech", "us"):       {"tam": "$200B", "cagr": "17%", "segments": ["Payments infrastructure", "Lending platforms", "Wealth tech"]},
    ("retailtech", "global"):{"tam": "$180B", "cagr": "15%", "segments": ["E-commerce enablement", "Retail analytics", "Supply chain tech"]},
    ("logistics", "global"): {"tam": "$290B", "cagr": "11%", "segments": ["Last-mile delivery", "Freight management", "Warehouse automation"]},
    ("cleantech", "global"): {"tam": "$310B", "cagr": "22%", "segments": ["Solar/wind platforms", "Carbon markets", "EV infrastructure"]},
    ("agritech", "global"):  {"tam": "$22B",  "cagr": "12%", "segments": ["Precision farming", "AgriFinance", "Supply chain traceability"]},
    ("ai", "global"):        {"tam": "$500B", "cagr": "37%", "segments": ["Enterprise AI", "Generative AI tools", "AI infrastructure"]},
    ("legaltech", "global"): {"tam": "$25B",  "cagr": "10%", "segments": ["Contract management", "Legal research", "e-Discovery"]},
    ("hrtech", "global"):    {"tam": "$35B",  "cagr": "9%",  "segments": ["Talent acquisition", "Employee engagement", "Payroll automation"]},
}

_DEFAULT_TAM = {"tam": "~$50B", "cagr": "10%", "segments": ["Enterprise buyers", "SMB market", "Consumer segment"]}


def estimate_tam(industry: str, region: str) -> str:
    """Estimate Total Addressable Market for a given industry and region.

    Parameters:
    - industry: The industry vertical (e.g. saas, healthtech, fintech, edtech, ai, legaltech).
    - region: The target region (e.g. global, us, eu, apac).
    """
    key = (industry.lower().strip(), region.lower().strip())
    data = _TAM_DATA.get(key) or _TAM_DATA.get((key[0], "global")) or _DEFAULT_TAM
    segments = ", ".join(data["segments"])
    return (
        f"TAM ({industry.title()}, {region.upper()}): {data['tam']} "
        f"| CAGR: {data['cagr']} "
        f"| Top segments: {segments}"
    )


# ── Tech complexity scorer ────────────────────────────────────────────────────

_COMPLEXITY_WEIGHTS: dict[str, int] = {
    "blockchain": 4, "smart contract": 4, "zero-knowledge": 5,
    "real-time": 3, "streaming": 2, "websocket": 2,
    "ml": 3, "machine learning": 3, "deep learning": 4, "llm": 3, "ai": 2,
    "computer vision": 4, "nlp": 3, "recommendation": 3,
    "iot": 3, "hardware": 4, "embedded": 4, "robotics": 5,
    "native mobile": 3, "ios": 2, "android": 2, "react native": 1,
    "microservices": 2, "kubernetes": 2, "distributed": 3,
    "payment": 2, "compliance": 2, "hipaa": 2, "gdpr": 2,
    "marketplace": 2, "two-sided": 2, "multi-tenant": 2,
}

_STACK_RECOMMENDATIONS: dict[str, str] = {
    "Low":       "Python/FastAPI + React + PostgreSQL + Vercel",
    "Medium":    "Python/FastAPI + React + PostgreSQL + Redis + AWS",
    "High":      "Go/Python microservices + React + PostgreSQL + Redis + Kafka + Kubernetes",
    "Very High": "Polyglot microservices + Rust/Go hot paths + Kafka + ClickHouse + Kubernetes + MLOps pipeline",
}

_BUILD_TIME: dict[str, str] = {
    "Low":       "2–4 months (3-person team)",
    "Medium":    "4–8 months (3-person team)",
    "High":      "8–14 months (3-person team, likely needs specialised hires)",
    "Very High": "14–24 months (needs 5+ engineers including ML/infra specialists)",
}


def score_tech_complexity(keywords: str) -> str:
    """Score the technical complexity of a startup idea based on technology keywords.

    Parameters:
    - keywords: Comma-separated technology domain keywords extracted from the startup idea (e.g. 'ai, real-time, mobile, payments').
    """
    tokens = [k.strip().lower() for k in keywords.replace(";", ",").split(",")]
    score = sum(_COMPLEXITY_WEIGHTS.get(tok, 0) for tok in tokens)

    if score <= 3:
        level = "Low"
    elif score <= 7:
        level = "Medium"
    elif score <= 12:
        level = "High"
    else:
        level = "Very High"

    return (
        f"Complexity: {level} (score={score}) "
        f"| Build time: {_BUILD_TIME[level]} "
        f"| Recommended stack: {_STACK_RECOMMENDATIONS[level]}"
    )


# ── Competitor lookup ─────────────────────────────────────────────────────────

_COMPETITORS: dict[str, list[dict]] = {
    "saas": [
        {"name": "Salesforce", "stage": "Public ($200B+)", "gap": "Too complex for SMBs — vertical/niche SaaS still wide open"},
        {"name": "HubSpot",    "stage": "Public ($20B)",   "gap": "Mid-market focus — micro-business segment underserved"},
        {"name": "Monday.com", "stage": "Public ($8B)",    "gap": "Workflow-agnostic — domain-specific workflow tools have a moat"},
    ],
    "healthtech": [
        {"name": "Epic Systems",  "stage": "Private ($10B+)", "gap": "Monolithic hospital EHR — outpatient and specialist niches underserved"},
        {"name": "Teladoc",       "stage": "Public ($3B)",    "gap": "Reactive telehealth — proactive chronic-care management open"},
        {"name": "Hinge Health",  "stage": "IPO (2024)",      "gap": "MSK only — mental health + chronic disease combo underexplored"},
    ],
    "edtech": [
        {"name": "Coursera",   "stage": "Public ($1.5B)", "gap": "Broad catalogues — employer-credentialed micro-skills gap"},
        {"name": "Duolingo",   "stage": "Public ($5B)",   "gap": "Language only — gamified STEM for adults underexplored"},
        {"name": "Chegg",      "stage": "Public ($300M)", "gap": "Homework help declining — AI tutoring personalisation gap"},
    ],
    "fintech": [
        {"name": "Stripe",   "stage": "Private ($50B)",   "gap": "Developer-first — SMB non-technical payment orchestration open"},
        {"name": "Plaid",    "stage": "Private ($13B)",   "gap": "US-centric — emerging-market open banking infrastructure open"},
        {"name": "Brex",     "stage": "Private ($12B)",   "gap": "Tech startups only — creator economy + freelance fintech open"},
    ],
    "legaltech": [
        {"name": "Ironclad",   "stage": "Private ($3B)", "gap": "Enterprise CLM — SMB contract automation underserved"},
        {"name": "Harvey AI",  "stage": "Private ($1.5B)", "gap": "BigLaw focus — solo practitioners and boutique firms unserved"},
        {"name": "Clio",       "stage": "Private ($1.6B)", "gap": "Practice management — AI-native legal research integration gap"},
    ],
    "ai": [
        {"name": "OpenAI",      "stage": "Private ($80B+)", "gap": "Horizontal platform — vertical AI applications mostly unbuilt"},
        {"name": "Anthropic",   "stage": "Private ($18B)",  "gap": "API-first — regulated-industry safe AI deployments open"},
        {"name": "Scale AI",    "stage": "Private ($14B)",  "gap": "Data labelling — synthetic data for low-resource domains open"},
    ],
    "logistics": [
        {"name": "Flexport",  "stage": "Private ($8B)",  "gap": "Full-container — LTL and last-mile AI coordination open"},
        {"name": "project44", "stage": "Private ($2.7B)", "gap": "Large shippers — SMB freight visibility tools underserved"},
        {"name": "Convoy",    "stage": "Closed (2023)",   "gap": "Spot market only — contracted lane optimisation AI needed"},
    ],
    "cleantech": [
        {"name": "Arcadia",      "stage": "Private ($1.5B)", "gap": "Utility data only — building-level carbon accounting open"},
        {"name": "Watershed",    "stage": "Private ($1B)",   "gap": "Enterprise Scope 1/2 — Scope 3 supply chain tracking open"},
        {"name": "Raptor Maps",  "stage": "Private",         "gap": "Solar only — multi-asset renewable O&M platform open"},
    ],
}

_DEFAULT_COMPETITORS = [
    {"name": "Established incumbents", "stage": "Various",        "gap": "Legacy players slow to innovate — tech-native approach has moat"},
    {"name": "VC-backed startups",     "stage": "Series A–C",     "gap": "Horizontal players — deep vertical focus creates defensibility"},
    {"name": "Self-serve tools",       "stage": "Bootstrapped",   "gap": "Single-feature tools — integrated platform play open"},
]


def lookup_competitors(category: str) -> str:
    """Look up known competitors in a given market category.

    Parameters:
    - category: The market category to look up (e.g. saas, fintech, healthtech, edtech, legaltech, ai, logistics, cleantech).
    """
    comps = _COMPETITORS.get(category.lower().strip(), _DEFAULT_COMPETITORS)
    lines = [
        f"  • {c['name']} ({c['stage']}) — moat gap: {c['gap']}"
        for c in comps
    ]
    return f"Competitors in '{category}':\n" + "\n".join(lines)


# ── Financial estimator ───────────────────────────────────────────────────────

_FULLY_LOADED_COST_PER_PERSON_PER_MONTH = 12_000  # USD
_SEED_ROUND = 500_000  # USD
_MOM_GROWTH = 0.15     # 15% month-over-month revenue growth assumption


def estimate_financials(team_size: int, monthly_revenue_usd: int) -> str:
    """Estimate startup financials: burn rate, runway, and break-even timeline.

    Parameters:
    - team_size: Number of full-time team members (integer, e.g. 3).
    - monthly_revenue_usd: Current or estimated monthly revenue in USD (integer, e.g. 5000).
    """
    burn = team_size * _FULLY_LOADED_COST_PER_PERSON_PER_MONTH
    net_burn = max(0, burn - monthly_revenue_usd)
    runway_months = round(_SEED_ROUND / net_burn) if net_burn > 0 else 99

    # Project months until cumulative revenue ≥ burn (break-even)
    revenue = float(monthly_revenue_usd)
    months_to_be = None
    for m in range(1, 61):
        revenue *= (1 + _MOM_GROWTH)
        if revenue >= burn:
            months_to_be = m
            break

    be_str = f"{months_to_be} months" if months_to_be else ">5 years"

    return (
        f"Monthly burn: ${burn:,} | Net burn (after revenue): ${net_burn:,} "
        f"| Runway @ $500K seed: {runway_months} months "
        f"| Break-even (15% MoM growth): {be_str}"
    )
