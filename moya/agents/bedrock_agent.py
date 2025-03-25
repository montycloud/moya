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



class BedrockAgent(Agent):
    """
    A simple AWS Bedrock-based agent that uses the Bedrock API.
    """

    def __init__(
        self,
        config: BedrockAgentConfig
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
            config=config
        )
        self.config = config
        self.system_prompt = config.system_prompt
        self.model_id = config.model_id
        self.region = config.region

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
            # Construct the request based on the model
            if "anthropic.claude-3" in self.model_id:
                # Use Messages API format for Claude 3 models
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.config.llm_config.get('max_tokens', 1000),
                    "temperature": self.config.llm_config.get('temperature', 0.7),
                    "messages": [
                        {
                            "role": "assistant",
                            "content": self.system_prompt
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ]
                }
            elif "anthropic" in self.model_id:
                # Legacy format for older Claude models
                prompt = f"\n\nHuman: {message}\n\nAssistant:"
                body = {
                    "prompt": self.system_prompt + prompt,
                    "max_tokens_to_sample": self.config.llm_config.get('max_tokens', 1000),
                    "temperature": self.config.llm_config.get('temperature', 0.7)
                }
            else:
                # Handle other model types here
                body = {
                    "inputText": message
                }
                
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            response_body = json.loads(response['body'].read())
            
            # Handle different response formats
            if "anthropic.claude-3" in self.model_id:
                return response_body.get('content', [{}])[0].get('text', '')
            else:
                return response_body.get('completion', response_body.get('outputText', ''))
                
        except Exception as e:
            return f"[BedrockAgent error: {str(e)}]"
            
    def handle_message_stream(self, message: str, **kwargs):
        """
        Calls AWS Bedrock to handle the user's message with streaming support.
        """
        try:
            if "anthropic.claude-3" in self.model_id:
                # Use Messages API format for Claude 3 models
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.config.llm_config.get('max_tokens', 1000),
                    "temperature": self.config.llm_config.get('temperature', 0.7),
                    "messages": [
                        {
                            "role": "assistant",
                            "content": self.system_prompt
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ]
                }
            elif "anthropic" in self.model_id:
                # Legacy format for older Claude models
                prompt = f"\n\nHuman: {message}\n\nAssistant:"
                body = {
                    "prompt": self.system_prompt + prompt,
                    "max_tokens_to_sample": self.config.llm_config.get('max_tokens', 1000),
                    "temperature": self.config.llm_config.get('temperature', 0.7)
                }
            else:
                body = {
                    "inputText": message
                }
                
            response = self.client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            for event in response['body']:
                chunk = json.loads(event['chunk']['bytes'])
                if "anthropic.claude-3" in self.model_id:
                    if 'delta' in chunk and 'text' in chunk['delta']:
                        yield chunk['delta']['text']
                elif 'completion' in chunk:
                    yield chunk['completion']
                elif 'outputText' in chunk:
                    yield chunk['outputText']
                    
        except Exception as e:
            error_message = f"[BedrockAgent error: {str(e)}]"
            print(error_message)
            yield error_message
