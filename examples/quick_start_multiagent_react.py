import os
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
# from moya.agents.remote_agent import RemoteAgent
from moya.classifiers.llm_classifier import LLMClassifier
from moya.orchestrators.react_orchestrator import ReActOrchestrator
from moya.registry.agent_registry import AgentRegistry
from moya.tools.memory_tool import MemoryTool
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool_registry import ToolRegistry


def setup_memory_components():
    """Set up memory components for the agents."""
    memory_repo = InMemoryRepository()
    memory_tool = MemoryTool(memory_repository=memory_repo)
    tool_registry = ToolRegistry()
    tool_registry.register_tool(memory_tool)
    return tool_registry


def create_food_agent(tool_registry) -> OpenAIAgent:
    """Create a food recommendation agent."""
    system_prompt = """You are a great foodie who has tried every dish in your city.
    You should be able to recommend the best dishes based on the user's preferences.
    Give detailed descriptions and provide additional information about the dishes.
    You should not provide any other information except about food."""

    agent = OpenAIAgent(
        agent_name="food_agent",
        agent_config=OpenAIAgentConfig(system_prompt=system_prompt),
        description="Food recommendation specialist that provides detailed descriptions of dishes",
        tool_registry=tool_registry
    )
    agent.setup()
    return agent


def create_attractions_agent(tool_registry) -> OpenAIAgent:
    """Create a local attractions agent."""
    system_prompt = """You are a local guide who knows all the best attractions in your city.
    Recommend the best places to visit based on the user's preferences.
    Provide detailed information and tips about the attractions.
    You should not provide any other information except about attractions."""

    agent = OpenAIAgent(
        agent_name="attractions_agent",
        agent_config=OpenAIAgentConfig(system_prompt=system_prompt),
        description="Local attractions expert that recommends the best places to visit",
        tool_registry=tool_registry
    )
    agent.setup()
    return agent


def create_country_agent(tool_registry) -> OpenAIAgent:
    """Create an agent that has country specific knowledge."""
    system_prompt = """You are an expert on the quirks and laws of your country.
    Provide information about the culture, customs, and unique aspects of your country.
    Offer advice and tips for travelers visiting your country.
    You should only provide information about the country asked for, and politely decline if asked about anything else."""

    agent = OpenAIAgent(
        agent_name="country_agent",
        agent_config=OpenAIAgentConfig(system_prompt=system_prompt),
        description="Country expert that provides information about culture, customs, and travel tips",
        tool_registry=tool_registry
    )
    agent.setup()
    return agent


def create_language_agent(tool_registry) -> OpenAIAgent:
    """Create a language translation agent."""
    system_prompt = """You are a native speaker of your language and an expert in translation.
    Provide some translations and explanations of common phrases in your language.
    Help users learn and understand your language better. 
    You should only provide translations and explanations; no other information."""

    agent = OpenAIAgent(
        agent_name="language_agent",
        agent_config=OpenAIAgentConfig(system_prompt=system_prompt),
        description="Language expert that provides translations and explanations of common phrases",
        tool_registry=tool_registry
    )
    agent.setup()
    return agent


def create_classifier_agent() -> OpenAIAgent:
    """Create a classifier agent for language and task detection."""
    system_prompt = """You are a classifier. Your job is to determine the best agent based on the user's message. """

    agent = OpenAIAgent(
        agent_name="classifier",
        agent_config=OpenAIAgentConfig(system_prompt=system_prompt),
        description="Language and task classifier for routing messages"
    )
    agent.setup()
    return agent


def setup_orchestrator():
    """Set up the multi-agent orchestrator with all components."""
    # Set up shared components
    tool_registry = setup_memory_components()

    # Create agents
    food_agent = create_food_agent(tool_registry)
    attractions_agent = create_attractions_agent(tool_registry)
    country_agent = create_country_agent(tool_registry)
    language_agent = create_language_agent(tool_registry)

    classifier_agent = create_classifier_agent()

    # Set up agent registry
    registry = AgentRegistry()
    registry.register_agent(food_agent)
    registry.register_agent(attractions_agent)
    registry.register_agent(country_agent)
    registry.register_agent(language_agent)

    # Create and configure the classifier
    classifier = LLMClassifier(classifier_agent, default_agent="country_agent")

    # Create the orchestrator
    orchestrator = ReActOrchestrator(
        agent_registry=registry,
        classifier=classifier,
        default_agent_name=None,
        verbose=True
    )

    return orchestrator


def format_conversation_context(messages):
    """Format conversation history for context."""
    context = "\nPrevious conversation:\n"
    for msg in messages:
        sender = "User" if msg.sender == "user" else "Assistant"
        context += f"{sender}: {msg.content}\n"
    return context


def main():
    # Set up the orchestrator and all components
    orchestrator = setup_orchestrator()
    thread_id = "test_conversation"

    print("Welcome to your trip planner (type 'exit' to quit)")
    print("You can ask for food recommendations, local attractions, country information, or language translations.")
    print("-" * 50)

    def stream_callback(chunk):
        print(chunk, end="", flush=True)

    while True:
        # Get user input
        user_message = input("\nYou: ").strip()

        # Check for exit condition
        if user_message.lower() == 'exit':
            print("\nGoodbye!")
            break

        enhanced_input = user_message

        # Print Assistant prompt and get response
        print("\nAssistant: ", flush=True)
        response = orchestrator.orchestrate(
            thread_id=thread_id,
            user_message=enhanced_input,
            stream_callback=stream_callback
        )
        print(response)
        print()


if __name__ == "__main__":
    main()
