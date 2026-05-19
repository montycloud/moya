"""
BedrockAgent for Moya.

Uses AWS Bedrock's Converse API — the model-agnostic endpoint that works
with Claude, Llama, Titan, Mistral and others, with native tool-calling
support across all models that support it.

AWS credentials are resolved via the standard boto3 credential chain
(environment variables, ~/.aws/credentials, IAM role, etc.).
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional

from moya.agents.agent import Agent, AgentConfig

_SCHEMA_PASSTHROUGH = ("enum", "items", "properties", "additionalProperties",
                       "minimum", "maximum", "minLength", "maxLength", "pattern")


def _bedrock_property(pinfo: Dict[str, Any]) -> Dict[str, Any]:
    """Build a Bedrock-compatible property schema, preserving rich constraints."""
    schema: Dict[str, Any] = {
        "type": pinfo["type"],
        "description": pinfo.get("description", ""),
    }
    for key in _SCHEMA_PASSTHROUGH:
        if key in pinfo:
            schema[key] = pinfo[key]
    return schema


@dataclass
class BedrockAgentConfig(AgentConfig):
    model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    region: str = "us-east-1"
    max_iterations: int = 5


class BedrockAgent(Agent):
    """
    AWS Bedrock agent using the Converse API.

    Works with any Bedrock-hosted model that supports the Converse API.
    Tool calling is supported for models that advertise tool-use capability.
    """

    def __init__(self, config: BedrockAgentConfig):
        try:
            import boto3
        except ImportError:
            raise ImportError(
                "boto3 is required for BedrockAgent. "
                "Install it with: pip install boto3"
            )
        super().__init__(config=config)
        self.model_id = config.model_id
        self.region = config.region
        self.max_iterations = config.max_iterations
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=self.region,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def handle_message(self, message: str, **kwargs) -> str:
        thread_id = kwargs.get("thread_id", "default")
        conversation = [{"role": "user", "content": [{"text": message}]}]
        result = self._run_tool_loop(conversation)
        self._remember(thread_id, message, result)
        return result

    def handle_message_stream(self, message: str, **kwargs) -> Iterator[str]:
        """
        Stream the response token by token.

        When tool calls are required the tool loop runs non-streaming internally
        and the final answer is yielded as a single chunk. Pure-text responses
        are streamed word by word.
        """
        thread_id = kwargs.get("thread_id", "default")

        if self.tool_registry and self.tool_registry.get_tools():
            # Run non-streaming tool loop; yield complete answer as one chunk
            result = self.handle_message(message, **kwargs)
            yield result
            return

        full_response = ""
        try:
            response = self.client.converse_stream(
                modelId=self.model_id,
                system=[{"text": self.system_prompt}],
                messages=[{"role": "user", "content": [{"text": message}]}],
                inferenceConfig=self._inference_config(),
            )
            for event in response["stream"]:
                if "contentBlockDelta" in event:
                    delta = event["contentBlockDelta"]["delta"]
                    if "text" in delta:
                        full_response += delta["text"]
                        yield delta["text"]
        except Exception as e:
            error = f"[BedrockAgent error: {e}]"
            yield error
            full_response = error

        self._remember(thread_id, message, full_response)

    # ------------------------------------------------------------------
    # Tool definitions (Bedrock Converse API format)
    # ------------------------------------------------------------------

    def get_tool_definitions(self) -> Optional[List[Dict[str, Any]]]:
        if not self.tool_registry:
            return None
        return [
            {
                "toolSpec": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                pname: _bedrock_property(pinfo)
                                for pname, pinfo in (tool.parameters or {}).items()
                            },
                            "required": [
                                pname
                                for pname, pinfo in (tool.parameters or {}).items()
                                if pinfo.get("required", False)
                            ],
                        }
                    },
                }
            }
            for tool in self.tool_registry.get_tools()
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _inference_config(self) -> Dict[str, Any]:
        return {
            "maxTokens": self.llm_config.get("max_tokens", 2000),
            "temperature": self.llm_config.get("temperature", 0.7),
            "topP": self.llm_config.get("top_p", 1.0),
        }

    def _run_tool_loop(self, conversation: List[Dict[str, Any]]) -> str:
        tool_defs = self.get_tool_definitions()
        kwargs: Dict[str, Any] = {
            "modelId": self.model_id,
            "system": [{"text": self.system_prompt}],
            "messages": conversation,
            "inferenceConfig": self._inference_config(),
        }
        if tool_defs:
            kwargs["toolConfig"] = {"tools": tool_defs}

        for _ in range(self.max_iterations):
            try:
                response = self.client.converse(**kwargs)
            except Exception as e:
                return f"[BedrockAgent error: {e}]"

            stop_reason = response.get("stopReason", "end_turn")
            content = response["output"]["message"]["content"]

            if stop_reason != "tool_use":
                return next((b["text"] for b in content if "text" in b), "")

            # Execute tool calls and continue the conversation
            conversation.append({"role": "assistant", "content": content})
            tool_results = []
            for block in content:
                if "toolUse" not in block:
                    continue
                tu = block["toolUse"]
                result = self._execute_tool(tu["name"], tu.get("input", {}))
                tool_results.append({
                    "toolResult": {
                        "toolUseId": tu["toolUseId"],
                        "content": [{"text": str(result)}],
                    }
                })
            conversation.append({"role": "user", "content": tool_results})
            kwargs["messages"] = conversation

        return "[BedrockAgent: max tool iterations reached]"

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
