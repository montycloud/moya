"""
OllamaAgent for Moya.

An Agent that uses Ollama's API to generate responses using locally hosted models.
"""

import requests
import json
from typing import Any, Dict, Optional
from dataclasses import dataclass
from moya.agents.base_agent import Agent, AgentConfig


@dataclass
class OllamaAgentConfig(AgentConfig):
    base_url: str = "http://localhost:11434"
    model_name: str = "llama2"
    context_window: int = 4096
    num_ctx: int = 4096
    repeat_penalty: float = 1.1


class OllamaAgent(Agent):
    """
    A simple Ollama-based agent that uses the local Ollama API.
    """

    def __init__(
        self,
        agent_name: str,
        description: str,
        config: Optional[Dict[str, Any]] = None,
        tool_registry: Optional[Any] = None,
        agent_config: Optional[OllamaAgentConfig] = None
    ):
        """
        :param agent_name: Unique name or identifier for the agent.
        :param description: A brief explanation of the agent's capabilities.
        :param config: Optional config dict (unused by default).
        :param tool_registry: Optional ToolRegistry to enable tool calling.
        :param agent_config: Optional OllamaAgentConfig instance.
        """
        super().__init__(
            agent_name=agent_name,
            agent_type="OllamaAgent",
            description=description,
            config=config,
            tool_registry=tool_registry
        )
        self.agent_config = agent_config or OllamaAgentConfig()
        self.system_prompt = self.agent_config.system_prompt
        self.base_url = self.agent_config.base_url
        self.model_name = self.agent_config.model_name

    def setup(self) -> None:
        """
        Verify Ollama server is accessible.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                raise ConnectionError("Unable to connect to Ollama server")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Ollama server: {str(e)}")

    def handle_message(self, message: str, **kwargs) -> str:
        """
        Calls Ollama API to handle the user's message.
        """
        try:
            # Combine system prompt and user message
            prompt = f"{self.system_prompt}\n\nUser: {message}\nAssistant:"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            return f"[OllamaAgent error: {str(e)}]"

    def handle_message_stream(self, message: str, **kwargs):
        """
        Calls Ollama API to handle the user's message with streaming support.
        """
        try:
            # Combine system prompt and user message
            prompt = f"{self.system_prompt}\n\nUser: {message}\nAssistant:"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": True
                },
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        if "response" in chunk:
                            yield chunk["response"]
                    except json.JSONDecodeError:
                        continue
                            
        except Exception as e:
            error_message = f"[OllamaAgent error: {str(e)}]"
            print(error_message)
            yield error_message
