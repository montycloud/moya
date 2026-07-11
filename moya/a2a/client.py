"""
A2AAgent — a Moya Agent that delegates to a remote A2A endpoint.

Usage::

    from moya.a2a.client import A2AAgent, A2AAgentConfig

    config = A2AAgentConfig(
        agent_name="remote_helper",
        agent_type="a2a",
        description="Connects to a remote A2A agent at localhost:8001",
        endpoint_url="http://localhost:8001",
    )
    agent = A2AAgent(config)
    response = agent.handle_message("What is the capital of France?")
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterator, Optional

from moya.agents.agent import Agent, AgentConfig

try:
    from a2a.client import create_client
except ImportError:
    create_client = None  # type: ignore[assignment]


@dataclass
class A2AAgentConfig(AgentConfig):
    """
    Configuration for an A2AAgent.

    Args:
        endpoint_url:     Base URL of the remote A2A server
                          (e.g. ``"http://localhost:8000"``).
        timeout_seconds:  HTTP timeout for individual requests (default 60 s).
        card_path:        Relative path used to resolve the AgentCard
                          (default ``"/.well-known/agent-card.json"``).
    """
    endpoint_url: str = ""
    timeout_seconds: float = 60.0
    card_path: str = "/.well-known/agent-card.json"


class A2AAgent(Agent):
    """
    A Moya ``Agent`` that forwards every ``handle_message()`` call to a
    remote A2A-compliant server and returns the completed task response.

    The A2A SDK client is async; this class bridges to Moya's synchronous
    interface using ``asyncio.run()`` (or the running loop if one exists).
    """

    def __init__(self, config: A2AAgentConfig) -> None:
        super().__init__(config)
        if not config.endpoint_url:
            raise ValueError("A2AAgentConfig.endpoint_url is required.")
        self.endpoint_url = config.endpoint_url.rstrip("/")
        self.timeout_seconds = config.timeout_seconds
        self.card_path = config.card_path

    # ------------------------------------------------------------------
    # Moya Agent interface
    # ------------------------------------------------------------------

    def handle_message(self, message: str, **kwargs) -> str:
        """
        Send *message* to the remote A2A agent and return the response text.

        Blocks until the remote agent completes the task or the timeout
        is exceeded.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Already inside an async context — schedule a new task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    asyncio.run,
                    self._async_handle_message(message, **kwargs),
                )
                return future.result(timeout=self.timeout_seconds + 5)
        else:
            return asyncio.run(self._async_handle_message(message, **kwargs))

    def handle_message_stream(self, message: str, **kwargs) -> Iterator[str]:
        """Yield the full response as a single chunk (streaming not implemented)."""
        yield self.handle_message(message, **kwargs)

    # ------------------------------------------------------------------
    # Async implementation
    # ------------------------------------------------------------------

    async def _async_handle_message(self, message: str, **kwargs) -> str:
        import httpx
        from a2a.helpers.proto_helpers import (
            new_text_message,
            get_stream_response_text,
        )
        from a2a.types import SendMessageRequest, Role, TaskState

        context_id = kwargs.get("thread_id") or None
        timeout = httpx.Timeout(self.timeout_seconds)

        async with httpx.AsyncClient(timeout=timeout) as http:  # noqa: F841
            client = await create_client(
                self.endpoint_url,
                relative_card_path=self.card_path,
            )

            user_msg = new_text_message(
                text=message,
                context_id=context_id,
                role=Role.ROLE_USER,
            )
            request = SendMessageRequest(message=user_msg)

            chunks: list[str] = []
            final_state: int = TaskState.TASK_STATE_UNSPECIFIED

            async for stream_response in client.send_message(request):
                # Each StreamResponse wraps a TaskStatusUpdateEvent or similar
                chunk = get_stream_response_text(stream_response)
                if chunk:
                    chunks.append(chunk)

                # Track task state from status updates
                if stream_response.HasField("status_update"):
                    final_state = stream_response.status_update.status.state

            if final_state == TaskState.TASK_STATE_FAILED:
                error = " ".join(chunks) or "Remote agent task failed."
                raise RuntimeError(f"[A2AAgent] Remote task failed: {error}")

            # Filter out the "Processing…" working-state message
            meaningful = [c for c in chunks if c and c != "Processing…"]
            return "\n".join(meaningful) if meaningful else ""

    # ------------------------------------------------------------------
    # Agent Card discovery
    # ------------------------------------------------------------------

    def fetch_agent_card(self) -> dict:
        """
        Fetch and return the remote agent's card as a plain dict.

        Useful for discovery and capability inspection.
        """
        import httpx
        url = f"{self.endpoint_url}{self.card_path}"
        response = httpx.get(url, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()
