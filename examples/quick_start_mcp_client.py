"""
MCP Client example — connect to an MCP server and use its tools in a MOYA agent.

This script:
  1. Launches quick_start_mcp_server.py as a subprocess (the MCP server).
  2. Connects to it using MCPClient.from_subprocess().
  3. Discovers the server's tools and registers them in a shared ToolRegistry.
  4. Creates an OpenAI agent that uses those tools to answer questions.

The agent never knows that the tools come from an external process — they look
and behave like any other MOYA tool.

Requires: OPENAI_API_KEY environment variable.
"""

import os
import sys

from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.mcp import MCPClient
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.registry.agent_registry import AgentRegistry
from moya.tools.tool_registry import ToolRegistry


def setup() -> SimpleOrchestrator:
    tool_registry = ToolRegistry()

    # ------------------------------------------------------------------
    # Connect to the MCP server (launches it as a subprocess)
    # ------------------------------------------------------------------
    server_script = os.path.join(os.path.dirname(__file__), "quick_start_mcp_server.py")

    print("Connecting to MCP server...")
    client = MCPClient.from_subprocess(
        command=sys.executable,
        args=[server_script],
        name="text_tools",
    )

    # Discover tools and add them to the registry
    mcp_tools = client.get_tools()
    for tool in mcp_tools:
        tool_registry.register_tool(tool)

    print(f"Discovered {len(mcp_tools)} MCP tools: {[t.name for t in mcp_tools]}")
    print(f"Tool catalog: {[t['name'] for t in tool_registry.get_catalog()]}")

    # ------------------------------------------------------------------
    # Create an agent that uses the MCP tools
    # ------------------------------------------------------------------
    config = OpenAIAgentConfig(
        agent_name="text_analyst",
        description="Analyses text using specialised text tools.",
        agent_type="OpenAIAgent",
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4o-mini",
        tool_registry=tool_registry,
        is_tool_caller=True,
        system_prompt=(
            "You are a text analysis assistant. You have access to text tools. "
            "Use them to answer questions accurately. "
            "Note: tool names are prefixed with 'text_tools/' (e.g. 'text_tools/word_count')."
        ),
    )
    agent = OpenAIAgent(config)

    registry = AgentRegistry()
    registry.register_agent(agent)

    orchestrator = SimpleOrchestrator(
        agent_registry=registry,
        default_agent_name="text_analyst",
    )

    # Keep client alive for the session lifetime (don't close it yet)
    orchestrator._mcp_client = client  # hold reference to prevent GC

    return orchestrator


def main() -> None:
    orchestrator = setup()
    thread_id = "mcp-demo"

    questions = [
        "How many words are in the phrase 'The quick brown fox jumps over the lazy dog'?",
        "What is the sentiment of: 'This is a wonderful and fantastic product!'",
        "Reverse the words in: 'Hello World from MOYA'",
    ]

    for q in questions:
        print(f"\nUser: {q}")
        response = orchestrator.orchestrate(thread_id, q)
        print(f"Agent: {response}")

    # Clean up
    if hasattr(orchestrator, "_mcp_client"):
        orchestrator._mcp_client.close()


if __name__ == "__main__":
    main()
