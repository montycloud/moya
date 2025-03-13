"""
OpenAIAgent for Moya.

An Agent that uses OpenAI's ChatCompletion or Completion API
to generate responses, pulling API key from the environment.
"""


import os
from openai import AzureOpenAI
from dataclasses import dataclass

from typing import Any, Dict, Optional
from moya.agents.base_agent import Agent, AgentConfig


@dataclass
class AzureOpenAIAgentConfig(AgentConfig):
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    organization: Optional[str] = None
    model_name: str = "gpt-4o"


class AzureOpenAIAgent(Agent):
    """
    A simple AzureOpenAI-based agent that uses the ChatCompletion API.
    """

    def __init__(
        self,
        agent_name: str,
        description: str,
        config: Optional[Dict[str, Any]] = None,
        tool_registry: Optional[Any] = None,
        agent_config: Optional[AzureOpenAIAgentConfig] = None
    ):
        """
        :param agent_name: Unique name or identifier for the agent.
        :param description: A brief explanation of the agent's capabilities.
        :param model_name: The AzureOpenAI model name (e.g., "gpt-3.5-turbo").
        :param config: Optional config dict (unused by default).
        :param tool_registry: Optional ToolRegistry to enable tool calling.
        :param agent_config: Optional configuration for the agent.
        """
        super().__init__(
            agent_name=agent_name,
            agent_type="AzureOpenAIAgent",
            description=description,
            config=config,
            tool_registry=tool_registry
        )
        self.agent_config = agent_config or AzureOpenAIAgentConfig()
        self.system_prompt = self.agent_config.system_prompt
        self.model_name = self.agent_config.model_name

    def setup(self) -> None:
        """
        Set the AzureOpenAI API key from the environment.
        You could also handle other setup tasks here
        (e.g., model selection logic).
        """
        api_key = self.agent_config.api_key if self.agent_config.api_key else os.environ.get("AZURE_OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "AZURE_OPENAI_API_KEY is not found. Either set it in the environment or pass it in the agent config."
            )
        api_base = self.agent_config.api_base if self.agent_config.api_base else os.environ.get("AZURE_OPENAI_ENDPOINT")
        if not api_base:
            raise EnvironmentError(
                "AZURE_OPENAI_ENDPOINT is not found. Either set it in the environment or pass it in the agent config."
            )
        api_version = self.agent_config.api_version if self.agent_config.api_version else os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

        params = {
            "api_key": api_key,
            "azure_endpoint": api_base,
            "api_version": api_version
        }
        print(f"Setting up AzureOpenAI with params: {params}")
        if self.agent_config.organization:  
            params["organization"] = self.agent_config.organization
        self.client = AzureOpenAI(
            **params
        )

    def handle_message(self, message: str, **kwargs) -> str:
        """
        Calls AzureOpenAI ChatCompletion to handle the user's message.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message},
                ]
            )
            print(f"Response: {response}")
            return response.choices[0].message.content
        except Exception as e:
            return f"[AzureOpenAIAgent error: {str(e)}]"

    def handle_message_stream(self, message: str, **kwargs):
        """
        Calls AzureOpenAI ChatCompletion to handle the user's message with streaming support.
        """
        # Starting streaming response from AzureOpenAIAgent
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
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    yield content
        except Exception as e:
            error_message = f"[AzureOpenAIAgent error: {str(e)}]"
            print(error_message)
            yield error_message
