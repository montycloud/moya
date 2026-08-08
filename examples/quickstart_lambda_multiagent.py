import os
from moya.agents.lambda_agent import LambdaAgent, LambdaAgentConfig
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator
from moya.registry.agent_registry import AgentRegistry
from moya.classifiers.llm_classifier import LLMClassifier
from moya.tools.tool_registry import ToolRegistry
from moya.tools.ephemeral_memory import EphemeralMemory


def create_lambda_agent(agent_name, function_name, description, tool_registry):
    """Create a LambdaAgent with the given configuration."""
    config = LambdaAgentConfig(
        agent_name=agent_name,
        agent_type="LambdaAgent",
        description=description,
        function_name=function_name,
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        tool_registry=tool_registry,
    )
    return LambdaAgent(config)


def setup_orchestrator():
    """Set up the multi-agent orchestrator with Lambda agents."""
    # Set up tool registry
    tool_registry = ToolRegistry()

    # Create Lambda agents
    agent1 = create_lambda_agent(
        agent_name="lambda_agent_1",
        function_name=os.getenv("LAMBDA_FUNCTION_NAME_1"), # Function name is from environment variable - can be from a different source. This is for demonstration purposes.
        description="Lambda agent for function 1",
        tool_registry=tool_registry,
    )

    agent2 = create_lambda_agent(
        agent_name="lambda_agent_2",
        function_name=os.getenv("LAMBDA_FUNCTION_NAME_2"),
        description="Lambda agent for function 2",
        tool_registry=tool_registry,
    )

    # Set up agent registry
    registry = AgentRegistry()
    registry.register_agent(agent1)
    registry.register_agent(agent2)

    # Create a classifier agent
    system_prompt="""You are a classifier. Your job is to determine the best agent based on the user's message:
        1. If the message is in English or requests English response, return 'lambda_agent_1'
        2. If the message is in Spanish or requests Spanish response, return 'lambda_agent_2'
        3. For any other language requests, return null
        
        Analyze both the language and intent of the message.
        Return only the agent name as specified above."""

    classifier_agent_config = OpenAIAgentConfig(
        agent_name="classifier",
        agent_type="AgentClassifier",
        description="Classifier for routing messages to Lambda agents",
        system_prompt=system_prompt,
        model_name="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    classifier_agent = OpenAIAgent(config=classifier_agent_config)

    # Create and configure the classifier
    classifier = LLMClassifier(classifier_agent, default_agent="lambda_agent_1")

    # Create the orchestrator
    orchestrator = MultiAgentOrchestrator(
        agent_registry=registry,
        classifier=classifier,
        default_agent_name=None
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

    print("Starting multi-agent chat (type 'exit' to quit)")
    print("You can chat in English or Spanish, or request responses in either language.")
    print("-" * 50)

    def stream_callback(chunk):
        print(chunk, end="", flush=True)

    EphemeralMemory.store_message(thread_id=thread_id, sender="system", content=f"thread ID: {thread_id}")

    while True:
        # Get user input
        user_message = input("\nYou: ").strip()

        # Check for exit condition
        if user_message.lower() == 'exit':
            print("\nGoodbye!")
            break

        # Get available agents
        agents = orchestrator.agent_registry.list_agents()
        if not agents:
            print("\nNo agents available!")
            continue

        # Get the last used agent or default to the first one
        last_agent = orchestrator.agent_registry.get_agent(agents[0].name)

        # Store the user message first
        EphemeralMemory.store_message(thread_id=thread_id, sender="user", content=user_message) 

        session_summary = EphemeralMemory.get_thread_summary(thread_id)
        enriched_input = f"{session_summary}\nCurrent user message: {user_message}"

        # Print Assistant prompt and get response
        print("\nAssistant: ", end="", flush=True)
        response = orchestrator.orchestrate(
            thread_id=thread_id,
            user_message=enriched_input,
            stream_callback=stream_callback
        )
        print()  # New line after response
        EphemeralMemory.store_message(thread_id=thread_id, sender="system", content=response)


if __name__ == "__main__":
    main()
