"""
OpenAIAgent for Moya.

Uses OpenAI's ChatCompletion API. Supports tool calling and genuine
token-by-token streaming via handle_message_stream().
"""

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional

from openai import OpenAI

from moya.agents.agent import Agent, AgentConfig

_SCHEMA_PASSTHROUGH = ("enum", "items", "properties", "additionalProperties",
                       "minimum", "maximum", "minLength", "maxLength", "pattern")


def _openai_property(pinfo: Dict[str, Any]) -> Dict[str, Any]:
    """Build an OpenAI-compatible property schema, preserving rich constraints."""
    schema: Dict[str, Any] = {
        "type": pinfo["type"],
        "description": pinfo.get("description", ""),
    }
    for key in _SCHEMA_PASSTHROUGH:
        if key in pinfo:
            schema[key] = pinfo[key]
    return schema


@dataclass
class OpenAIAgentConfig(AgentConfig):
    model_name: str = "gpt-4o"
    api_key: Optional[str] = None
    tool_choice: Optional[str] = None
    max_iterations: int = 5


class OpenAIAgent(Agent):
    """
    OpenAI-backed agent with tool calling and streaming support.
    """

    def __init__(self, config: OpenAIAgentConfig):
        super().__init__(config=config)
        if not config.api_key:
            raise ValueError("OpenAI API key is required for OpenAIAgent.")
        self.client = OpenAI(api_key=config.api_key)
        self.model_name = config.model_name
        self.tool_choice = config.tool_choice
        self.max_iterations = config.max_iterations

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
        Yield response tokens as they arrive from the API.

        When tools are registered the first streaming pass collects tool calls,
        executes them, then streams the final answer. Callers always receive a
        proper generator regardless of whether tools are used.
        """
        thread_id = kwargs.get("thread_id", "default")
        conversation = self._build_conversation(message)
        full_response = ""

        for _ in range(self.max_iterations):
            response_text, tool_calls = yield from self._stream_one_turn(conversation)
            full_response = response_text

            if not tool_calls:
                break

            # Append assistant turn with tool calls, then tool results
            entry: Dict[str, Any] = {"role": "assistant", "content": response_text}
            entry["tool_calls"] = tool_calls
            conversation.append(entry)
            for tc in tool_calls:
                conversation.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id"),
                    "content": self._execute_tool(tc),
                })

        self._remember(thread_id, message, full_response)

    # ------------------------------------------------------------------
    # Tool definitions (OpenAI-specific format)
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
                            pname: _openai_property(pinfo)
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
        """Non-streaming tool loop; returns the final assistant text."""
        for _ in range(self.max_iterations):
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=conversation,
                tools=self.get_tool_definitions(),
                tool_choice=self.tool_choice if self.tool_registry else None,
            )
            msg = response.choices[0].message
            content = msg.content or ""
            tool_calls = msg.tool_calls or []

            entry: Dict[str, Any] = {"role": "assistant", "content": content}
            if tool_calls:
                entry["tool_calls"] = [tc.dict() for tc in tool_calls]
            conversation.append(entry)

            if not tool_calls:
                return content

            for tc in tool_calls:
                tc_dict = tc.dict()
                conversation.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": self._execute_tool(tc_dict),
                })

        return conversation[-1].get("content", "")

    def _stream_one_turn(self, conversation):
        """
        Stream one LLM turn, yielding text chunks.

        Returns (response_text, tool_calls) via a generator that yields str chunks.
        Use as: response_text, tool_calls = yield from self._stream_one_turn(conv)
        """
        response_text = ""
        tool_calls: List[Dict[str, Any]] = []

        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=conversation,
            tools=self.get_tool_definitions(),
            tool_choice=self.tool_choice if self.tool_registry else None,
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                response_text += delta.content
                yield delta.content
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    while len(tool_calls) <= idx:
                        tool_calls.append(
                            {"id": "", "type": "function",
                             "function": {"name": "", "arguments": ""}}
                        )
                    tc = tool_calls[idx]
                    if tc_delta.id:
                        tc["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tc["function"]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            tc["function"]["arguments"] += tc_delta.function.arguments

        return response_text, tool_calls

    def _execute_tool(self, tool_call: Dict[str, Any]) -> str:
        if not self.tool_registry:
            return "[No tool registry attached]"
        fn = tool_call.get("function", {})
        name = fn.get("name", "")
        try:
            args = json.loads(fn.get("arguments", "{}"))
        except json.JSONDecodeError:
            args = {}
        tool = self.tool_registry.get_tool(name)
        if not tool:
            return f"[Tool '{name}' not found]"
        try:
            return str(tool.function(**args))
        except Exception as e:
            return f"[Error in tool '{name}': {e}]"
