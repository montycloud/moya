from typing import List, Optional

from moya.agents.agent_info import AgentInfo
from moya.classifiers.base_classifier import BaseClassifier
from moya.agents.base_agent import Agent


class LLMClassifier(BaseClassifier):
    """LLM-based classifier for agent selection."""

    def __init__(self, llm_agent: Agent, default_agent: str):
        """
        Initialize with an LLM agent for classification.
        
        :param llm_agent: An agent that will be used for classification
        :param default_agent: The default agent to use if no specialized match is found
        """
        self.llm_agent = llm_agent
        self.default_agent = default_agent

    def classify(self, message: str, thread_id: Optional[str] = None, available_agents: List[AgentInfo] = None) -> str:
        """
        Use LLM to classify message and select appropriate agent.
        
        :param message: The user message to classify
        :param thread_id: Optional thread ID for context
        :param available_agents: List of available agent names to choose from
        :return: Selected agent name
        """
        if not available_agents:
            return None

        # Construct prompt for the LLM
        prompt = f"""Given the following user message and list of available specialized agents, 
        select the most appropriate agent to handle the request. Return only the agent id.
        
        Available agents: {', '.join([f"'{agent.name}: {agent.description}'" for agent in available_agents])}
        
        User message: {message}
        """

        # Get classification from LLM
        response = self.llm_agent.handle_message(prompt, thread_id=thread_id)

        # Clean up response and validate
        selected_agent = response.strip()

        if selected_agent not in [agent.name for agent in available_agents]:
            return self.default_agent

        return selected_agent
