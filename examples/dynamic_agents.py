"""
Example demonstrating dynamic agent creation and registration during runtime.
"""

from typing import Dict, Any
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.classifiers.llm_classifier import LLMClassifier
from moya.orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator
from moya.registry.agent_registry import AgentRegistry
from moya.tools.memory_tool import MemoryTool
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool_registry import ToolRegistry


def setup_memory_components():
    """Set up shared memory components."""
    memory_repo = InMemoryRepository()
    memory_tool = MemoryTool(memory_repository=memory_repo)
    tool_registry = ToolRegistry()
    tool_registry.register_tool(memory_tool)
    return tool_registry


def create_initial_classifier() -> OpenAIAgent:
    """Create the initial classifier with basic routing."""
    classifier_config = OpenAIAgentConfig(
        system_prompt="""You are a classifier that routes messages to appropriate agents.
        Given a user message and list of available specialized agents, select the most appropriate agent.
        Currently available agents:
        - english_agent: Default agent that responds in English
        
        If the message starts with 'Create new agent', return 'CREATOR' as this requires agent creation.
        Otherwise, return the most appropriate agent name from the available agents list.
        Return only the agent name, nothing else.""",
        model_name="gpt-4o",
        temperature=0.7
    )

    agent = OpenAIAgent(
        agent_name="classifier",
        description="Dynamic message router",
        agent_config=classifier_config
    )
    agent.setup()
    return agent


def update_classifier_prompt(classifier: OpenAIAgent, agents: Dict[str, Dict[str, Any]]):
    """Update classifier's system prompt with current agent list."""
    base_prompt = """You are a classifier that routes messages to appropriate agents.
    Given a user message and list of available specialized agents, select the most appropriate agent.
    Currently available agents:"""

    # Add each agent's details to the prompt
    for name, details in agents.items():
        base_prompt += f"\n- {name}: {details['description']}"

    base_prompt += "\n\nIf the message starts with 'Create new agent', return 'CREATOR' as this requires agent creation."
    base_prompt += "\nOtherwise, return the most appropriate agent name from the available agents list."
    base_prompt += "\nReturn only the agent name, nothing else."

    classifier.system_prompt = base_prompt


def create_new_agent(tool_registry, agents_info: Dict[str, Dict[str, Any]]) -> OpenAIAgent:
    """Create a new agent based on user input."""
    print("\nCreating new agent...")
    agent_name = input("Enter agent name: ").strip()
    description = input("Enter agent description: ").strip()
    system_prompt = input("Enter system prompt: ").strip()

    agent_config = OpenAIAgentConfig(
        system_prompt=system_prompt
    )

    agent = OpenAIAgent(
        agent_name=agent_name,
        description=description,
        agent_config=agent_config,
        tool_registry=tool_registry
    )
    agent.setup()

    # Store agent info for classifier updates
    agents_info[agent_name] = {
        "description": description,
        "system_prompt": system_prompt
    }

    return agent


def format_conversation_context(messages):
    """Format conversation history for context."""
    context = "\nPrevious conversation:\n"
    for msg in messages:
        sender = "User" if msg.sender == "user" else "Assistant"
        context += f"{sender}: {msg.content}\n"
    return context


def main():
    # Set up initial components
    tool_registry = setup_memory_components()
    registry = AgentRegistry()

    # Create and register initial English agent
    english_config = OpenAIAgentConfig(
        system_prompt="You are a helpful assistant that responds in English."
    )

    english_agent = OpenAIAgent(
        agent_name="english_agent",
        description="Default English language agent",
        agent_config=english_config,
        tool_registry=tool_registry
    )
    english_agent.setup()
    registry.register_agent(english_agent)

    # Store agent information for classifier updates
    agents_info = {
        "english_agent": {
            "description": "Default English language agent",
            "system_prompt": "You are a helpful assistant that responds in English."
        }
    }

    # Set up classifier and orchestrator
    classifier_agent = create_initial_classifier()
    classifier = LLMClassifier(classifier_agent, default_agent="english_agent")
    orchestrator = MultiAgentOrchestrator(
        agent_registry=registry,
        classifier=classifier
    )

    # Interactive loop
    thread_id = "dynamic_agents_chat"
    print("Starting dynamic multi-agent chat (type 'exit' to quit)")
    print("Type 'Create new agent' to add a new agent to the system")
    print("-" * 50)

    def stream_callback(chunk):
        print(chunk, end="", flush=True)

    while True:
        user_message = input("\nYou: ").strip()

        if user_message.lower() == 'exit':
            print("\nGoodbye!")
            break

        # Check if this is a request to create a new agent
        if user_message.lower().startswith('create new agent'):
            new_agent = create_new_agent(tool_registry, agents_info)
            registry.register_agent(new_agent)
            update_classifier_prompt(classifier_agent, agents_info)
            print(f"\nAgent '{new_agent.agent_name}' created and registered!")
            continue

        # Get available agents
        agents = registry.list_agents()
        if not agents:
            print("\nNo agents available!")
            continue

        # Get the last used agent or default to the first one
        last_agent = registry.get_agent(agents[0])

        # Store the user message first
        if last_agent.tool_registry:
            try:
                last_agent.call_tool(
                    tool_name="MemoryTool",
                    method_name="store_message",
                    thread_id=thread_id,
                    sender="user",
                    content=user_message
                )
            except Exception as e:
                print(f"Error storing user message: {e}")

        # Get conversation context
        previous_messages = last_agent.get_last_n_messages(thread_id, n=5)

        # Add context to the user's message if there are previous messages
        if previous_messages:
            context = format_conversation_context(previous_messages)
            enhanced_input = f"{context}\nCurrent user message: {user_message}"
        else:
            enhanced_input = user_message

        # Handle normal messages with orchestrator
        print("\nAssistant: ", end="", flush=True)
        response = orchestrator.orchestrate(
            thread_id=thread_id,
            user_message=enhanced_input,
            stream_callback=stream_callback
        )
        print()


if __name__ == "__main__":
    main()
