"""
BedrockAgent for Moya.

An Agent that uses AWS Bedrock API to generate responses,
pulling AWS credentials from environment or AWS configuration.
"""

import json
import boto3
from typing import Any, Dict, Optional
from moya.agents.base_agent import Agent, AgentConfig
from dataclasses import dataclass


@dataclass
class BedrockAgentConfig(AgentConfig):
    model_id: str = "anthropic.claude-v2"
    region: str = "us-east-1"
    max_tokens_to_sample: int = 2000
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 250


class BedrockAgent(Agent):
    """
    A simple AWS Bedrock-based agent that uses the Bedrock API.
    """

    def __init__(
        self,
        agent_name: str,
        description: str,
        config: Optional[Dict[str, Any]] = None,
        tool_registry: Optional[Any] = None,
        agent_config: Optional[BedrockAgentConfig] = None
    ):
        """
        :param agent_name: Unique name or identifier for the agent.
        :param description: A brief explanation of the agent's capabilities.
        :param model_id: The Bedrock model ID (e.g., "anthropic.claude-v2").
        :param config: Optional config dict (can include AWS region).
        :param tool_registry: Optional ToolRegistry to enable tool calling.
        :param system_prompt: Default system prompt for context.
        """
        super().__init__(
            agent_name=agent_name,
            agent_type="BedrockAgent",
            description=description,
            config=config,
            tool_registry=tool_registry
        )
        self.agent_config = agent_config or BedrockAgentConfig()
        self.system_prompt = self.agent_config.system_prompt
        self.model_id = self.agent_config.model_id
        self.region = self.agent_config.region

    def setup(self) -> None:
        """
        Initialize the Bedrock client using boto3.
        AWS credentials should be configured via environment variables
        or AWS configuration files.
        """
        try:
            self.client = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.region
            )
        except Exception as e:
            raise EnvironmentError(
                f"Failed to initialize Bedrock client: {str(e)}"
            )

    def handle_message(self, message: str, **kwargs) -> str:
        """
        Calls AWS Bedrock to handle the user's message.
        """
        try:
            # Construct the prompt based on the model
            if "anthropic" in self.model_id:
                prompt = f"\n\nHuman: {message}\n\nAssistant:"
                body = {
                    "prompt": self.system_prompt + prompt,
                    "max_tokens_to_sample": self.agent_config.max_tokens_to_sample,
                    "temperature": self.agent_config.temperature
                }
            else:
                # Handle other model types here
                body = {
                    "inputText": message,
                    "textGenerationConfig": {
                        "maxTokenCount": self.agent_config.max_tokens_to_sample,
                        "temperature": self.agent_config.temperature
                    }
                }

            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )

            response_body = json.loads(response['body'].read())
            return response_body.get('completion', response_body.get('outputText', ''))

        except Exception as e:
            return f"[BedrockAgent error: {str(e)}]"

    def handle_message_stream(self, message: str, **kwargs):
        """
        Calls AWS Bedrock to handle the user's message with streaming support.
        """
        try:
            if "anthropic" in self.model_id:
                prompt = f"\n\nHuman: {message}\n\nAssistant:"
                body = {
                    "prompt": self.system_prompt + prompt,
                    "max_tokens_to_sample": self.agent_config.max_tokens_to_sample,
                    "temperature": self.agent_config.temperature
                }
            else:
                body = {
                    "inputText": message,
                    "textGenerationConfig": {
                        "maxTokenCount": self.agent_config.max_tokens_to_sample,
                        "temperature": self.agent_config.temperature
                    }
                }

            response = self.client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(body)
            )

            for event in response['body']:
                chunk = json.loads(event['chunk']['bytes'])
                if 'completion' in chunk:
                    yield chunk['completion']
                elif 'outputText' in chunk:
                    yield chunk['outputText']

        except Exception as e:
            error_message = f"[BedrockAgent error: {str(e)}]"
            print(error_message)
            yield error_message
