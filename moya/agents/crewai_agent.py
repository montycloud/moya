"""
CrewAIAgent for Moya.

Wraps a CrewAI Crew as a single MOYA agent. Because CrewAI does not expose
a streaming API the handle_message_stream() implementation yields the complete
response as a single chunk, which is valid under MOYA's streaming contract.
"""

import os
from dataclasses import dataclass
from typing import Iterator, Optional

from moya.agents.agent import Agent, AgentConfig

os.environ["OTEL_SDK_DISABLED"] = "true"


@dataclass
class CrewAIAgentConfig(AgentConfig):
    api_key: Optional[str] = None
    model_name: str = "gpt-4o"

    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.getenv("OPENAI_API_KEY")
        super().__post_init__()


class CrewAIAgent(Agent):
    """
    CrewAI-backed agent. Delegates every message to a single-task Crew.
    """

    def __init__(self, config: CrewAIAgentConfig):
        super().__init__(config=config)
        self.agent_config = config
        self._crew_agent = None

    def setup(self) -> None:
        """Initialise the CrewAI agent and verify the LLM connection."""
        try:
            from crewai import Agent as CrewAgent, LLM as CrewLLM

            self._crew_agent = CrewAgent(
                role="assistant",
                goal=self.system_prompt,
                backstory=self.description,
                verbose=False,
                llm=CrewLLM(
                    model=self.agent_config.model_name,
                    api_key=self.agent_config.api_key,
                ),
            )
        except Exception as e:
            raise EnvironmentError(f"Failed to initialise CrewAI agent: {e}") from e

    def handle_message(self, message: str, **kwargs) -> str:
        thread_id = kwargs.get("thread_id", "default")
        if self._crew_agent is None:
            self.setup()
        try:
            from crewai import Task, Crew

            task = Task(description=message, expected_output="", agent=self._crew_agent)
            crew = Crew(agents=[self._crew_agent], tasks=[task])
            result = crew.kickoff().raw
            self._remember(thread_id, message, result)
            return result
        except Exception as e:
            return f"[CrewAIAgent error: {e}]"

    def handle_message_stream(self, message: str, **kwargs) -> Iterator[str]:
        """CrewAI has no streaming API — yields the full response as one chunk."""
        yield self.handle_message(message, **kwargs)
