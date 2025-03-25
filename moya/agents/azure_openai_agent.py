"""
AzureOpenAIAgent for Moya.

An Agent that uses OpenAI's ChatCompletion or Completion API
to generate responses, pulling API key from the environment.
"""


import os
from openai import AzureOpenAI
from dataclasses import dataclass
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

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
    use_azure_ad_token_provider: Optional[bool] = False


class AzureOpenAIAgent(OpenAIAgent):
    """
    A simple AzureOpenAI-based agent that uses the ChatCompletion API.
    """

    def __init__(self, config: AzureOpenAIAgentConfig):
        """
        Initialize the AzureOpenAIAgent.

        :param config: Configuration for the agent.
        """
        if config.use_azure_ad_token_provider:
            config.api_key = "Using Azure AD token provider"

        super().__init__(config=config)
        if not os.getenv("AZURE_API_ENDPOINT"):
            raise ValueError("Azure OpenAI API ENDPOINT environment variable for reading base is required for AzureOpenAIAgent.")
        config.api_base = os.getenv("AZURE_API_ENDPOINT")

        if not config.api_base:
            raise ValueError("Azure OpenAI API base is required for AzureOpenAIAgent.")
        api_base = config.api_base 

        if not config.api_version:
            raise ValueError("Azure OpenAI API version is required for AzureOpenAIAgent.")
        

        
        if config.use_azure_ad_token_provider:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
            )

            self.client = AzureOpenAI( 
                                  azure_endpoint=api_base, 
                                  api_version=config.api_version,
                                  azure_ad_token_provider=token_provider,
                                  organization=config.organization)
        else:
            self.client = AzureOpenAI(api_key=config.api_key,
                                  azure_endpoint=api_base,
                                  api_version=config.api_version,
                                  organization=config.organization)
        
