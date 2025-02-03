"""
BedrockAgent for Moya.

An Agent that uses AWS Bedrock API to generate responses,
pulling AWS credentials from environment or AWS configuration.
"""

# Todo: Implement more configuration freedom for the agent.

import json
import os
from crewai import Agent as CrewAgent, LLM as CrewLLM, Task as CrewTask, Crew
from typing import Any, Dict, Optional
from moya.agents.base_agent import Agent


class CrewAIAgent(Agent):
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
            agent_type="CrewAIAgent",
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
            self.client = CrewAgent(
                role="assistant",
                goal=self.system_prompt,
                backstory=self.description,
                verbose=False,
                llm=CrewLLM(
                    model=self.config.get("model", "gpt-4o"),
                    api_key=self.config.get("api_key", None),
                ))
        except Exception as e:
            raise EnvironmentError(
                f"Failed to initialize Crew Agent: {str(e)}"
            )

    def handle_message(self, message: str, **kwargs) -> str:
        """
        Calls AWS Bedrock to handle the user's message.
        """
        try:
            task = CrewTask(
                        description=message,
                        expected_output="",
                        agent=self.client,
                    )
            crew = Crew(agents=[self.client], tasks=[task])
            response = crew.kickoff().raw
            return response

        except Exception as e:
            return f"[BedrockAgent error: {str(e)}]"

    def handle_message_stream(self, message: str, **kwargs):
        """
        Calls AWS Bedrock to handle the user's message with streaming support.
        """
        try:
            # if "anthropic" in self.model_id:
            #     prompt=f"\n\nHuman: {message}\n\nAssistant:"
            #     body={
            #         "prompt": self.system_prompt + prompt,
            #         "max_tokens_to_sample": 2000,
            #         "temperature": 0.7
            #     }
            # else:
            #     body={
            #         "inputText": message,
            #         "textGenerationConfig": {
            #             "maxTokenCount": 2000,
            #             "temperature": 0.7
            #         }
            #     }

            # response=self.client.invoke_model_with_response_stream(
            #     modelId=self.model_id,
            #     body=json.dumps(body)
            # )

            # for event in response['body']:
            #     chunk=json.loads(event['chunk']['bytes'])
            #     if 'completion' in chunk:
            #         yield chunk['completion']
            #     elif 'outputText' in chunk:
            #         yield chunk['outputText']

            task = CrewTask( #wraps prompt into a task object
                        description=message,
                        expected_output="",
                        agent=self.client,
                    )
            crew = Crew(agents=[self.client], tasks=[task])
            response = crew.kickoff().raw
            # print(response)
            yield response

        except Exception as e:
            error_message=f"[BedrockAgent error: {str(e)}]"
            print(error_message)
            yield error_message
