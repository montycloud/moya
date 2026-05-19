"""
Moya Trip Planner — Multi-Agent Demo
Powered by Ollama (llama3.1 / mistral / any tool-calling model)

Usage:
    python -m examples.trip_planner.app               # interactive mode
    python -m examples.trip_planner.app --demo        # guided demo (all 4 agents)
    python -m examples.trip_planner.app --model llama3.1:latest

Architecture
------------
1. User query → LLM Classifier → selects specialist agent
2. Entity extractor → parses destination, month, duration, style, interests
3. Relevant tools called directly (Python) → structured data retrieved
4. Enriched message (query + tool data) → specialist agent → final response

Pre-fetching tool data in the app layer (step 3) ensures reliable output
regardless of whether the local model supports tool-calling via the API.
"""

import argparse
import re
import sys
import time

from .agents import DEFAULT_BASE_URL, DEFAULT_MODEL, build_agents
from .skills import local_insider_tips
from .tools import (
    build_itinerary,
    estimate_budget,
    get_destination_info,
    get_packing_list,
    get_weather,
)

# ---------------------------------------------------------------------------
# ANSI colour helpers
# ---------------------------------------------------------------------------
_C = {
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "dim":     "\033[2m",
    "cyan":    "\033[96m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "magenta": "\033[95m",
    "blue":    "\033[94m",
    "red":     "\033[91m",
}

AGENT_STYLES = {
    "destination_agent": {"color": "cyan",    "icon": "🌍", "label": "DESTINATION"},
    "itinerary_agent":   {"color": "green",   "icon": "📅", "label": "ITINERARY  "},
    "budget_agent":      {"color": "yellow",  "icon": "💰", "label": "BUDGET     "},
    "packing_agent":     {"color": "magenta", "icon": "🧳", "label": "PACKING    "},
}

BANNER = (
    f"\n{_C['bold']}{_C['cyan']}"
    "╔══════════════════════════════════════════════════════════════╗\n"
    "║          MOYA TRIP PLANNER — Multi-Agent Demo              ║\n"
    "║               Powered by Ollama + Gemma 4                  ║\n"
    "╚══════════════════════════════════════════════════════════════╝"
    f"{_C['reset']}\n"
)

_DEMO_QUERIES_TEMPLATE = [
    ("destination_agent", "What should I know about visiting {dest}? I'm going in {month}."),
    ("itinerary_agent",   "Create a {days}-day itinerary for {dest} focused on food and local culture."),
    ("budget_agent",      "What is the mid-range daily budget for a {days}-day trip to {dest}?"),
    ("packing_agent",     "What should I pack for {days} days in {dest} in {month}?"),
]

_DEMO_DEFAULTS = {"dest": "Tokyo", "month": "April", "days": 5}


def _build_demo_queries(dest: str, month: str, days: int) -> list:
    return [
        (agent, q.format(dest=dest, month=month, days=days))
        for agent, q in _DEMO_QUERIES_TEMPLATE
    ]

# ---------------------------------------------------------------------------
# Entity extraction — parse travel parameters from natural language
# ---------------------------------------------------------------------------

_KNOWN_DESTINATIONS = [
    "tokyo", "paris", "bali", "new york", "rome", "barcelona", "sydney",
    "london", "amsterdam", "berlin", "dubai", "singapore", "bangkok",
    "lisbon", "prague", "vienna", "kyoto", "osaka", "seoul", "hong kong",
]

_MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]

_INTEREST_KEYWORDS = [
    "food", "culture", "history", "art", "nature", "adventure", "shopping",
    "nightlife", "architecture", "beaches", "hiking", "museums", "music",
    "temples", "wildlife", "photography", "luxury", "backpacking",
]

_STYLE_KEYWORDS = {"budget": "budget", "mid-range": "mid-range", "midrange": "mid-range",
                   "luxury": "luxury", "luxurious": "luxury", "cheap": "budget",
                   "affordable": "budget", "expensive": "luxury", "splurge": "luxury"}


def extract_entities(query: str) -> dict:
    """Parse destination, month, duration, travel style, and interests from a query."""
    q = query.lower()

    # Destination
    destination = None
    for dest in sorted(_KNOWN_DESTINATIONS, key=len, reverse=True):
        if dest in q:
            destination = dest.title()
            break

    # Month
    month = None
    for m in _MONTHS:
        if m in q:
            month = m.title()
            break

    # Duration — "5-day", "5 days", "five days", "a week"
    duration_days = 5  # default
    match = re.search(r"(\d+)[\s-]?day", q)
    if match:
        duration_days = int(match.group(1))
    elif "week" in q:
        duration_days = 7
    elif "weekend" in q:
        duration_days = 3

    # Travel style — check compound keywords before simple ones to avoid
    # "budget" matching the noun "budget" in "mid-range daily budget"
    travel_style = "mid-range"
    for kw in sorted(_STYLE_KEYWORDS, key=len, reverse=True):
        if kw in q:
            travel_style = _STYLE_KEYWORDS[kw]
            break

    # Interests
    interests = [kw for kw in _INTEREST_KEYWORDS if kw in q]
    interests_str = ", ".join(interests) if interests else "sightseeing, food, culture"

    return {
        "destination": destination or "Tokyo",  # fallback for demo
        "month": month or "July",
        "duration_days": duration_days,
        "travel_style": travel_style,
        "interests": interests_str,
    }


# ---------------------------------------------------------------------------
# Tool pre-fetch — call the right tools for each agent type
# ---------------------------------------------------------------------------

def _fetch_tool_data(agent_name: str, entities: dict) -> str:
    """
    Call the relevant tools for the given agent and return formatted context.
    This is the 'tool layer' that runs before the LLM response is generated.
    """
    dest  = entities["destination"]
    month = entities["month"]
    days  = entities["duration_days"]
    style = entities["travel_style"]
    interests = entities["interests"]
    sections = []

    if agent_name == "destination_agent":
        sections.append(get_destination_info(dest))
        sections.append(get_weather(dest, month))

    elif agent_name == "itinerary_agent":
        sections.append(build_itinerary(dest, days, interests))
        sections.append(local_insider_tips(dest))

    elif agent_name == "budget_agent":
        sections.append(estimate_budget(dest, days, style))

    elif agent_name == "packing_agent":
        sections.append(get_weather(dest, month))
        sections.append(get_packing_list(dest, days, month))

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _c(key: str) -> str:
    return _C.get(key, "")


def sep(char: str = "─", width: int = 64) -> None:
    print(f"{_c('dim')}{char * width}{_c('reset')}")


def print_tool_data(label: str, data: str) -> None:
    print(f"\n{_c('dim')}┌─ Tool Data ({label}) {'─' * (40 - len(label))}┐{_c('reset')}")
    for line in data.splitlines():
        print(f"{_c('dim')}│ {line}{_c('reset')}")
    print(f"{_c('dim')}└{'─' * 55}┘{_c('reset')}\n")


def agent_header(agent_name: str) -> None:
    style = AGENT_STYLES.get(agent_name, {"color": "blue", "icon": "🤖", "label": agent_name.upper()})
    color = _c(style["color"])
    icon  = style["icon"]
    label = style["label"]
    print(f"\n{color}{_c('bold')} {icon}  [{label}]  {agent_name}{_c('reset')}")
    sep()


def print_agents_overview(registry) -> None:
    print(f"\n{_c('bold')}Specialist Agents:{_c('reset')}")
    sep()
    for info in registry.list_agents():
        style = AGENT_STYLES.get(info.name, {"color": "blue", "icon": "🤖", "label": info.name.upper()})
        color = _c(style["color"])
        icon  = style["icon"]
        label = style["label"]
        skills_note = f"  ({', '.join(info.skills)})" if info.skills else ""
        print(f"  {color}{_c('bold')}{icon} [{label}]{_c('reset')}  {info.description}")
        if skills_note:
            print(f"  {_c('dim')}  Skills:{skills_note}{_c('reset')}")
    sep()


# ---------------------------------------------------------------------------
# Orchestration wrapper with tool pre-fetch
# ---------------------------------------------------------------------------

class TripOrchestrator:
    """
    Wraps MultiAgentOrchestrator to add a tool pre-fetch step.

    Flow:
      1. Classifier selects the specialist agent.
      2. Entity extractor parses the query.
      3. Relevant tools are called directly (Python, no LLM needed).
      4. Tool outputs are injected into the message as structured context.
      5. The specialist agent synthesises a response from the enriched message.
    """

    def __init__(self, registry, orchestrator):
        self.registry = registry
        self._orchestrator = orchestrator

    def process(self, query: str, thread_id: str, stream_callback=None, show_tool_data: bool = True):
        """
        Route query, pre-fetch tool data, and generate a response.

        :returns: (agent_name, response_text)
        """
        # Step 1: Classify
        available = self.registry.list_agents()
        agent_name = self._orchestrator.classifier.classify(
            message=query,
            thread_id=thread_id,
            available_agents=available,
        ) or "destination_agent"

        # Step 2: Extract entities
        entities = extract_entities(query)

        # Step 3: Fetch tool data
        tool_data = _fetch_tool_data(agent_name, entities)

        # Step 4: Build enriched message
        if tool_data:
            enriched = (
                f"{query}\n\n"
                f"[TRAVEL DATA — retrieved from our tools for {entities['destination']}]\n"
                f"{tool_data}"
            )
            if show_tool_data:
                print_tool_data(agent_name, tool_data)
        else:
            enriched = query

        # Step 5: Call specialist agent via orchestrator (agent_name override bypasses re-classification)
        response = self._orchestrator.orchestrate(
            thread_id=thread_id,
            user_message=enriched,
            stream_callback=stream_callback,
            agent_name=agent_name,
        )
        return agent_name, response


# ---------------------------------------------------------------------------
# Stream callback — parses the [agent_name] prefix from the orchestrator
# ---------------------------------------------------------------------------

class _StreamHandler:
    """Print stream chunks, handling the [agent_name] prefix emitted by the orchestrator."""

    def __init__(self):
        self._prefix_done = False
        self._buffer = ""
        self.selected_agent = None

    def __call__(self, chunk: str) -> None:
        if not self._prefix_done:
            self._buffer += chunk
            if "]" in self._buffer:
                end = self._buffer.index("]")
                self.selected_agent = self._buffer[1:end]
                remainder = self._buffer[end + 2:]  # skip "] "
                if remainder:
                    print(remainder, end="", flush=True)
                self._prefix_done = True
        else:
            print(chunk, end="", flush=True)


# ---------------------------------------------------------------------------
# Demo mode
# ---------------------------------------------------------------------------

def run_demo(trip_orchestrator: TripOrchestrator, registry, demo_queries: list) -> None:
    print(f"\n{_c('bold')}{_c('yellow')}DEMO MODE{_c('reset')} "
          f"— Four queries, one per specialist agent\n")
    print_agents_overview(registry)

    for i, (expected_agent, query) in enumerate(demo_queries, 1):
        print(f"\n{_c('bold')}Query {i} of {len(demo_queries)}:{_c('reset')}")
        print(f"{_c('dim')}You: {_c('reset')}{query}\n")

        handler = _StreamHandler()
        agent_header(expected_agent)

        trip_orchestrator.process(
            query=query,
            thread_id=f"demo_{expected_agent[:4]}",
            stream_callback=handler,
            show_tool_data=True,
        )
        print("\n")
        sep()

        if i < len(demo_queries):
            try:
                input(f"{_c('dim')}Press Enter for the next query…{_c('reset')} ")
            except (EOFError, KeyboardInterrupt):
                print()
                break

    print(f"\n{_c('green')}{_c('bold')}Demo complete! All four specialist agents demonstrated.{_c('reset')}\n")


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------

def run_interactive(trip_orchestrator: TripOrchestrator, registry) -> None:
    print(f"\n{_c('bold')}INTERACTIVE MODE{_c('reset')}")
    print_agents_overview(registry)
    print(
        "Ask anything about your trip — destination info, day plans, budget, or packing.\n"
        "The right specialist will handle your query automatically.\n"
        f"Type {_c('bold')}quit{_c('reset')} or {_c('bold')}exit{_c('reset')} to end.\n"
    )

    thread_id = f"trip_{int(time.time())}"

    while True:
        try:
            user_input = input(f"{_c('bold')}You:{_c('reset')} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{_c('dim')}Goodbye! Happy travels.{_c('reset')}\n")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q", "bye"):
            print(f"\n{_c('dim')}Goodbye! Happy travels.{_c('reset')}\n")
            break

        entities = extract_entities(user_input)
        print(
            f"\n{_c('dim')}Routing  → classifying your query…{_c('reset')}"
        )

        handler = _StreamHandler()

        agent_name, _ = trip_orchestrator.process(
            query=user_input,
            thread_id=thread_id,
            stream_callback=handler,
            show_tool_data=False,  # cleaner for interactive chat
        )
        agent_header(agent_name)
        print("\n")
        sep()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="trip_planner",
        description="Moya Trip Planner — Multi-Agent Demo using Ollama",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the guided demo (4 pre-built queries, one per specialist agent)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        metavar="MODEL",
        help=f"Ollama model tag (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        metavar="URL",
        help=f"Ollama server URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--destination",
        default=_DEMO_DEFAULTS["dest"],
        metavar="CITY",
        help="Destination city for demo mode (default: Tokyo). "
             f"Built-in data: {', '.join(t.title() for t in ['tokyo','paris','bali','new york','rome','barcelona','sydney'])}",
    )
    parser.add_argument(
        "--month",
        default=_DEMO_DEFAULTS["month"],
        metavar="MONTH",
        help=f"Travel month for demo mode (default: {_DEMO_DEFAULTS['month']})",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=_DEMO_DEFAULTS["days"],
        metavar="N",
        help=f"Number of trip days for demo mode (default: {_DEMO_DEFAULTS['days']})",
    )
    args = parser.parse_args()

    print(BANNER)
    print(f"{_c('dim')}Model : {args.model}")
    print(f"Server: {args.base_url}{_c('reset')}\n")

    print(f"{_c('dim')}Connecting to Ollama and initialising agents…{_c('reset')}")
    registry, orchestrator = build_agents(model=args.model, base_url=args.base_url)
    trip_orchestrator = TripOrchestrator(registry, orchestrator)
    print(f"{_c('green')}Ready!{_c('reset')}\n")

    demo_queries = _build_demo_queries(args.destination, args.month, args.days)

    if args.demo:
        run_demo(trip_orchestrator, registry, demo_queries)
        return

    print(f"{_c('bold')}Choose a mode:{_c('reset')}")
    print("  1  Demo mode   — guided walkthrough of all four specialist agents")
    print("  2  Interactive — free-form trip planning chat\n")

    try:
        choice = input("Enter 1 or 2 (default: 2): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)

    if choice == "1":
        run_demo(trip_orchestrator, registry, demo_queries)
    else:
        run_interactive(trip_orchestrator, registry)


if __name__ == "__main__":
    main()
