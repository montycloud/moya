"""
AzureOpenAIAgent for Moya.

An Agent that uses OpenAI's ChatCompletion or Completion API
to generate responses, pulling API key from the environment.
"""


import os
from openai import AzureOpenAI
from dataclasses import dataclass

from typing import Any, Dict, List, Optional
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig


@dataclass
class AzureOpenAIAgentConfig(OpenAIAgentConfig):
    """
    Configuration data for an AzureOpenAIAgent.
    """
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    organization: Optional[str] = None


class AzureOpenAIAgent(OpenAIAgent):
    """
    A simple AzureOpenAI-based agent that uses the ChatCompletion API.
    """

    def __init__(self, config: AzureOpenAIAgentConfig):
        """
        Initialize the AzureOpenAIAgent.

        :param config: Configuration for the agent.
        """
        super().__init__(config=config)
        if not config.api_base:
            raise ValueError("Azure OpenAI API base is required for AzureOpenAIAgent.")
        api_base = config.api_base 

        if not config.api_version:
            raise ValueError("Azure OpenAI API version is required for AzureOpenAIAgent.")
        
        if not config.api_version:
            raise ValueError("Azure OpenAI API version is required for AzureOpenAIAgent.")

        api_version = config.api_version 

        self.client = AzureOpenAI(api_key=config.api_key, 
                                  azure_endpoint=api_base, 
                                  api_version=api_version,
                                  organization=config.organization)
