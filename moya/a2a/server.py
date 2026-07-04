"""
A2AServer — expose any Moya Agent as an A2A-compliant HTTP endpoint.

Usage::

    from moya.a2a.server import A2AServer

    server = A2AServer(
        agent=my_moya_agent,
        endpoint_url="http://localhost:8000",
        host="0.0.0.0",
        port=8000,
    )

    # Get the ASGI app (for testing or custom ASGI servers)
    app = server.app

    # Or start uvicorn directly
    server.run()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_rest_routes, create_agent_card_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard

from moya.a2a.agent_card import agent_card_from_moya
from moya.a2a.executor import MoyaAgentExecutor

if TYPE_CHECKING:
    from moya.agents.agent import Agent


class A2AServer:
    """
    Wraps a Moya ``Agent`` into a fully compliant A2A HTTP server.

    The server exposes:
    - ``POST /message:send``            — send a message / create a task
    - ``POST /message:stream``          — streaming variant
    - ``GET  /tasks/{id}``              — fetch a task by ID
    - ``POST /tasks/{id}:cancel``       — cancel a running task
    - ``GET  /.well-known/agent-card.json`` — Agent Card discovery

    Args:
        agent:        Moya agent to expose.
        endpoint_url: Public base URL of this server (written into the AgentCard).
        host:         Bind address for ``run()`` (default ``"0.0.0.0"``).
        port:         Port for ``run()`` (default ``8000``).
        version:      AgentCard version string.
        streaming:    Advertise streaming support in the AgentCard.
        agent_card:   Supply a pre-built ``AgentCard`` to override auto-generation.
    """

    def __init__(
        self,
        agent: "Agent",
        endpoint_url: str,
        host: str = "0.0.0.0",
        port: int = 8000,
        version: str = "1.0.0",
        streaming: bool = False,
        agent_card: AgentCard | None = None,
    ) -> None:
        self.agent = agent
        self.endpoint_url = endpoint_url
        self.host = host
        self.port = port

        self.agent_card: AgentCard = agent_card or agent_card_from_moya(
            agent, endpoint_url, version=version, streaming=streaming
        )

        executor = MoyaAgentExecutor(agent)
        task_store = InMemoryTaskStore()
        self._handler = DefaultRequestHandler(
            agent_executor=executor,
            task_store=task_store,
            agent_card=self.agent_card,
        )
        self._app = self._build_app()

    def _build_app(self):
        try:
            from starlette.applications import Starlette
            from starlette.routing import Route
        except ImportError as exc:
            raise ImportError(
                "starlette is required to use A2AServer. "
                "Install it with: pip install starlette sse-starlette"
            ) from exc

        routes = [
            *create_agent_card_routes(self.agent_card),
            *create_rest_routes(self._handler),
        ]
        return Starlette(routes=routes)

    @property
    def app(self):
        """The ASGI application — pass this to any ASGI server or test client."""
        return self._app

    def run(self, host: str | None = None, port: int | None = None, **uvicorn_kwargs) -> None:
        """
        Start a blocking uvicorn server.

        Args:
            host:            Override bind address.
            port:            Override port.
            **uvicorn_kwargs: Forwarded to ``uvicorn.run()``.
        """
        try:
            import uvicorn
        except ImportError as exc:
            raise ImportError(
                "uvicorn is required to use A2AServer.run(). "
                "Install it with: pip install uvicorn"
            ) from exc

        uvicorn.run(
            self._app,
            host=host or self.host,
            port=port or self.port,
            **uvicorn_kwargs,
        )
