"""
Reusable Skills for the Moya Trip Planner example.

Two skills are defined here:
  - local_tips_skill  : Adds a local_insider_tips tool + prompt guidance.
  - travel_safety_skill: Prompt-only skill that injects safety reminders.
"""

from moya.skills import Skill
from moya.tools.tool import Tool


# ---------------------------------------------------------------------------
# Tool backing the local_tips_skill
# ---------------------------------------------------------------------------

_INSIDER_TIPS = {
    "tokyo": [
        "Buy a Suica IC card at the airport — it works on all trains, buses, and at convenience stores.",
        "7-Eleven, Lawson, and FamilyMart convenience stores serve surprisingly good hot food cheaply.",
        "Many great ramen shops have no English menu — point at pictures or use Google Translate camera.",
        "Book teamLab Planets or Borderless weeks in advance; they sell out regularly.",
        "Vending machines sell hot and cold drinks everywhere — a ¥120 coffee beats any café queue.",
    ],
    "paris": [
        "Say 'Bonjour, Madame/Monsieur' before every interaction — it transforms the response you get.",
        "National museums are free on the first Sunday of each month (book online anyway to avoid queues).",
        "Walk 2 streets away from any major monument to find better food at half the price.",
        "The Palais-Royal gardens are a hidden oasis — calm, beautiful, and free.",
        "Pharmacies (marked with a green cross) stock excellent affordable skincare and cosmetics.",
    ],
    "bali": [
        "Use Grab (ride-hailing app) for all transport — it's far cheaper and more reliable than metered taxis.",
        "Warung (family-owned food stalls) serve the most authentic and cheapest food on the island.",
        "Visit temples early morning (7–9am) to beat crowds and avoid the midday heat.",
        "Negotiate at markets — start at 30–40% of the asking price; it's expected and part of the experience.",
        "A sarong is required at temples; many entrance gates loan them, or buy one for ~$2.",
    ],
    "new york": [
        "Stand to the right on escalators — the left lane is for walking, and New Yorkers take this seriously.",
        "The Staten Island Ferry is free and offers spectacular views of the Statue of Liberty and skyline.",
        "Happy hour (4–7pm) at most Manhattan bars means 50% off drinks — check Time Out NY for deals.",
        "The best bagels are found at neighbourhood delis, not tourist spots — ask a local.",
        "Download the MTA app for live subway updates and service alerts.",
    ],
    "rome": [
        "Carry a refillable water bottle — hundreds of free nasoni (drinking fountains) are dotted across the city.",
        "Pre-book the Vatican and Colosseum online — same-day queues can be 2+ hours.",
        "Eat lunch away from tourist sites — a €3–4 cornetto and espresso at a local bar beats any tourist café.",
        "The Borghese Gallery is Rome's best-kept art secret — book 2 weeks ahead, visits are timed entry.",
        "Avoid restaurants with photos on their menus near major attractions — walk one street further.",
    ],
    "barcelona": [
        "Book Sagrada Família and Park Güell online months in advance — walk-up entry is very limited.",
        "Dinner before 9pm marks you as a tourist; locals eat between 9–11pm.",
        "La Barceloneta beach gets very crowded in summer — take the metro to Ocata beach (30 min) instead.",
        "Bicing bike-share requires a local bank card; use rental shops for tourists instead.",
        "El Born neighbourhood has better tapas and fewer crowds than Las Ramblas.",
    ],
    "sydney": [
        "The Manly Ferry (30 min from Circular Quay) is the best budget harbour experience in the city.",
        "Check Broadsheet Sydney for current pop-ups, markets, and events.",
        "The coastal walk from Bondi to Coogee (6 km) is one of the world's great free walks.",
        "BYO (bring your own wine) restaurants let you save significantly on drinks — look for 'BYO licensed'.",
        "Buy an Opal card from any convenience store — cash on buses is not accepted.",
    ],
}


def local_insider_tips(destination: str) -> str:
    """Get insider tips and local secrets for a travel destination.

    Parameters:
    - destination: The destination city or country (e.g., 'Tokyo', 'Paris').
    """
    tips = _INSIDER_TIPS.get(destination.lower().strip(), [
        "Ask locals for restaurant recommendations over tourist guides.",
        "Learn a few words of the local language — it's always appreciated.",
        "Carry small bills for street food and local markets.",
        "Download offline maps (Maps.me or Google Maps offline) before arrival.",
        "Travel insurance is non-negotiable — always have it in place before you fly.",
    ])
    tip_lines = "\n".join(f"  • {t}" for t in tips)
    return f"Insider Tips for {destination.title()}:\n{tip_lines}"


# ---------------------------------------------------------------------------
# Skill definitions
# ---------------------------------------------------------------------------

local_tips_skill = Skill(
    name="local_insider_tips",
    description="Equips agents with local insider knowledge and hidden-gem tips for destinations.",
    version="1.0.0",
    tags=["local", "tips", "insider", "travel", "hidden-gems"],
    prompt_snippet=(
        "You have access to the 'local_insider_tips' tool.\n"
        "When discussing a destination, call this tool to surface practical, "
        "on-the-ground insights that most tourists miss. Weave these tips naturally "
        "into your response — they are a key differentiator of great travel advice."
    ),
    tools_factory=lambda: [Tool(name="local_insider_tips", function=local_insider_tips)],
)

travel_safety_skill = Skill(
    name="travel_safety",
    description="Prompts agents to include concise travel safety reminders in their advice.",
    version="1.0.0",
    tags=["safety", "health", "insurance", "emergency", "travel"],
    prompt_snippet=(
        "## Travel Safety Reminders\n"
        "Always include a brief safety note in your responses where relevant:\n"
        "  - Recommend comprehensive travel insurance before any international trip.\n"
        "  - Advise keeping digital copies of all important documents (passport, visa, insurance).\n"
        "  - Suggest checking current travel advisories from the traveller's home government.\n"
        "Keep safety notes brief — one or two sentences integrated naturally into the response."
    ),
)
