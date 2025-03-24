"""
TeamOrchestrator for Moya.

TeamOrchestrator is a reference implementation of an orchestrator that:
- Selects a team of agents using a classifier, based on the context of the user message,
- Calls handle_message on each agent in the team parllelly in a multi-threaded manner,
- Uses the combined response from the team to enhance the context.
- Iterates and forms a new team of agents using the classifier based on enhanced message,
     until answer is reached or a maximum number of steps is reached.
- Returns the final response.
"""
import os
from typing import Optional, List
from moya.orchestrators.base_orchestrator import BaseOrchestrator
from moya.registry.agent_registry import AgentRegistry
from moya.classifiers.base_classifier import BaseClassifier
from moya.agents.base_agent import Agent
from moya.tools.ephemeral_memory import EphemeralMemory
import threading


class TeamOrchestrator(BaseOrchestrator):
    """
    An orchestrator that uses a classifier to select a team of agents to handle the user message.
    """
    
    def __init__(
        self,
        agent_registry: AgentRegistry,
        classifier: BaseClassifier,
        default_agent_name: Optional[str] = None,
        config: Optional[dict] = None
    ):
        """
        :param agent_registry: The AgentRegistry to retrieve agents from
        :param classifier: The classifier to use for agent selection
        :param default_agent_name: Fallback agent if classification fails
        :param config: Optional configuration dictionary
        """
        super().__init__(agent_registry=agent_registry, config=config)
        self.classifier = classifier
        self.default_agent_name = default_agent_name

    def orchestrate(self, thread_id: str, user_message: str, stream_callback=None, **kwargs) -> str:
        """
        Orchestrate the message handling using a team of agents selected by the classifier.

        :param thread_id: The conversation thread ID
        :param user_message: The message from the user
        :param stream_callback: Optional callback for streaming responses
        :param kwargs: Additional context
        :return: The response from the team of agents
        """
        
        # Store user message
        EphemeralMemory.store_message(thread_id=thread_id, sender="user", content=user_message)
    
        self.max_steps = self.config.get("max_steps", 10)

        observation = [user_message]

        available_agents = self.agent_registry.list_agents()

        if not available_agents or len(available_agents) == 0:
            return "[No agents available to handle message.]"
        
        for step in range(self.max_steps):
            print(f"Step {step}")
            team = self.classifier.classify( message=observation,
                thread_id=thread_id,
                available_agents=available_agents,
            )
            
            if not team or len(team) == 0:
                break
            print(f"Team: {team}\n")
            if "END_CONVERSATION" in team:
                break
            responses = []
            threads = []
            
            for agent_name in team:
                agent = self.agent_registry.get_agent(agent_name)

                thread = threading.Thread(
                    target=self._call_agent, args=(agent, observation[-1], responses)
                )
                threads.append(thread)
                thread.start()
                thread.join()
            
            observation.append(" ".join(responses))
            print(f"Observation: {observation[-1]}\n")
        EphemeralMemory.store_message(thread_id=thread_id, sender="system", content=observation[-1])

        return "\n".join(observation)

    def _call_agent(self, agent: Agent, message: str, responses: List[str]):
        """
        Call the agent to generate a response.
        """
        response = agent.handle_message(message)
        responses.append(f"{agent.agent_name}: {response}" if response else "")

