"""
Travel tools for the Moya Trip Planner example.

All tools return curated data — no external API calls required, making this
example fully runnable with a local Ollama instance.
"""

from moya.tools.tool import Tool

# ---------------------------------------------------------------------------
# Destination data
# ---------------------------------------------------------------------------

_DESTINATION_DATA = {
    "tokyo": {
        "country": "Japan",
        "highlights": [
            "Shibuya Crossing", "Senso-ji Temple", "teamLab Planets",
            "Tsukiji Outer Market", "Harajuku / Takeshita Street",
            "Shinjuku Gyoen National Garden", "Akihabara Electric Town",
        ],
        "culture": (
            "Deeply respectful and orderly society. Bow slightly when greeting. "
            "Remove shoes when entering homes and traditional restaurants. "
            "Avoid eating or drinking while walking — it's considered rude. "
            "Queues are strictly observed."
        ),
        "cuisine": ["ramen", "sushi", "tempura", "yakitori", "matcha desserts", "conveyor-belt sushi (kaiten-zushi)"],
        "transport": "Excellent metro and JR rail network — buy a Suica IC card at the airport. Taxis are available but expensive.",
        "language": "Japanese. English signage at major tourist attractions and train stations.",
        "visa": "Many nationalities visit Japan visa-free for up to 90 days. Check your country's requirements.",
    },
    "paris": {
        "country": "France",
        "highlights": [
            "Eiffel Tower", "Louvre Museum", "Montmartre & Sacré-Cœur",
            "Palace of Versailles", "Seine River cruise",
            "Musée d'Orsay", "Notre-Dame Cathedral",
        ],
        "culture": (
            "Always say 'Bonjour' before any request — Parisians appreciate politeness. "
            "Dining is unhurried; a meal can last 2+ hours. Dress stylishly, "
            "especially in restaurants. Tipping is appreciated but not mandatory."
        ),
        "cuisine": ["croissants", "baguettes", "coq au vin", "crêpes", "macarons", "French onion soup"],
        "transport": "Excellent metro and RER trains. Vélib' bike-share is great for short hops. Walking is best in the historic centre.",
        "language": "French. English widely understood in tourist areas.",
        "visa": "Schengen area — many nationalities enter visa-free for up to 90 days.",
    },
    "bali": {
        "country": "Indonesia",
        "highlights": [
            "Tegallalang Rice Terraces", "Tanah Lot Temple", "Seminyak Beach",
            "Ubud Monkey Forest", "Mount Batur sunrise hike",
            "Uluwatu Kecak Fire Dance", "Tirta Empul Holy Springs",
        ],
        "culture": (
            "Predominantly Hindu. Always wear a sarong when entering temples. "
            "Step around, never over, offerings (canang sari) on the ground. "
            "Dress modestly outside beach areas. The left hand is considered unclean."
        ),
        "cuisine": ["nasi goreng", "satay", "babi guling (suckling pig)", "lawar", "fresh tropical fruits", "jamu herbal drinks"],
        "transport": "Scooter rental is common and cheap. Grab app for taxis. Traffic in South Bali can be heavy — plan accordingly.",
        "language": "Balinese and Indonesian. English widely spoken in tourist areas.",
        "visa": "Visa on arrival for most nationalities. 30 days, extendable once.",
    },
    "new york": {
        "country": "USA",
        "highlights": [
            "Central Park", "Times Square", "Metropolitan Museum of Art",
            "Brooklyn Bridge", "The High Line", "Statue of Liberty",
            "Chelsea Market",
        ],
        "culture": (
            "Fast-paced and direct. Tipping 18–20% is expected at restaurants, "
            "bars, and cabs. New Yorkers are helpful if you ask. "
            "The city never truly sleeps — most neighbourhoods are safe and lively at night."
        ),
        "cuisine": ["NY-style pizza", "bagels with lox", "pastrami sandwiches", "dim sum (Chinatown)", "New York cheesecake"],
        "transport": "Subway runs 24/7 — buy an OMNY card. Yellow cabs and Uber/Lyft are plentiful. Walking is ideal in Manhattan.",
        "language": "English. Dozens of other languages spoken throughout the boroughs.",
        "visa": "ESTA for Visa Waiver Program countries. Tourist visa (B-2) required for others.",
    },
    "rome": {
        "country": "Italy",
        "highlights": [
            "Colosseum & Roman Forum", "Vatican City & St. Peter's Basilica",
            "Trevi Fountain", "Pantheon", "Borghese Gallery",
            "Trastevere neighbourhood", "Campo de' Fiori market",
        ],
        "culture": (
            "Lunch is the main meal of the day. Dress code at churches — cover "
            "shoulders and knees. Coffee culture is serious: stand at the bar for "
            "espresso, never order a cappuccino after 11am. Embrace la dolce vita."
        ),
        "cuisine": ["carbonara", "cacio e pepe", "supplì (rice balls)", "gelato", "tiramisu", "artichokes alla giudia"],
        "transport": "Metro has 2 main lines but coverage is limited. Buses and trams cover the rest. The historic centre is best explored on foot.",
        "language": "Italian. English spoken at most tourist sites.",
        "visa": "Schengen area — many nationalities enter visa-free.",
    },
    "barcelona": {
        "country": "Spain",
        "highlights": [
            "Sagrada Família", "Park Güell", "Las Ramblas",
            "Gothic Quarter (Barri Gòtic)", "Camp Nou stadium",
            "Barceloneta Beach", "La Boqueria market",
        ],
        "culture": (
            "Late dining culture — dinner rarely starts before 9pm. "
            "Siesta (2–5pm) means some shops close mid-afternoon. "
            "Catalan identity is distinct from Spanish — locals appreciate "
            "acknowledgement of the local culture and language."
        ),
        "cuisine": ["tapas", "paella", "pan con tomate", "crema catalana", "cava sparkling wine", "patatas bravas"],
        "transport": "Excellent metro system. Buses and trams fill the gaps. TMB card for all public transport. Cycling lanes are extensive.",
        "language": "Catalan and Spanish. English widely spoken in tourist areas.",
        "visa": "Schengen area.",
    },
    "sydney": {
        "country": "Australia",
        "highlights": [
            "Sydney Opera House", "Harbour Bridge climb", "Bondi Beach",
            "Blue Mountains day trip", "Darling Harbour", "Royal Botanic Garden",
            "Manly Beach ferry trip",
        ],
        "culture": (
            "Casual and outdoor-focused. Barbecue (BBQ) is a social institution. "
            "Very multicultural and generally relaxed. Slip, slop, slap — "
            "sun protection is taken seriously. 'No worries' is a way of life."
        ),
        "cuisine": ["meat pies", "Tim Tams", "flat white coffee", "fresh seafood", "multicultural fusion cuisine"],
        "transport": "Opal card for trains, buses, and ferries. Uber widely used. Ferries offer scenic routes across the harbour.",
        "language": "English.",
        "visa": "eVisitor (651) or ETA (601) for most nationalities — apply online before arrival.",
    },
}

_WEATHER_DATA = {
    ("tokyo", "january"):   "Cold and dry, 2–10°C. Clear blue skies are common. Occasional light snow possible. Pack a warm coat.",
    ("tokyo", "february"):  "Cold, 2–11°C. Ume (plum) blossoms begin. Crisp and dry with excellent visibility.",
    ("tokyo", "march"):     "Cool and pleasant, 5–15°C. Cherry blossoms start late March. Light layers ideal.",
    ("tokyo", "april"):     "Warm and beautiful, 10–20°C. Peak cherry blossom (sakura) season — expect crowds. Ideal conditions.",
    ("tokyo", "may"):       "Warm, 15–25°C. Golden Week (late April – early May) is very busy. Excellent weather.",
    ("tokyo", "june"):      "Rainy season begins, 17–27°C. Bring a compact umbrella. Humid but verdant.",
    ("tokyo", "july"):      "Hot and humid, 22–31°C. Typhoon season starts. Lively summer festivals (matsuri).",
    ("tokyo", "august"):    "Very hot and humid, 23–32°C. Typhoons possible. Obon summer festivals.",
    ("tokyo", "september"): "Warm and gradually improving, 19–28°C. Typhoon risk decreasing.",
    ("tokyo", "october"):   "Pleasant and comfortable, 13–22°C. Autumn foliage begins. One of the best times to visit.",
    ("tokyo", "november"):  "Cool, 8–18°C. Peak autumn foliage (koyo) — stunning colours. Highly recommended.",
    ("tokyo", "december"):  "Cold, 3–13°C. Winter illumination festivals. Clear, dry, and festive.",

    ("paris", "april"):    "Mild spring, 8–18°C. Gardens bloom. Occasional showers — bring a light jacket.",
    ("paris", "june"):     "Warm, 14–24°C. Long days. Fête de la Musique (June 21). Very pleasant.",
    ("paris", "july"):     "Warm to hot, 16–27°C. Bastille Day (July 14). Peak tourist season.",
    ("paris", "october"):  "Cool autumn, 7–17°C. Beautiful fall colours. Fewer crowds than summer.",
    ("paris", "december"): "Cold, 3–10°C. Magical Christmas markets and holiday decorations.",

    ("bali", "january"):   "Wet season, 23–30°C. Daily tropical showers, usually brief and refreshing. Lush green landscapes.",
    ("bali", "june"):      "Dry season begins, 22–30°C. Lower humidity and comfortable evenings. Good time to visit.",
    ("bali", "july"):      "Dry season, 22–31°C. Low humidity and breezy. Best overall conditions. Kite Festival.",
    ("bali", "august"):    "Dry season peak, 22–31°C. Excellent conditions. Busiest tourist month.",
    ("bali", "september"): "Dry season, 22–31°C. Crowds begin to ease. Still great weather.",

    ("new york", "april"):    "Mild spring, 7–19°C. Cherry blossoms in Central Park. Perfect sightseeing weather.",
    ("new york", "july"):     "Hot and humid, 20–30°C. Outdoor events and parks lively. Sunscreen essential.",
    ("new york", "october"):  "Crisp and beautiful, 10–22°C. Spectacular fall foliage. Ideal for sightseeing.",
    ("new york", "december"): "Cold, 0–8°C. Holiday atmosphere, Rockefeller Center tree, ice skating at Bryant Park.",

    ("rome", "april"):    "Warm spring, 10–20°C. Spring flowers. Quieter than summer. Near-perfect conditions.",
    ("rome", "june"):     "Hot, 18–28°C. Long days. Crowds at attractions — visit early morning or late evening.",
    ("rome", "october"):  "Mild and lovely, 12–22°C. Fewer crowds. Golden light. One of the best months.",

    ("barcelona", "may"):     "Warm, 14–24°C. Beach season starts. Lively outdoor life. Ideal conditions.",
    ("barcelona", "july"):    "Hot, 20–30°C. Peak beach season. Busy — book everything in advance.",
    ("barcelona", "october"): "Warm, 13–23°C. Fewer crowds, pleasant temperatures, sea still warm.",

    ("sydney", "january"): "Hot summer, 18–28°C. Beach weather. Occasional afternoon thunderstorms.",
    ("sydney", "april"):   "Mild and pleasant autumn, 13–23°C. Fewer crowds. Comfortable for sightseeing.",
    ("sydney", "july"):    "Cool winter, 8–17°C. Clear sunny days. Whale watching season on the coast.",
    ("sydney", "october"): "Warm spring, 13–22°C. Wildflowers in Blue Mountains. Great all-around conditions.",
}

_BUDGET_DATA = {
    "budget": {
        "tokyo":     {"accommodation": 45, "food": 22, "transport": 8,  "activities": 15},
        "paris":     {"accommodation": 55, "food": 28, "transport": 6,  "activities": 15},
        "bali":      {"accommodation": 20, "food": 8,  "transport": 4,  "activities": 10},
        "new york":  {"accommodation": 85, "food": 30, "transport": 10, "activities": 20},
        "rome":      {"accommodation": 45, "food": 22, "transport": 5,  "activities": 15},
        "barcelona": {"accommodation": 45, "food": 20, "transport": 5,  "activities": 12},
        "sydney":    {"accommodation": 70, "food": 28, "transport": 9,  "activities": 18},
    },
    "mid-range": {
        "tokyo":     {"accommodation": 130, "food": 55,  "transport": 15, "activities": 45},
        "paris":     {"accommodation": 160, "food": 65,  "transport": 12, "activities": 40},
        "bali":      {"accommodation": 65,  "food": 28,  "transport": 12, "activities": 28},
        "new york":  {"accommodation": 210, "food": 75,  "transport": 18, "activities": 55},
        "rome":      {"accommodation": 135, "food": 58,  "transport": 10, "activities": 38},
        "barcelona": {"accommodation": 125, "food": 52,  "transport": 10, "activities": 32},
        "sydney":    {"accommodation": 165, "food": 65,  "transport": 15, "activities": 42},
    },
    "luxury": {
        "tokyo":     {"accommodation": 360, "food": 160, "transport": 45, "activities": 110},
        "paris":     {"accommodation": 420, "food": 170, "transport": 35, "activities": 90},
        "bali":      {"accommodation": 260, "food": 90,  "transport": 45, "activities": 85},
        "new york":  {"accommodation": 520, "food": 190, "transport": 55, "activities": 130},
        "rome":      {"accommodation": 360, "food": 155, "transport": 32, "activities": 85},
        "barcelona": {"accommodation": 330, "food": 140, "transport": 32, "activities": 75},
        "sydney":    {"accommodation": 390, "food": 155, "transport": 42, "activities": 95},
    },
}

_PACKING_CLIMATE = {
    "hot":  ["lightweight breathable shirts (x5)", "shorts or light trousers", "summer dress/linen pants",
             "sandals or flip-flops", "sun hat", "UV-protection sunglasses", "light rain jacket"],
    "warm": ["mix of short and long-sleeve shirts (x5)", "light trousers/jeans", "comfortable walking shoes",
             "light jacket or cardigan", "compact umbrella"],
    "cool": ["layering tees + fleece or sweater", "jeans or warm trousers", "mid-weight jacket",
             "comfortable waterproof shoes", "umbrella"],
    "cold": ["heavy winter coat", "thermal base layers (top + bottom)", "warm sweaters (x3)",
             "waterproof insulated boots", "gloves", "woolly hat", "scarf"],
}

_PACKING_DESTINATION_EXTRAS = {
    "tokyo":     ["Suica IC card (buy at airport)", "cash — many local shops are cash-only",
                  "portable WiFi router or SIM card", "small towel for onsens"],
    "paris":     ["one smart outfit for upscale dining", "comfortable shoes (cobblestone streets are hard on feet)",
                  "Paris Museum Pass (saves time and money)", "small French phrasebook or offline translator"],
    "bali":      ["sarong (required at temples — or buy one there)", "modest clothing for temple visits",
                  "reef-safe sunscreen", "strong mosquito repellent (DEET)"],
    "new york":  ["comfortable sneakers (you'll walk 15k+ steps/day)", "layers for heavily air-conditioned interiors",
                  "OMNY card or MetroCard", "reusable water bottle"],
    "rome":      ["modest clothing for Vatican & churches (cover shoulders and knees)", "comfortable walking shoes",
                  "refillable water bottle (free drinking fountains everywhere)", "money belt"],
    "barcelona": ["beach bag and towel", "sunscreen SPF 50+", "TMB travel card",
                  "light evening layer (sea breeze can be cool)"],
    "sydney":    ["reef-safe sunscreen SPF 50+", "wide-brim hat", "beach gear (towel, rashie)",
                  "Opal card", "insect repellent for national park walks"],
}


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

def get_destination_info(destination: str) -> str:
    """Get general information about a travel destination.

    Returns highlights, culture & etiquette tips, local cuisine, transport
    options, language, and visa information.

    Parameters:
    - destination: The name of the destination city or country (e.g., 'Tokyo', 'Bali', 'New York').
    """
    data = _DESTINATION_DATA.get(destination.lower().strip())
    if not data:
        return (
            f"Destination info for '{destination}':\n"
            f"Our database doesn't have curated data for this destination yet. "
            f"Key things to research: local customs, must-see attractions, typical cuisine, "
            f"public transport, and visa requirements for your nationality."
        )

    highlights = ", ".join(data["highlights"][:5])
    cuisine = ", ".join(data["cuisine"][:5])
    return (
        f"=== {destination.title()} ({data['country']}) ===\n\n"
        f"Top Highlights:\n  {highlights}\n\n"
        f"Culture & Etiquette:\n  {data['culture']}\n\n"
        f"Local Cuisine:\n  {cuisine}\n\n"
        f"Getting Around:\n  {data['transport']}\n\n"
        f"Language:\n  {data['language']}\n\n"
        f"Visa Requirements:\n  {data['visa']}"
    )


def get_weather(destination: str, month: str) -> str:
    """Get typical weather conditions for a destination in a given month.

    Parameters:
    - destination: The destination city or country (e.g., 'Tokyo', 'Bali').
    - month: The month of travel (e.g., 'January', 'July').
    """
    key = (destination.lower().strip(), month.lower().strip())
    info = _WEATHER_DATA.get(key)
    if info:
        return f"Weather — {destination.title()} in {month.title()}: {info}"

    month_lower = month.lower()
    if month_lower in ("december", "january", "february"):
        season = "Northern Hemisphere winter / Southern Hemisphere summer"
    elif month_lower in ("march", "april", "may"):
        season = "Northern Hemisphere spring / Southern Hemisphere autumn"
    elif month_lower in ("june", "july", "august"):
        season = "Northern Hemisphere summer / Southern Hemisphere winter"
    else:
        season = "Northern Hemisphere autumn / Southern Hemisphere spring"

    return (
        f"Weather — {destination.title()} in {month.title()}: "
        f"Specific data not available. {month.title()} falls in {season}. "
        f"Check a weather service or the destination's tourism board for accurate forecasts."
    )


def estimate_budget(destination: str, duration_days: int, travel_style: str) -> str:
    """Estimate the daily and total travel budget for a trip.

    Returns an itemised daily breakdown and total cost (flights not included).

    Parameters:
    - destination: The destination city or country (e.g., 'Tokyo', 'Bali').
    - duration_days: Number of days for the trip (e.g., 5, 7, 10).
    - travel_style: Budget tier — one of 'budget', 'mid-range', or 'luxury'.
    """
    style = travel_style.lower().strip()
    if style not in _BUDGET_DATA:
        style = "mid-range"

    dest_key = destination.lower().strip()
    costs = _BUDGET_DATA[style].get(dest_key)

    if not costs:
        generic = {"budget": 65, "mid-range": 155, "luxury": 460}
        daily = generic.get(style, 155)
        return (
            f"Budget estimate — {destination.title()} ({duration_days} days, {style}):\n"
            f"  Daily estimate  : ~${daily} USD/day\n"
            f"  Total estimate  : ~${daily * duration_days} USD\n"
            f"  Note: Book accommodation early. Flights are extra."
        )

    daily = sum(costs.values())
    total = daily * duration_days
    return (
        f"=== {style.title()} Budget — {destination.title()} ({duration_days} days) ===\n\n"
        f"  Daily Breakdown:\n"
        f"    Accommodation : ${costs['accommodation']}/night\n"
        f"    Food & Drink  : ${costs['food']}/day\n"
        f"    Local Transport: ${costs['transport']}/day\n"
        f"    Activities    : ${costs['activities']}/day\n"
        f"    {'─' * 30}\n"
        f"    Daily Total   : ${daily}/day\n\n"
        f"  Trip Total      : ~${total} USD\n"
        f"  (International flights not included)\n\n"
        f"  Tip: Book accommodation and popular attractions in advance for best rates."
    )


def build_itinerary(destination: str, duration_days: int, interests: str) -> str:
    """Build a day-by-day travel itinerary outline for a destination.

    Parameters:
    - destination: The destination city or country (e.g., 'Tokyo', 'Rome').
    - duration_days: Number of days for the trip (e.g., 3, 5, 7).
    - interests: Comma-separated traveller interests to tailor the itinerary
                 (e.g., 'history, food, nature, art, shopping').
    """
    dest_key = destination.lower().strip()
    data = _DESTINATION_DATA.get(dest_key)
    highlights = data["highlights"] if data else ["local landmarks", "markets", "cultural sites"]
    transport_tip = data["transport"] if data else "Use local public transport."

    # Distribute highlights across middle days
    interest_list = [i.strip() for i in interests.split(",") if i.strip()]
    primary_interest = interest_list[0].title() if interest_list else "Exploration"

    days = []
    for day in range(1, duration_days + 1):
        if day == 1:
            days.append(
                f"  Day 1 — Arrival & First Impressions\n"
                f"    Morning  : Arrive, check in, and freshen up\n"
                f"    Afternoon: Orientation walk around your neighbourhood\n"
                f"    Evening  : Welcome dinner — try {highlights[0] if highlights else 'a local restaurant'} area"
            )
        elif day == duration_days and duration_days > 1:
            days.append(
                f"  Day {day} — Leisure & Departure\n"
                f"    Morning  : Revisit a favourite spot or last-minute shopping\n"
                f"    Afternoon: Pack and head to airport / transfer\n"
                f"    Tip      : Keep luggage light for the journey home"
            )
        else:
            h1 = highlights[(day - 1) % len(highlights)]
            h2 = highlights[day % len(highlights)]
            focus = interest_list[(day - 2) % len(interest_list)].title() if interest_list else "Sightseeing"
            days.append(
                f"  Day {day} — {focus} Focus\n"
                f"    Morning  : {h1}\n"
                f"    Afternoon: {h2}\n"
                f"    Evening  : Local dinner and neighbourhood stroll"
            )

    itinerary = "\n\n".join(days)
    return (
        f"=== {duration_days}-Day Itinerary: {destination.title()} ===\n"
        f"Tailored for: {interests}\n\n"
        f"{itinerary}\n\n"
        f"Getting Around: {transport_tip}\n"
        f"Tip: Pre-book popular attractions to skip queues and guarantee entry."
    )


def get_packing_list(destination: str, duration_days: int, month: str) -> str:
    """Get a recommended packing list tailored to destination, trip length, and weather.

    Parameters:
    - destination: The destination city or country (e.g., 'Tokyo', 'Bali').
    - duration_days: Number of days for the trip (e.g., 5, 10).
    - month: The month of travel (e.g., 'April', 'December').
    """
    dest_key = destination.lower().strip()
    month_lower = month.lower().strip()

    # Determine climate based on destination and month
    if month_lower in ("december", "january", "february"):
        climate = "hot" if dest_key in ("bali", "sydney") else "cold"
    elif month_lower in ("june", "july", "august"):
        climate = "cool" if dest_key == "sydney" else "hot"
    else:
        climate = "warm"

    seasonal = _PACKING_CLIMATE.get(climate, _PACKING_CLIMATE["warm"])
    extras = _PACKING_DESTINATION_EXTRAS.get(dest_key, [
        "local SIM card or portable WiFi", "small daypack for excursions", "padlock for hostel lockers",
    ])

    laundry_note = "plan on doing laundry mid-trip" if duration_days > 7 else "no laundry needed"
    days_of_clothes = min(duration_days, 7)

    lines = [
        f"=== Packing List: {destination.title()} in {month.title()} ({duration_days} days) ===\n",
        f"Clothing ({days_of_clothes} days' worth — {laundry_note}):",
    ]
    for item in seasonal:
        lines.append(f"  ✓ {item}")

    lines.append("\nDocuments & Admin:")
    for item in ["Passport (check expiry — 6 months beyond travel dates)", "Travel insurance policy",
                 "Booking confirmations (hotel, flights, tours)", "Emergency contacts list"]:
        lines.append(f"  ✓ {item}")

    lines.append("\nHealth & Safety:")
    for item in ["Any prescription medications (with doctor's letter)", "Basic first aid kit",
                 "Sunscreen SPF 50+", "Hand sanitiser", "Face masks"]:
        lines.append(f"  ✓ {item}")

    lines.append("\nTech & Money:")
    for item in ["Phone + charger", "Power bank (10,000 mAh+)", "Universal travel adapter",
                 "Earphones/headphones", "Local currency (small bills for arrival)",
                 "Credit & debit cards (notify your bank)", "Hidden money belt"]:
        lines.append(f"  ✓ {item}")

    lines.append(f"\nDestination Essentials ({destination.title()}):")
    for item in extras:
        lines.append(f"  ✓ {item}")

    lines.append("\nLeave at Home:")
    lines.append("  ✗ Valuables you can't afford to lose")
    lines.append("  ✗ Full-size toiletries (buy locally to save space)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool factory
# ---------------------------------------------------------------------------

def get_tools() -> list:
    """Return all trip-planner Tool objects."""
    return [
        Tool(name="get_destination_info", function=get_destination_info),
        Tool(name="get_weather",          function=get_weather),
        Tool(name="estimate_budget",      function=estimate_budget),
        Tool(name="build_itinerary",      function=build_itinerary),
        Tool(name="get_packing_list",     function=get_packing_list),
    ]
