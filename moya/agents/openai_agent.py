"""
OpenAIAgent for Moya.

An Agent that uses OpenAI's ChatCompletion or Completion API
to generate responses, pulling API key from the environment.
"""


import os
from openai import OpenAI
from dataclasses import dataclass
from dataclasses import dataclass

from typing import Any, Dict, Optional
from moya.agents.base_agent import Agent
from moya.agents.base_agent import AgentConfig

@dataclass
class OpenAIAgentConfig(AgentConfig):
    """
    Configuration data for an OpenAIAgent.
    """
    model_name: str = "gpt-4o"
    api_key: str = None
    streaming: bool = False
class OpenAIAgent(Agent):
    """
    A simple OpenAI-based agent that uses the ChatCompletion API.
    """

    def __init__(
        self,
        config: OpenAIAgentConfig   
    ):
        """
        :param agent_name: Unique name or identifier for the agent.
        :param description: A brief explanation of the agent's capabilities.
        :param model_name: The OpenAI model name (e.g., "gpt-3.5-turbo").
        :param config: Optional config dict (unused by default).
        :param tool_registry: Optional ToolRegistry to enable tool calling.
        :param agent_config: Optional configuration for the agent.
        """
        super().__init__(config=config)
        self.model_name = config.model_name
        if not config.api_key:
            raise ValueError("OpenAI API key is required for OpenAIAgent.")
        self.client = OpenAI(api_key=config.api_key)
        self.streaming = config.streaming
        self.system_prompt = config.system_prompt

    def handle_message(self, message: str, **kwargs) -> str:
        """
        Calls OpenAI ChatCompletion to handle the user's message.
        """
        try:
            response = self.client.chat.completions.create(model=self.model_name,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message},
            ])
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAIAgent error: {str(e)}]"

    def handle_message_stream(self, message: str, **kwargs):
        """
        Calls OpenAI ChatCompletion to handle the user's message with streaming support.
        """
        # Starting streaming response from OpenAIAgent
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message},
                ],
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    yield content
        except Exception as e:
            error_message = f"[OpenAIAgent error: {str(e)}]"
            print(error_message)
            yield error_message
