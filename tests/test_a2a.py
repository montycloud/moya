"""
Tests for moya.a2a — A2A protocol server and client.

Integration tests use httpx.ASGITransport to call the ASGI app directly,
without binding a real port. No network I/O takes place.
"""

from __future__ import annotations

import asyncio
import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from a2a.helpers.proto_helpers import new_text_message, new_text_status_update_event
from a2a.server.events import EventQueue
from a2a.server.agent_execution import RequestContext
from a2a.server.context import ServerCallContext
from a2a.types import TaskState, Role

from moya.a2a.agent_card import agent_card_from_moya, agent_card_to_dict
from moya.a2a.executor import MoyaAgentExecutor
from moya.a2a.server import A2AServer
from moya.a2a.client import A2AAgent, A2AAgentConfig
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.tools.tool_registry import ToolRegistry


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_echo_agent(name: str = "echo", response: str = "Hello back!") -> OpenAIAgent:
    os.environ.setdefault("OPENAI_API_KEY", "sk-test")
    config = OpenAIAgentConfig(
        agent_name=name,
        agent_type="openai",
        description=f"Echo agent {name}",
        api_key="sk-test",
        tool_registry=ToolRegistry(),
    )
    agent = OpenAIAgent(config)
    agent.client = MagicMock()
    agent.handle_message = MagicMock(return_value=response)
    return agent


def make_request_context(task_id: str = "task-1", context_id: str = "ctx-1", text: str = "hello") -> RequestContext:
    msg = new_text_message(text=text, context_id=context_id, task_id=task_id, role=Role.ROLE_USER)
    from a2a.types import SendMessageRequest
    req = SendMessageRequest(message=msg)
    ctx = ServerCallContext()
    return RequestContext(
        call_context=ctx,
        request=req,
        task_id=task_id,
        context_id=context_id,
    )


# ── agent_card_from_moya ──────────────────────────────────────────────────────

class TestAgentCard:
    def test_basic_fields(self):
        agent = make_echo_agent("my_agent")
        agent.description = "Does cool stuff"
        card = agent_card_from_moya(agent, "http://localhost:8000", version="2.0.0")
        assert card.name == "my_agent"
        assert card.description == "Does cool stuff"
        assert card.version == "2.0.0"

    def test_interface_url(self):
        agent = make_echo_agent()
        card = agent_card_from_moya(agent, "http://localhost:9000")
        assert len(card.supported_interfaces) == 1
        assert card.supported_interfaces[0].url == "http://localhost:9000"

    def test_capabilities_streaming_false(self):
        agent = make_echo_agent()
        card = agent_card_from_moya(agent, "http://localhost:8000", streaming=False)
        assert card.capabilities.streaming is False

    def test_capabilities_streaming_true(self):
        agent = make_echo_agent()
        card = agent_card_from_moya(agent, "http://localhost:8000", streaming=True)
        assert card.capabilities.streaming is True

    def test_skills_populated(self):
        from moya.skills.skill import Skill
        agent = make_echo_agent()
        skill = Skill(name="my_skill", description="A skill", version="1.0.0", tags=["demo"])
        agent.skills = [skill]
        card = agent_card_from_moya(agent, "http://localhost:8000")
        assert len(card.skills) == 1
        assert card.skills[0].id == "my_skill"
        assert card.skills[0].name == "my_skill"
        assert "demo" in card.skills[0].tags

    def test_no_skills_empty(self):
        agent = make_echo_agent()
        agent.skills = []
        card = agent_card_from_moya(agent, "http://localhost:8000")
        assert len(card.skills) == 0

    def test_to_dict(self):
        agent = make_echo_agent()
        card = agent_card_from_moya(agent, "http://localhost:8000")
        d = agent_card_to_dict(card)
        assert isinstance(d, dict)
        assert d["name"] == agent.agent_name


# ── MoyaAgentExecutor ─────────────────────────────────────────────────────────

class TestMoyaAgentExecutor:
    def _make_queue(self):
        """Mock queue with async enqueue_event (EventQueue.enqueue_event is async)."""
        events = []

        async def _enqueue(event):
            events.append(event)

        queue = MagicMock()
        queue.enqueue_event = _enqueue
        return queue, events

    @pytest.mark.asyncio
    async def test_execute_enqueues_working_and_completed(self):
        agent = make_echo_agent(response="The answer is 42.")
        executor = MoyaAgentExecutor(agent)
        context = make_request_context(text="What is the answer?")
        queue, events = self._make_queue()

        await executor.execute(context, queue)

        assert len(events) == 2
        assert events[0].status.state == TaskState.TASK_STATE_WORKING
        assert events[1].status.state == TaskState.TASK_STATE_COMPLETED
        from a2a.helpers.proto_helpers import get_message_text
        assert "42" in get_message_text(events[1].status.message)

    @pytest.mark.asyncio
    async def test_execute_enqueues_failed_on_exception(self):
        agent = make_echo_agent()
        agent.handle_message = MagicMock(side_effect=RuntimeError("model error"))
        executor = MoyaAgentExecutor(agent)
        context = make_request_context()
        queue, events = self._make_queue()

        await executor.execute(context, queue)

        states = [e.status.state for e in events]
        assert TaskState.TASK_STATE_FAILED in states
        failed_evt = next(e for e in events if e.status.state == TaskState.TASK_STATE_FAILED)
        from a2a.helpers.proto_helpers import get_message_text
        assert "model error" in get_message_text(failed_evt.status.message)

    @pytest.mark.asyncio
    async def test_cancel_enqueues_canceled(self):
        agent = make_echo_agent()
        executor = MoyaAgentExecutor(agent)
        context = make_request_context()
        queue, events = self._make_queue()

        await executor.cancel(context, queue)

        assert len(events) == 1
        assert events[0].status.state == TaskState.TASK_STATE_CANCELED

    @pytest.mark.asyncio
    async def test_execute_passes_user_input_to_agent(self):
        agent = make_echo_agent()
        executor = MoyaAgentExecutor(agent)
        context = make_request_context(text="Tell me a joke")
        queue, _ = self._make_queue()

        await executor.execute(context, queue)

        agent.handle_message.assert_called_once()
        assert agent.handle_message.call_args[0][0] == "Tell me a joke"

    @pytest.mark.asyncio
    async def test_execute_passes_thread_id(self):
        agent = make_echo_agent()
        executor = MoyaAgentExecutor(agent)
        context = make_request_context(context_id="my-thread")
        queue, _ = self._make_queue()

        await executor.execute(context, queue)

        _, kwargs = agent.handle_message.call_args
        assert kwargs.get("thread_id") == "my-thread"


# ── A2AServer construction ────────────────────────────────────────────────────

class TestA2AServer:
    def test_construction(self):
        agent = make_echo_agent()
        server = A2AServer(agent, endpoint_url="http://localhost:8000")
        assert server.agent is agent
        assert server.agent_card.name == agent.agent_name
        assert server.app is not None

    def test_custom_agent_card(self):
        agent = make_echo_agent()
        custom_card = agent_card_from_moya(agent, "http://custom:9999", version="3.0.0")
        server = A2AServer(agent, endpoint_url="http://localhost:8000", agent_card=custom_card)
        assert server.agent_card.version == "3.0.0"

    def test_app_is_asgi(self):
        agent = make_echo_agent()
        server = A2AServer(agent, endpoint_url="http://localhost:8000")
        # ASGI apps are callables
        assert callable(server.app)

    @pytest.mark.asyncio
    async def test_agent_card_endpoint(self):
        import httpx
        agent = make_echo_agent("card_agent")
        server = A2AServer(agent, endpoint_url="http://localhost:8000")
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=server.app),
            base_url="http://test",
        ) as client:
            resp = await client.get("/.well-known/agent-card.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "card_agent"

    @pytest.mark.asyncio
    async def test_send_message_returns_200(self):
        import httpx
        from google.protobuf.json_format import MessageToJson
        from a2a.types import SendMessageRequest, SendMessageConfiguration
        from a2a.utils.constants import VERSION_HEADER, PROTOCOL_VERSION_1_0

        agent = make_echo_agent(response="Pong!")
        server = A2AServer(agent, endpoint_url="http://localhost:8000")

        msg = new_text_message(text="Ping", role=Role.ROLE_USER, context_id="c1")
        cfg = SendMessageConfiguration()
        cfg.return_immediately = True
        req = SendMessageRequest(message=msg, configuration=cfg)
        body = json.loads(MessageToJson(req))

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=server.app),
            base_url="http://test",
            timeout=10.0,
        ) as client:
            resp = await client.post(
                "/message:send",
                json=body,
                headers={VERSION_HEADER: PROTOCOL_VERSION_1_0},
            )

        assert resp.status_code == 200


# ── A2AAgent ──────────────────────────────────────────────────────────────────

class TestA2AAgentConfig:
    def test_requires_endpoint_url(self):
        with pytest.raises(ValueError, match="endpoint_url"):
            A2AAgent(A2AAgentConfig(
                agent_name="x",
                agent_type="a2a",
                description="test",
                endpoint_url="",
            ))

    def test_construction(self):
        config = A2AAgentConfig(
            agent_name="remote",
            agent_type="a2a",
            description="Remote agent",
            endpoint_url="http://localhost:8001",
        )
        agent = A2AAgent(config)
        assert agent.endpoint_url == "http://localhost:8001"
        assert agent.agent_name == "remote"

    def test_trailing_slash_stripped(self):
        config = A2AAgentConfig(
            agent_name="r",
            agent_type="a2a",
            description="d",
            endpoint_url="http://localhost:8000/",
        )
        a = A2AAgent(config)
        assert a.endpoint_url == "http://localhost:8000"


class TestA2AAgentIntegration:
    """Tests for A2AAgent — create_client is mocked to avoid real HTTP."""

    def _make_client_agent(self, endpoint: str = "http://test-server") -> A2AAgent:
        config = A2AAgentConfig(
            agent_name="proxy",
            agent_type="a2a",
            description="Proxy to test server",
            endpoint_url=endpoint,
        )
        return A2AAgent(config)

    def _make_mock_a2a_client(self, response_text: str = "The answer is 7."):
        """Return a mock A2A Client whose send_message yields a completed status event."""
        from a2a.helpers.proto_helpers import new_text_status_update_event
        from a2a.types import StreamResponse, TaskState

        completed_event = new_text_status_update_event(
            task_id="t1",
            context_id="c1",
            state=TaskState.TASK_STATE_COMPLETED,
            text=response_text,
        )
        stream_resp = StreamResponse()
        stream_resp.status_update.CopyFrom(completed_event)

        async def _fake_send_message(request):
            yield stream_resp

        mock_client = MagicMock()
        mock_client.send_message = _fake_send_message
        return mock_client

    @pytest.mark.asyncio
    async def test_handle_message_returns_response(self):
        agent = self._make_client_agent()
        mock_a2a_client = self._make_mock_a2a_client("The answer is 7.")

        with patch("moya.a2a.client.create_client", new=AsyncMock(return_value=mock_a2a_client)):
            result = await agent._async_handle_message("What is the answer?", thread_id="t1")

        assert "7" in result

    @pytest.mark.asyncio
    async def test_handle_message_raises_on_failure(self):
        from a2a.helpers.proto_helpers import new_text_status_update_event
        from a2a.types import StreamResponse, TaskState

        failed_event = new_text_status_update_event(
            task_id="t1", context_id="c1",
            state=TaskState.TASK_STATE_FAILED, text="upstream error",
        )
        stream_resp = StreamResponse()
        stream_resp.status_update.CopyFrom(failed_event)

        async def _fake_send(request):
            yield stream_resp

        mock_client = MagicMock()
        mock_client.send_message = _fake_send
        agent = self._make_client_agent()

        with patch("moya.a2a.client.create_client", new=AsyncMock(return_value=mock_client)):
            with pytest.raises(RuntimeError, match="upstream error"):
                await agent._async_handle_message("test", thread_id="c1")

    @pytest.mark.asyncio
    async def test_fetch_agent_card(self):
        agent = self._make_client_agent()
        with patch("httpx.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = {"name": "backend"}
            mock_get.return_value = mock_resp
            card = agent.fetch_agent_card()
        assert card["name"] == "backend"
