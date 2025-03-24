from typing import List, Optional

from moya.agents.agent_info import AgentInfo
from moya.classifiers.base_classifier import BaseClassifier
from moya.agents.base_agent import Agent


class LLMTeamClassifier(BaseClassifier):
    """LLM-based classifier for agent selection."""

    def __init__(self, llm_agent: Agent, default_agent: Optional[str] = None):
        """
        Initialize with an LLM agent for classification.
        
        :param llm_agent: An agent that will be used for classification
        :param default_agent: The default agent to use if no specialized match is found
        """
        self.llm_agent = llm_agent
        self.default_agent = default_agent

    def classify(self, message: str, thread_id: Optional[str] = None, available_agents: List[AgentInfo] = None) -> List[str]:
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
        select the most appropriate teams of agents that can handle the request. Return only a comma separatef value of the agent names.

        Strictly follow these guidelines: 
        1. Choose agents based on their description, make sure only the agents that can meaningfully handle the user message.
        2. Exclude any agents that are not relevant to the user message.
        3. If no agent is suitable, return the default agent.
        4. Be very selective, do not consider scope that is not relevant to the user message.
        5. Do not select general purpose agents, only specialized agents to accomplish user's intent are allowed.
        6. Always keep the user's original intent in mind. Use the latest context and findings available in the conversation to make the decision.
        7. If you are not sure about any agent, do not include it in the list.
        8. If you feel that the original intent of the user has been fulfilled or if you detect you are unable to resolve it, you can return "END_CONVERSATION" to end the conversation.
        9. The agents you return will be invoked parallely in different threads, If you feel that there is a dependency between agents, try to include only the agent that can provide the most relevant information first. for example prioritize "check_agent" before "update_agent".  or "check_agent" before "report_agent".
        
        Available agents: {', '.join([f"'{agent.name}: {agent.description}'" for agent in available_agents])}
        
        User message: {message}

        Return the list of agent IDs as a comma separated value. Use "none" if no agent is suitable.
        example 1: "agent1, agent2, agent3"
        example 2: "agent1"
        """

        # Get classification from LLM
        response = self.llm_agent.handle_message(prompt, thread_id=thread_id)

        # Clean up response and validate
        agent_list = response.strip()
        
        selected_agents = agent_list.split(", ")

        valid_agents = [agent.name for agent in available_agents if agent.name in selected_agents]

        if not valid_agents or valid_agents == []:
            return [self.default_agent] if self.default_agent else []
        
        return valid_agents
