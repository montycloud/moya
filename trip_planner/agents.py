"""
Agent definitions and registry setup for the MOYA Trip Planner demo.

This module:
  1. Launches the MCP server subprocess and connects via MCPClient.
  2. Registers MCP tools in a shared ToolRegistry.
  3. Defines a SkillRegistry with travel_safety and eco_travel skills.
  4. Creates five agents: destination_expert, itinerary_builder,
     budget_advisor, packing_advisor, coordinator.
  5. Registers all agents in an AgentRegistry with skills and tags.
  6. Sets up a DelegationManager with list_agents / delegate_task tools
     registered on the coordinator's tool registry.

Public API::

    registry, skill_registry, tool_registry, delegation_manager, mcp_client
        = build_registry()

Call ``mcp_client.close()`` when you are done to shut down the subprocess.
"""

import os
import sys

from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.delegation.manager import DelegationManager
from moya.mcp.client import MCPClient
from moya.registry.agent_registry import AgentRegistry
from moya.skills.registry import SkillRegistry
from moya.tools.tool_registry import ToolRegistry

from trip_planner.skills import eco_travel_skill, travel_safety_skill


def build_registry():
    """
    Construct and wire up all agents, registries, and the MCP connection.

    Returns:
        (AgentRegistry, SkillRegistry, ToolRegistry, DelegationManager, MCPClient)
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")

    # ------------------------------------------------------------------
    # 1. Shared ToolRegistry — populated first by MCP tools
    # ------------------------------------------------------------------
    tool_registry = ToolRegistry()

    # ------------------------------------------------------------------
    # 2. MCP client — launches mcp_server.py as a subprocess
    # ------------------------------------------------------------------
    mcp_server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")
    mcp_client = MCPClient.from_subprocess(
        command=sys.executable,
        args=[mcp_server_path],
        name="trip_tools",
    )
    for tool in mcp_client.get_tools():
        tool_registry.register_tool(tool)

    # ------------------------------------------------------------------
    # 3. SkillRegistry
    # ------------------------------------------------------------------
    skill_registry = SkillRegistry()
    skill_registry.register(travel_safety_skill)
    skill_registry.register(eco_travel_skill)

    # ------------------------------------------------------------------
    # 4. Agent definitions
    # ------------------------------------------------------------------

    def _make_tool_registry(include_mcp: bool = True) -> ToolRegistry:
        """Return a ToolRegistry pre-populated with MCP tools if requested."""
        if not include_mcp:
            return ToolRegistry()
        # Share the same global tool_registry so all MCP tools are visible
        return tool_registry

    # --- destination_expert -------------------------------------------
    destination_expert = OpenAIAgent(
        OpenAIAgentConfig(
            agent_name="destination_expert",
            agent_type="openai",
            description=(
                "Researches destination facts, highlights, and cultural tips. "
                "Uses MCP tools to fetch real destination data, weather, and visa info."
            ),
            system_prompt=(
                "You are an expert travel researcher. When given a destination and "
                "travel month, use your available tools to gather comprehensive facts "
                "about that destination. Include highlights, must-see areas, practical "
                "tips, and an overview that ends with the exact phrase 'OVERVIEW COMPLETE'."
            ),
            api_key=api_key,
            tool_registry=_make_tool_registry(include_mcp=True),
            is_tool_caller=True,
            skills=[travel_safety_skill, eco_travel_skill],
        )
    )
    destination_expert.tags = ["specialist"]

    # --- itinerary_builder --------------------------------------------
    itinerary_agent_registry = ToolRegistry()
    itinerary_builder = OpenAIAgent(
        OpenAIAgentConfig(
            agent_name="itinerary_builder",
            agent_type="openai",
            description=(
                "Builds detailed day-by-day travel itineraries with morning, "
                "afternoon, and evening activities."
            ),
            system_prompt=(
                "You are an expert travel planner specialising in itinerary design. "
                "Create detailed day-by-day schedules for trips. Structure each day "
                "with Morning, Afternoon, and Evening sections. Incorporate local "
                "culture, cuisine, and unique experiences."
            ),
            api_key=api_key,
            tool_registry=itinerary_agent_registry,
            is_tool_caller=False,
            skills=[travel_safety_skill],
        )
    )
    itinerary_builder.tags = ["specialist"]

    # --- budget_advisor -----------------------------------------------
    budget_advisor = OpenAIAgent(
        OpenAIAgentConfig(
            agent_name="budget_advisor",
            agent_type="openai",
            description=(
                "Estimates trip costs and produces itemised budget breakdowns "
                "covering flights, accommodation, food, transport, and activities."
            ),
            system_prompt=(
                "You are a travel finance expert. Use the estimate_trip_cost tool "
                "to provide accurate budget breakdowns. Present costs clearly with "
                "totals and money-saving tips."
            ),
            api_key=api_key,
            tool_registry=_make_tool_registry(include_mcp=True),
            is_tool_caller=True,
        )
    )
    budget_advisor.tags = ["specialist"]

    # --- packing_advisor ----------------------------------------------
    packing_advisor = OpenAIAgent(
        OpenAIAgentConfig(
            agent_name="packing_advisor",
            agent_type="openai",
            description=(
                "Recommends what to pack based on destination, season, and trip style "
                "(cultural / adventure / relaxation)."
            ),
            system_prompt=(
                "You are a travel packing expert. Create concise, practical packing "
                "lists tailored to the destination's climate, planned activities, and "
                "trip style. Organise items into clear categories (clothing, toiletries, "
                "documents, tech, etc.)."
            ),
            api_key=api_key,
            tool_registry=ToolRegistry(),
            is_tool_caller=False,
        )
    )
    packing_advisor.tags = ["specialist"]

    # --- coordinator --------------------------------------------------
    coordinator_tools = ToolRegistry()
    coordinator = OpenAIAgent(
        OpenAIAgentConfig(
            agent_name="coordinator",
            agent_type="openai",
            description=(
                "Orchestration coordinator that synthesises trip plans and delegates "
                "follow-up questions to the right specialist agents."
            ),
            system_prompt=(
                "You are a travel coordination expert. Your job is to:\n"
                "1. Synthesise information from specialist agents into polished travel plans.\n"
                "2. Answer follow-up questions by delegating to the right specialist.\n"
                "Use list_agents to find available specialists, then delegate_task to "
                "get their expertise. Present results in a clear, organised format."
            ),
            api_key=api_key,
            tool_registry=coordinator_tools,
            is_tool_caller=True,
        )
    )
    coordinator.tags = ["coordinator"]

    # ------------------------------------------------------------------
    # 5. AgentRegistry
    # ------------------------------------------------------------------
    agent_registry = AgentRegistry()
    agent_registry.register_agent(destination_expert)
    agent_registry.register_agent(itinerary_builder)
    agent_registry.register_agent(budget_advisor)
    agent_registry.register_agent(packing_advisor)
    agent_registry.register_agent(coordinator)

    # ------------------------------------------------------------------
    # 6. DelegationManager — wire list_agents + delegate_task into coordinator
    # ------------------------------------------------------------------
    delegation_manager = DelegationManager(agent_registry, max_depth=3)
    delegation_manager.setup_tools(coordinator_tools)

    return agent_registry, skill_registry, tool_registry, delegation_manager, mcp_client
