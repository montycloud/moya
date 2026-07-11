"""
Mock trip-data tools for the MOYA Trip Planner demo.

All functions are pure Python with no external API calls.
They return realistic-looking text for Tokyo (primary test city)
with a generic fallback for other destinations.

These functions serve double duty:
- Registered directly in a ToolRegistry for local agents.
- Served over MCP via mcp_server.py for MCPClient-based agents.
"""


# ---------------------------------------------------------------------------
# Data store (mock)
# ---------------------------------------------------------------------------

_DESTINATION_DATA = {
    "tokyo": {
        "october": """DESTINATION: Tokyo, Japan — October

HIGHLIGHTS
• World's most populous metropolitan area (14 million residents)
• October is peak season: mild weather, autumn foliage (koyo) late in the month
• Seamless blend of ultra-modern districts and ancient temples

MUST-SEE AREAS
• Asakusa — Senso-ji Temple, Japan's oldest, surrounded by traditional markets
• Shibuya — the iconic scramble crossing and vibrant youth culture
• Shinjuku — neon-lit entertainment hub, also home to Shinjuku Gyoen garden
• Harajuku — cutting-edge fashion and Meiji Shrine in the same neighbourhood
• Akihabara — electronics, anime, and pop culture epicentre

TOP EXPERIENCES
• teamLab Borderless — immersive digital art museum (book ahead)
• Tsukiji Outer Market — fresh sushi breakfast at 6 a.m.
• Sumo morning practice viewing (Ryogoku district)
• Tea ceremony in a traditional machiya townhouse
• Owl café / themed café culture unique to Tokyo

PRACTICAL TIPS
• IC card (Suica or Pasmo) covers all trains, subways, and many buses
• Cash still widely used — keep ¥10,000 on hand at all times
• Shoes off when entering homes, many ryokan, and some restaurants
• Escalator etiquette: stand left, pass right (except in Osaka)
• Google Translate camera mode handles menus instantly

OVERVIEW COMPLETE""",
    },
}

_COST_DATA = {
    "tokyo": {
        "cultural": {
            "flight_usd": "800–1,200 (from USA) / 600–900 (from Europe)",
            "hotel_per_night": 120,
            "food_per_day": 50,
            "transport_total": 80,
            "activities_total": 200,
        },
        "adventure": {
            "flight_usd": "800–1,200 (from USA)",
            "hotel_per_night": 80,
            "food_per_day": 40,
            "transport_total": 120,
            "activities_total": 300,
        },
        "relaxation": {
            "flight_usd": "800–1,200 (from USA)",
            "hotel_per_night": 180,
            "food_per_day": 60,
            "transport_total": 60,
            "activities_total": 150,
        },
    }
}

_WEATHER_DATA = {
    "tokyo": {
        "october": {
            "temp_range": "15–22 °C (59–72 °F)",
            "conditions": "Generally clear with occasional light rain showers",
            "humidity": "Moderate — comfortable for walking",
            "special": "Autumn foliage (koyo) begins in late October — parks and temples turn vivid red and gold",
            "packing": "Light layers, a cardigan or jacket for evenings, packable rain jacket, comfortable walking shoes",
        }
    }
}

_VISA_DATA = {
    ("japan", "us"): {
        "type": "Visa Waiver — no visa required",
        "max_stay": "Up to 90 days",
        "requirements": "Valid US passport, return ticket, proof of sufficient funds",
        "customs": "Declare items over ¥1,000,000 (~$6,500); no fresh produce",
        "note": "Rules subject to change — verify at mofa.go.jp before travel",
    },
    ("japan", "uk"): {
        "type": "Visa Waiver — no visa required",
        "max_stay": "Up to 90 days",
        "requirements": "Valid UK passport, return ticket",
        "customs": "Declare items over ¥1,000,000 in value",
        "note": "Verify current requirements at mofa.go.jp",
    },
}


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

def get_destination_facts(city: str, month: str) -> str:
    """Return key facts and highlights about a travel destination in a given month.

    Parameters:
    - city: The destination city name (e.g. Tokyo, Paris).
    - month: The travel month (e.g. October, July).
    """
    key = city.lower()
    m_key = month.lower()
    city_data = _DESTINATION_DATA.get(key, {})
    result = city_data.get(m_key)
    if result:
        return result

    # Generic fallback
    return (
        f"DESTINATION: {city.title()} — {month.title()}\n\n"
        f"A wonderful destination with rich culture, local cuisine, and unique experiences.\n"
        f"Visiting in {month.title()} offers pleasant weather for sightseeing.\n\n"
        f"Recommended: research local neighbourhoods, must-try restaurants,\n"
        f"and cultural sites specific to {city.title()} before you travel.\n\n"
        f"OVERVIEW COMPLETE"
    )


def estimate_trip_cost(city: str, days: int, style: str) -> str:
    """Return an itemised cost estimate for a trip.

    Parameters:
    - city: Destination city.
    - days: Number of travel days.
    - style: Trip style — cultural, adventure, or relaxation.
    """
    style = style.lower()
    key = city.lower()

    city_costs = _COST_DATA.get(key, {})
    costs = city_costs.get(style, city_costs.get("cultural", {
        "flight_usd": "500–1,500 (varies by origin)",
        "hotel_per_night": 100,
        "food_per_day": 40,
        "transport_total": 80,
        "activities_total": 150,
    }))

    hotel_total = costs["hotel_per_night"] * days
    food_total = costs["food_per_day"] * days
    land_total = hotel_total + food_total + costs["transport_total"] + costs["activities_total"]

    return (
        f"BUDGET BREAKDOWN — {city.title()} ({days} days, {style} style)\n\n"
        f"FLIGHTS (round-trip estimate)\n"
        f"  {costs['flight_usd']}\n\n"
        f"ACCOMMODATION\n"
        f"  ${costs['hotel_per_night']}/night × {days} nights = ${hotel_total:,}\n\n"
        f"FOOD & DINING\n"
        f"  ${costs['food_per_day']}/day × {days} days = ${food_total:,}\n\n"
        f"LOCAL TRANSPORT\n"
        f"  Estimated total: ${costs['transport_total']}\n\n"
        f"ACTIVITIES & ENTRY FEES\n"
        f"  Estimated total: ${costs['activities_total']}\n\n"
        f"LAND TOTAL (excl. flights): ${land_total:,}\n"
        f"ADD FLIGHTS for full trip cost."
    )


def get_weather_summary(city: str, month: str) -> str:
    """Return weather conditions and packing advice for a destination and month.

    Parameters:
    - city: Destination city.
    - month: Travel month.
    """
    key = city.lower()
    m_key = month.lower()

    city_weather = _WEATHER_DATA.get(key, {})
    w = city_weather.get(m_key)

    if w:
        return (
            f"WEATHER — {city.title()}, {month.title()}\n\n"
            f"Temperature:  {w['temp_range']}\n"
            f"Conditions:   {w['conditions']}\n"
            f"Humidity:     {w['humidity']}\n"
            f"Special note: {w['special']}\n\n"
            f"WHAT TO PACK\n  {w['packing']}"
        )

    return (
        f"WEATHER — {city.title()}, {month.title()}\n\n"
        f"Expect seasonal weather typical for {month.title()}.\n"
        f"Pack layers, comfortable walking shoes, and a light rain jacket.\n"
        f"Check a weather service closer to your travel date for specifics."
    )


def get_visa_requirements(destination: str, passport_country: str) -> str:
    """Return visa requirements for travelling to a destination with a given passport.

    Parameters:
    - destination: Country of destination (e.g. Japan, France).
    - passport_country: Passport-holder's country (e.g. US, UK, Australia).
    """
    key = (destination.lower(), passport_country.lower())
    info = _VISA_DATA.get(key)

    if info:
        return (
            f"VISA INFO — {destination.title()} for {passport_country.upper()} passport holders\n\n"
            f"Visa type:     {info['type']}\n"
            f"Maximum stay:  {info['max_stay']}\n"
            f"Requirements:  {info['requirements']}\n"
            f"Customs:       {info['customs']}\n\n"
            f"⚠  {info['note']}"
        )

    return (
        f"VISA INFO — {destination.title()} for {passport_country.upper()} passport holders\n\n"
        f"Visa requirements vary. Please check the official embassy website\n"
        f"for {destination.title()} or your government's travel advisory portal."
    )
