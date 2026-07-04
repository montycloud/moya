"""
Custom Skills for the MOYA Trip Planner demo.

Demonstrates how reusable Skills can be attached to agents to add
specialised behaviours — prompt context and/or extra tools — without
modifying the agent class itself.

Skills defined here:
  travel_safety_skill  — prompt-only: agents remind travellers about safety
  eco_travel_skill     — prompt + tool: agents suggest eco-friendly options
"""

from moya.skills.skill import Skill
from moya.tools.tool import Tool


# ---------------------------------------------------------------------------
# Backing tool function for eco_travel_skill
# ---------------------------------------------------------------------------

_ECO_TIPS = {
    "tokyo": (
        "• Use IC card public transport instead of taxis — Tokyo's rail is world-class\n"
        "• Stay in eco-certified hotels (look for the Green Key or Earthcheck label)\n"
        "• Visit local konbini (convenience stores) with reusable bags\n"
        "• Opt for plant-based ramen and tofu dishes at local restaurants\n"
        "• Carry a reusable water bottle — tap water is safe to drink in Tokyo\n"
        "• Buy a day pass for the Tokyo Metro to reduce per-journey carbon footprint"
    ),
}


def eco_tips(city: str) -> str:
    """Return eco-friendly travel suggestions for a destination.

    Parameters:
    - city: The destination city.
    """
    city_lower = city.lower()
    tips = _ECO_TIPS.get(city_lower, (
        "• Prefer public transport or cycling over private taxis\n"
        "• Choose accommodation with sustainability certifications\n"
        "• Support local, small-scale restaurants over international chains\n"
        "• Carry a reusable bag, bottle, and cutlery set\n"
        "• Offset your flight emissions through a verified carbon-offset programme"
    ))
    return f"ECO-FRIENDLY TIPS — {city.title()}\n\n{tips}"


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

travel_safety_skill = Skill(
    name="travel_safety",
    version="1.0.0",
    description="Makes agents include safety tips, health advice, and travel advisories.",
    tags=["safety", "health", "travel"],
    prompt_snippet=(
        "## Travel Safety\n"
        "Always include a brief safety section in your responses when relevant:\n"
        "- Health precautions (vaccinations, medications, tap water safety)\n"
        "- Local scams or areas to avoid\n"
        "- Emergency contacts (local police, ambulance, nearest embassy)\n"
        "- Travel insurance recommendation\n"
    ),
    tools_factory=None,   # prompt-only skill
)

eco_travel_skill = Skill(
    name="eco_travel",
    version="1.0.0",
    description="Encourages sustainable travel and registers an eco-tips tool.",
    tags=["eco", "sustainability", "green", "travel"],
    prompt_snippet=(
        "## Eco-Friendly Travel\n"
        "Where appropriate, suggest lower-impact alternatives:\n"
        "- Public transport over private taxis\n"
        "- Local, independently owned accommodation and restaurants\n"
        "- Reusable items (bags, bottles, cutlery)\n"
        "Use the 'eco_tips' tool to retrieve city-specific sustainable travel suggestions.\n"
    ),
    tools_factory=lambda: [
        Tool(name="eco_tips", function=eco_tips)
    ],
)
