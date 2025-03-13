"""
CrewAIAgent for Moya.

An Agent that uses a Crew to generate responses using CrewAI.
"""
import os
from dataclasses import dataclass

from crewai import Agent as CrewAgent, LLM as CrewLLM, Task as CrewTask, Crew
from typing import Any, Dict, Optional
from moya.agents.base_agent import Agent, AgentConfig

os.environ["OTEL_SDK_DISABLED"] = "true"


@dataclass
class CrewAIAgentConfig(AgentConfig):
    api_key: str = os.getenv("OPENAI_API_KEY"),
    model_name: str = "gpt-4o"


class CrewAIAgent(Agent):
    """
    A simple CrewAI-based agent.
    """

    def __init__(
            self,
            agent_name: str,
            description: str,
            config: Optional[Dict[str, Any]] = None,
            tool_registry: Optional[Any] = None,
            agent_config: Optional[CrewAIAgentConfig] = None
    ):
        """
        :param agent_name: Unique name or identifier for the agent.
        :param description: A brief explanation of the agent's capabilities.
        :param config: Optional agent configuration (unused by default).
        :param tool_registry: Optional ToolRegistry to enable tool calling.
        :param system_prompt: Default system prompt for context.
        :param agent_config: Optional configuration for the CrewAIAgent.
        """
        super().__init__(
            agent_name=agent_name,
            agent_type="CrewAIAgent",
            description=description,
            config=config,
            tool_registry=tool_registry
        )
        self.agent_config = agent_config or CrewAIAgentConfig()
        self.system_prompt = self.agent_config.system_prompt
        self.client = None

    def setup(self) -> None:
        """
        Initialize the CrewAI agent with the provided configuration.
        """
        try:
            self.client = CrewAgent(
                role="assistant",
                goal=self.system_prompt,
                backstory=self.description,
                verbose=False,
                llm=CrewLLM(
                    model=self.agent_config.model_name,
                    api_key=self.agent_config.api_key,
                ))
        except Exception as e:
            raise EnvironmentError(
                f"Failed to initialize Crew Agent: {str(e)}"
            )

    def handle_message(self, message: str, **kwargs) -> str:
        """
        Calls the CrewAI agent to handle the user's message.
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
        Calls the CrewAI agent to handle the user's message.
        CrewAI does not support streaming responses, so this method is the same as handle_message.
        """
        try:
            task = CrewTask(
                description=message,
                expected_output="",
                agent=self.client,
            )
            crew = Crew(agents=[self.client], tasks=[task])
            response = crew.kickoff().raw
            yield response

        except Exception as e:
            error_message = f"[CrewAIAgent error: {str(e)}]"
            print(error_message)
            yield error_message
