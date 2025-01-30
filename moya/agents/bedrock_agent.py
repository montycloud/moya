"""
BedrockAgent for Moya.

An Agent that uses AWS Bedrock API to generate responses,
pulling AWS credentials from environment or AWS configuration.
"""

# Todo: Implement more configuration freedom for the agent.

import json
import boto3
from typing import Any, Dict, Optional
from moya.agents.base_agent import Agent


class BedrockAgent(Agent):
    """
    A simple AWS Bedrock-based agent that uses the Bedrock API.
    """

    def __init__(
        self,
        agent_name: str,
        description: str,
        model_id: str = "anthropic.claude-v2",
        config: Optional[Dict[str, Any]] = None,
        tool_registry: Optional[Any] = None,
        system_prompt: str = "You are a helpful AI assistant."
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
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.client = None

    def setup(self) -> None:
        """
        Initialize the Bedrock client using boto3.
        AWS credentials should be configured via environment variables
        or AWS configuration files.
        """
        try:
            self.client = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.config.get('region', 'us-east-1')
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
                    "max_tokens_to_sample": 2000,
                    "temperature": 0.7
                }
            else:
                # Handle other model types here
                body = {
                    "inputText": message,
                    "textGenerationConfig": {
                        "maxTokenCount": 2000,
                        "temperature": 0.7
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
                    "max_tokens_to_sample": 2000,
                    "temperature": 0.7
                }
            else:
                body = {
                    "inputText": message,
                    "textGenerationConfig": {
                        "maxTokenCount": 2000,
                        "temperature": 0.7
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
