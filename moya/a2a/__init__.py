"""
moya.a2a — Agent-to-Agent (A2A) protocol support for Moya.

Expose any Moya agent as an A2A server, or connect to a remote A2A agent
as a first-class Moya agent.

Quick start — server::

    from moya.a2a import A2AServer

    server = A2AServer(agent=my_agent, endpoint_url="http://localhost:8000")
    server.run()  # starts uvicorn on port 8000

Quick start — client::

    from moya.a2a import A2AAgent, A2AAgentConfig

    config = A2AAgentConfig(
        agent_name="remote",
        agent_type="a2a",
        description="Remote A2A agent",
        endpoint_url="http://localhost:8000",
    )
    agent = A2AAgent(config)
    print(agent.handle_message("Hello!"))
"""

from moya.a2a.agent_card import agent_card_from_moya, agent_card_to_dict
from moya.a2a.client import A2AAgent, A2AAgentConfig
from moya.a2a.executor import MoyaAgentExecutor
from moya.a2a.server import A2AServer

__all__ = [
    "A2AServer",
    "A2AAgent",
    "A2AAgentConfig",
    "MoyaAgentExecutor",
    "agent_card_from_moya",
    "agent_card_to_dict",
]
