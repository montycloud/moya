# Trip Planner — Use Case Requirements

**Purpose:** Validate every MOYA capability shipped in Phase 1 and Phase 2 through a single, coherent end-to-end scenario.  
**Folder:** `trip_planner/`  
**Status:** Ready for implementation

---

## 1. Scenario Overview

A user describes a trip they want to take. The system produces a complete travel plan that includes destination highlights, a day-by-day itinerary, a budget breakdown, and a packing list.

### Sample Input

```
I want to plan a 7-day trip to Tokyo, Japan in October.
My total budget is $4,000 USD. I prefer cultural experiences.
```

### Expected Output (assembled by the end of the pipeline)

```
DESTINATION OVERVIEW
  Key facts, highlights, and cultural tips about Tokyo in October.

DAY-BY-DAY ITINERARY
  Day 1 – Day 7 schedule with morning / afternoon / evening activities.

BUDGET BREAKDOWN
  Estimated flight, accommodation, food, transport, and activity costs.

PACKING LIST
  Weather-appropriate clothing and must-bring items for a cultural trip.

TRAVEL TIPS
  Visa requirements, safety notes, and eco-friendly travel suggestions.
```

---

## 2. Capability Coverage Map

Every MOYA capability must be exercised by at least one module in the demo.

| Capability | Module | How It Is Used |
|---|---|---|
| **Pipeline (sequential)** | `pipeline.py` | Overall plan is produced by a 4-step sequential pipeline |
| **Pipeline (parallel)** | `pipeline.py` | Itinerary and budget are generated concurrently via `ParallelStep` |
| **Pipeline (branch)** | `pipeline.py` | Packing list generation branches on trip style (cultural / adventure / relaxation) |
| **Pipeline (loop)** | `pipeline.py` | A refinement loop polishes the destination overview until quality passes |
| **Skills** | `skills.py` | Two custom skills (`travel_safety`, `eco_travel`) are attached to agents |
| **SkillRegistry** | `agents.py` | Skills are registered in a `SkillRegistry` and looked up by name |
| **Skill-based discovery** | `agents.py` | `find_agents_with_skill()` used to locate the safety-aware agent |
| **Agent tags** | `agents.py` | Agents tagged `specialist` vs `coordinator`; `find_agents_by_tag()` used |
| **MCP Server** | `mcp_server.py` | Four mock trip-data tools served over stdio MCP |
| **MCP Client** | `agents.py` | `MCPClient` connects to the server; tools appear in the shared `ToolRegistry` |
| **DelegationManager (programmatic)** | `pipeline.py` | Pipeline delegates the travel-tips step directly to `safety_advisor` agent |
| **DelegationManager (parallel)** | `pipeline.py` | Sends destination + budget tasks to two agents concurrently |
| **DelegationManager (LLM-driven)** | `main.py` | Coordinator agent uses `list_agents` + `delegate_task` tools |
| **MultiAgent Orchestrator** | `main.py` | Interactive mode routes follow-up questions to the right specialist |
| **Enhanced AgentRegistry** | `agents.py` | Agents registered with skills, tags; queried by skill and by tag |

---

## 3. Module Descriptions

### 3.1 `tools.py` — Mock Trip-Data Functions

Pure Python functions with no external API calls. Used both as local MOYA tools and as the backing implementation for the MCP server.

| Tool | Signature | Returns |
|---|---|---|
| `get_destination_facts` | `(city: str, month: str) -> str` | Key facts, highlights, best areas to visit |
| `estimate_trip_cost` | `(city: str, days: int, style: str) -> str` | Itemised cost estimate (flight, hotel, food, transport, activities) |
| `get_weather_summary` | `(city: str, month: str) -> str` | Average temperature, precipitation, what to wear |
| `get_visa_requirements` | `(destination: str, passport_country: str) -> str` | Visa type, processing time, fees |

All functions return structured plain-text strings (no JSON, no external calls).

### 3.2 `skills.py` — Custom Travel Skills

Two `Skill` objects defined using `moya.skills.Skill`.

**`travel_safety_skill`**
- Appends a prompt snippet reminding agents to include safety and health tips.
- No tools (prompt-only skill).
- Tags: `["safety", "travel"]`

**`eco_travel_skill`**
- Appends a prompt snippet encouraging sustainable travel recommendations.
- Registers one tool: `eco_tips(city: str) -> str` (a mock function that returns low-impact travel suggestions for a given city).
- Tags: `["eco", "sustainability", "travel"]`

### 3.3 `mcp_server.py` — MCP Tool Server

A standalone script. When run directly, it starts an `MCPServer` on stdio that serves the four tools from `tools.py`. Used by `agents.py` via `MCPClient.from_subprocess()`.

### 3.4 `agents.py` — Agent Definitions & Registry Setup

Builds all agents and returns a configured `AgentRegistry`. Responsible for:

1. Launching the MCP server subprocess and connecting via `MCPClient`.
2. Registering MCP tools in a shared `ToolRegistry`.
3. Defining a `SkillRegistry` and registering `travel_safety_skill` and `eco_travel_skill`.
4. Creating five agents:

| Agent | Skills | Tags | Tool-caller? | Role |
|---|---|---|---|---|
| `destination_expert` | `travel_safety`, `eco_travel` | `specialist` | Yes (MCP tools) | Researches destination facts and highlights |
| `itinerary_builder` | `travel_safety` | `specialist` | No | Builds day-by-day schedules |
| `budget_advisor` | — | `specialist` | Yes (MCP tools) | Estimates and breaks down trip costs |
| `packing_advisor` | — | `specialist` | No | Recommends what to pack |
| `coordinator` | — | `coordinator` | Yes (delegation tools) | Orchestrates via LLM-driven delegation |

5. Registering all agents in the `AgentRegistry` with skills and tags.
6. Setting up a `DelegationManager` and calling `setup_tools()` on the coordinator's tool registry.

### 3.5 `pipeline.py` — Trip Planning Pipeline

Builds and runs the main pipeline using `moya.flows`. The pipeline is structured as follows:

```
Step 1  DestinationStep (LoopStep wrapper)
           └── AgentStep(destination_expert)
               Runs up to 3 times until output contains "OVERVIEW COMPLETE"

Step 2  ParallelStep
           ├── AgentStep(itinerary_builder)   → produces itinerary text
           └── AgentStep(budget_advisor)      → produces budget text

Step 3  BranchStep  (condition: trip_style from ctx.metadata)
           ├── "cultural"    → AgentStep(packing_advisor) with cultural prompt
           ├── "adventure"   → AgentStep(packing_advisor) with adventure prompt
           └── "relaxation"  → AgentStep(packing_advisor) with relaxation prompt

Step 4  SynthesisStep (FunctionStep)
           Calls DelegationManager.delegate() to ask coordinator to
           synthesise the itinerary, budget, and packing list into a
           single formatted travel plan.
```

Entry point: `run_pipeline(trip_request: dict) -> str`

```python
trip_request = {
    "city": "Tokyo",
    "country": "Japan",
    "days": 7,
    "month": "October",
    "budget_usd": 4000,
    "style": "cultural",   # cultural | adventure | relaxation
    "passport": "US",
}
```

### 3.6 `main.py` — Entry Point & Demo Runner

Runs three distinct demos in sequence:

**Demo 1 — Pipeline demo**  
Calls `run_pipeline()` with the Tokyo cultural trip and prints the full travel plan.

**Demo 2 — LLM-driven delegation demo**  
Creates a fresh `coordinator` agent with delegation tools. Sends three follow-up questions directly to the coordinator and lets it decide which specialist to delegate each one to:
- *"What should I be careful about regarding safety in Tokyo?"*
- *"Can you suggest eco-friendly accommodation options?"*
- *"Give me a revised budget if I want to add a day trip to Kyoto."*

**Demo 3 — Skill and registry discovery demo**  
Without running any LLM calls, demonstrates the registry query capabilities:
- Lists all agents with the `travel_safety` skill.
- Lists all agents tagged `specialist`.
- Lists all eco-related skills from the `SkillRegistry`.
- Prints the full tool catalog (MCP tools + local tools) from the shared `ToolRegistry`.

---

## 4. Constraints

- **No real external API calls for trip data.** All destination, cost, weather, and visa data is hardcoded mock data in `tools.py`. Only OpenAI LLM calls are real.
- **Single `OPENAI_API_KEY` environment variable** is the only required secret.
- **Self-contained.** The folder must run with `python3 trip_planner/main.py` from the repo root without any additional setup beyond `pip install openai mcp`.
- **No output file writes.** Everything prints to stdout.
- **Each demo clearly labelled** with a header so it is obvious which capability is being exercised.

---

## 5. Acceptance Criteria

| # | Criterion |
|---|---|
| AC-1 | `python3 trip_planner/main.py` runs without unhandled exceptions |
| AC-2 | Demo 1 prints a travel plan with at least 4 labelled sections (Overview, Itinerary, Budget, Packing) |
| AC-3 | Demo 1 console output shows evidence of parallel execution (both itinerary and budget agents ran) |
| AC-4 | Demo 2 shows the coordinator delegating to at least two different specialist agents |
| AC-5 | Demo 3 prints the correct skill/tag/tool discovery results without LLM calls |
| AC-6 | The MCP server subprocess is started and shut down cleanly (no zombie processes) |
| AC-7 | No existing MOYA example or test breaks (regression check passes) |
