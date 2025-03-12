"""
ReActOrchestrator for Moya.

An implementation of an orchestrator that follows the ReAct framework:
- Thought: Explain reasoning towards solving the task and the assistant to assign the task to.
- Action: Provide the question or task to assign to the assistant.
- Observation: Automatically generated based on the responses of the assistants.
"""

from typing import Optional

from moya.agents.base_agent import Agent
from moya.orchestrators.base_orchestrator import BaseOrchestrator
from moya.registry.agent_registry import AgentRegistry
from moya.classifiers.base_classifier import BaseClassifier
import os


class ReActOrchestrator(BaseOrchestrator):
    """
    An orchestrator that follows the ReAct framework to handle user messages.
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        classifier: BaseClassifier,
        llm_agent: Agent,
        default_agent_name: Optional[str] = None,
        config: Optional[dict] = {},
        verbose=False
    ):
        """
        :param agent_registry: The AgentRegistry to retrieve agents from.
        :param classifier: The classifier to use for agent selection.
        :param llm_agent: The LLM agent to generate responses.
        :param default_agent_name: The default agent to fall back on if no specialized match is found.
        :param config: Optional dictionary for orchestrator configuration.
        """
        super().__init__(agent_registry=agent_registry, config=config)
        self.classifier = classifier
        self.default_agent_name = default_agent_name

        self.verbose = verbose
        self.llm_agent = llm_agent

    def orchestrate(self, thread_id: str, user_message: str, stream_callback=None, **kwargs) -> str:
        """
        The main orchestration method following the ReAct framework.
        """
        self.max_steps = self.config.get("max_steps", 5)

        observation = user_message

        while not self._is_final_answer(observation, user_message) and self.max_steps > 0:
            self.log(message=f"Step {self.config.get('max_steps', 5) - self.max_steps}")
            self.max_steps -= 1
            thought = self._generate_thought(observation, user_message)
            action = self._determine_action(thought)
            observation = self._execute_action(action)
            self.log(message="new_line")

        self.log(message="new_line\n=== Final Answer ===")
        return self._generate_final_answer(observation)

    def _call_llm(self, system_prompt: str, message: str) -> str:
        """
        Call the LLM to generate a response.
        """
        self.llm_agent.system_prompt = system_prompt
        response = self.llm_agent.handle_message(message)
        # print(response)
        return response

    def _determine_action(self, thought: str) -> str:
        """
        Determine the next action based on the current thought.
        """
        available_agents = self.agent_registry.list_agents()
        agent_name = self.classifier.classify(
            thought, available_agents=available_agents)
        if not agent_name:
            agent_name = self.default_agent_name
        task = self._generate_task(thought, agent_name)
        task = task.replace("task: ", "").replace("Task: ", "").strip()
        action = f"  agent: {agent_name}\n  task: {task}"

        self.log(message=f"{thought}\n{action}")
        return action

    def _generate_task(self, thought: str, agent_name: str) -> str:
        """
        Generate the task based on the thought.
        """
        system_prompt = """Use the agent details along with the observation to generate a descriptive task. NOTE THAT YOU SHOULD ONLY TELL THE AGENT WHAT TO DO, NOT HOW TO DO IT."""

        agent_description = self.agent_registry.get_agent(agent_name).description
        user_message = f"Thought: {thought}. Agent Description: {agent_description}"
        return self._call_llm(system_prompt, user_message)

    def _execute_action(self, action: str) -> str:
        """
        Execute the action and return the observation.
        """
        agent_name, task_description = self._parse_action(action)

        if task_description == "final_answer":
            return task_description

        agent = self.agent_registry.get_agent(agent_name)
        response = agent.handle_message(task_description)

        return self._generate_observation(response)

    def _parse_action(self, action: str) -> tuple:
        """
        Parse the action string to extract the agent name and task description.
        """
        lines = action.split('\n')
        agent_name = lines[0].split(': ')[1]
        task_description = lines[1].split(': ')[1]
        return agent_name, task_description

    def _generate_thought(self, observation: str, user_query: str) -> str:
        """
        Generate the next thought based on the observation.
        """
        system_prompt = """You are an Orchestrator that follows the ReAct framework.
        You will be provided with an observation for the user query.
        Based on the observation, generate a thought to determine the next action.
        You can only think in English; for other languages, first translate the observation to English, perform the thought process, and then use the specific language agent."""

        user_message = f"Observation: {observation}, User Query: {user_query}"
        return self._call_llm(system_prompt, user_message)

    def _is_final_answer(self, observation: str, user_query: str) -> bool:
        """
        Determine if the observation contains the final answer.
        """
        system_prompt = """You will be provided with an observation. If the observation seems to contain the answer to the user query, return 'final_answer', else return null."""

        if observation == user_query:
            return False

        user_message = f"Observation: {observation}, User Query: {user_query}"
        response = self._call_llm(system_prompt, user_message)
        self.log(message=f"Is final answer: {'yes' if response == 'final_answer' else 'no'}")
        return response == "final_answer"

    def _generate_observation(self, response: str) -> str:
        """
        Generate the observation based on the agent's response.
        """
        observation = f"Observation: {response}"
        temp_obs = observation.replace("\n", " ")
        if len(observation) > 100:
            self.log(message=temp_obs[:50] + "..." + temp_obs[-50:])
        else:
            self.log(message=temp_obs)
        return observation

    def _generate_final_answer(self, response: str) -> str:
        """
        Generate the final answer based on the agent's response.
        """
        return response.replace("Observation: ", "")

    def log(self, message: str):
        """
        Log the iteration message.
        """
        if self.verbose:
            messages = message.split('\n')
            for message in messages:
                cleaned_message = message.replace("\n", "").strip()
                if cleaned_message == 'new_line':
                    print("\n")
                elif cleaned_message:
                    print("    [Orchestrator]: ", message)
