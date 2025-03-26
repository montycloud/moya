"""
LambdaAgent for Moya.

An Agent that invokes an AWS Lambda function to generate responses.
"""
import json
import boto3
from dataclasses import dataclass
from typing import Optional, Iterator
from moya.agents.base_agent import Agent, AgentConfig


@dataclass
class LambdaAgentConfig(AgentConfig):
    """Configuration for LambdaAgent, separate from AgentConfig to avoid inheritance issues"""
    function_name: str = None
    aws_region: str = "us-east-1"
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None


class LambdaAgent(Agent):
    """
    An agent that invokes an AWS Lambda function to process requests.
    """

    def __init__(
        self,
        config=LambdaAgentConfig
    ):
        """
        Initialize a LambdaAgent.
        
        :param agent_name: Unique name for the agent
        :param description: Description of the agent's capabilities
        :param config: Optional configuration dictionary
        :param tool_registry: Optional ToolRegistry for tool support
        :param agent_config: Optional configuration for the LambdaAgent
        """
        super().__init__(config=config)

        if not config.function_name:
            raise ValueError("LambdaAgent function name is required.")
                   
        self.function_name = config.function_name
        self.system_prompt = config.system_prompt

        # Initialize AWS Lambda client
        self.lambda_client = boto3.client(
            "lambda"
        )

    def handle_message(self, message: str, **kwargs) -> str:
        """
        Invoke the Lambda function with the given message and get the response.
        
        :param message: The message to process
        :param kwargs: Additional parameters to pass to the Lambda function
        :return: Response from the Lambda function
        """
        try:
            payload = {
                "message": message,
                "thread_id": kwargs.get("thread_id"),
                **kwargs
            }
            
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType="RequestResponse",
                Payload=bytes(str(payload), encoding="utf-8")
            )
            
            response_payload = response["Payload"].read().decode("utf-8")
            return response_payload
            
        except Exception as e:
            return f"[LambdaAgent error: {str(e)}]"

    def handle_message_stream(self, message: str, **kwargs) -> Iterator[str]:
        """
        Invoke the Lambda function and stream the response.
        """
        try:
            payload = {
                "message": message,
                "thread_id": kwargs.get("thread_id"),
                **kwargs
            }
            
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(payload)
            )
            
            response_payload = response["Payload"].read().decode("utf-8")

            # Lambda function will not keep sending data in chunks
            # The response is split by newline character for demonstration purposes
            for chunk in response_payload.split("\n"):
                yield chunk.strip()
                            
        except Exception as e:
            error_message = f"[LambdaAgent error: {str(e)}]"
            print(error_message)
            yield error_message

    def __del__(self):
        """Cleanup resources if necessary when the agent is destroyed."""
        pass