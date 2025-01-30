"""
OpenAIAgent for Moya.

An Agent that uses OpenAI's ChatCompletion or Completion API
to generate responses, pulling API key from the environment.
"""

# Todo: Implement more configuration freedom for the agent.

import os
from openai import OpenAI

from typing import Any, Dict, Optional
from moya.agents.base_agent import Agent


class OpenAIAgent(Agent):
    """
    A simple OpenAI-based agent that uses the ChatCompletion API.
    """

    def __init__(
        self,
        agent_name: str,
        description: str,
        model_name: str = "gpt-4o",
        config: Optional[Dict[str, Any]] = None,
        tool_registry: Optional[Any] = None,
        system_prompt: str = "You are a helpful AI assistant."
    ):
        """
        :param agent_name: Unique name or identifier for the agent.
        :param description: A brief explanation of the agent's capabilities.
        :param model_name: The OpenAI model name (e.g., "gpt-3.5-turbo").
        :param config: Optional config dict (unused by default).
        :param tool_registry: Optional ToolRegistry to enable tool calling.
        :param system_prompt: Default system prompt for context.
        """
        super().__init__(
            agent_name=agent_name,
            agent_type="OpenAIAgent",
            description=description,
            config=config,
            tool_registry=tool_registry
        )
        self.model_name = model_name
        self.system_prompt = system_prompt

    def setup(self) -> None:
        """
        Set the OpenAI API key from the environment.
        You could also handle other setup tasks here
        (e.g., model selection logic).
        """
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY not found in environment. Please set it before using OpenAIAgent."
            )
        self.client = OpenAI(api_key=api_key)

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
