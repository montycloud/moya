"""
OllamaAgent for Moya.

Uses the Ollama /api/chat endpoint, which supports tool calling for models
that have function-calling capability (e.g. llama3.1, mistral, qwen2.5).

The Ollama server URL is configured via OllamaAgentConfig.base_url or the
OLLAMA_BASE_URL environment variable (default: http://localhost:11434).
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional

import requests

from moya.agents.agent import Agent, AgentConfig


@dataclass
class OllamaAgentConfig(AgentConfig):
    model_name: str = "llama3.1"
    base_url: str = field(
        default_factory=lambda: os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    max_iterations: int = 5


class OllamaAgent(Agent):
    """
    Ollama-backed agent with tool calling and streaming support.

    Call setup() to verify the server is reachable before first use.
    Agents that don't call setup() will surface connection errors lazily
    on the first handle_message() call instead of at construction time.
    """

    def __init__(self, config: OllamaAgentConfig):
        super().__init__(config=config)
        self.base_url = config.base_url.rstrip("/")
        self.model_name = config.model_name
        self.max_iterations = config.max_iterations

    def setup(self) -> None:
        """Verify the Ollama server is reachable. Raises ConnectionError on failure."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError(f"Ollama server responded with {response.status_code}")
        except requests.RequestException as e:
            raise ConnectionError(f"Cannot reach Ollama server at {self.base_url}: {e}") from e

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def handle_message(self, message: str, **kwargs) -> str:
        thread_id = kwargs.get("thread_id", "default")
        conversation = self._build_conversation(message)
        result = self._run_tool_loop(conversation)
        self._remember(thread_id, message, result)
        return result

    def handle_message_stream(self, message: str, **kwargs) -> Iterator[str]:
        """
        Yield response tokens as they arrive from Ollama.

        When tools are registered the full tool loop runs first and the
        complete answer is yielded as a single chunk (Ollama's streaming
        format does not interleave tool calls with text deltas).
        """
        thread_id = kwargs.get("thread_id", "default")

        if self.tool_registry and self.tool_registry.get_tools():
            result = self.handle_message(message, **kwargs)
            yield result
            return

        full_response = ""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": self._build_conversation(message),
                    "stream": True,
                },
                stream=True,
                timeout=120,
            )
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line.decode("utf-8"))
                    chunk = data.get("message", {}).get("content", "")
                    if chunk:
                        full_response += chunk
                        yield chunk
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            error = f"[OllamaAgent error: {e}]"
            yield error
            full_response = error

        self._remember(thread_id, message, full_response)

    # ------------------------------------------------------------------
    # Tool definitions (OpenAI-compatible format that Ollama accepts)
    # ------------------------------------------------------------------

    def get_tool_definitions(self) -> Optional[List[Dict[str, Any]]]:
        if not self.tool_registry:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            pname: {"type": pinfo["type"], "description": pinfo["description"]}
                            for pname, pinfo in (tool.parameters or {}).items()
                        },
                        "required": [
                            pname for pname, pinfo in (tool.parameters or {}).items()
                            if pinfo.get("required", False)
                        ],
                    },
                },
            }
            for tool in self.tool_registry.get_tools()
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_conversation(self, message: str) -> List[Dict[str, Any]]:
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": message},
        ]

    def _run_tool_loop(self, conversation: List[Dict[str, Any]]) -> str:
        tool_defs = self.get_tool_definitions()

        for _ in range(self.max_iterations):
            payload: Dict[str, Any] = {
                "model": self.model_name,
                "messages": conversation,
                "stream": False,
            }
            if tool_defs:
                payload["tools"] = tool_defs

            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=120,
                )
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                return f"[OllamaAgent error: {e}]"

            msg = data.get("message", {})
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls", [])

            if not tool_calls:
                return content

            # Add assistant turn and execute each tool call
            conversation.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
            for tc in tool_calls:
                fn = tc.get("function", {})
                name = fn.get("name", "")
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                result = self._execute_tool(name, args)
                conversation.append({
                    "role": "tool",
                    "content": str(result),
                    "name": name,
                })

        return "[OllamaAgent: max tool iterations reached]"

    def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        if not self.tool_registry:
            return "[No tool registry attached]"
        tool = self.tool_registry.get_tool(name)
        if not tool:
            return f"[Tool '{name}' not found]"
        try:
            return str(tool.function(**arguments))
        except Exception as e:
            return f"[Error in tool '{name}': {e}]"
