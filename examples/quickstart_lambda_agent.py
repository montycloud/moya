"""
Interactive example using LambdaAgent to invoke AWS Lambda functions.
"""

import os
from moya.tools.tool_registry import ToolRegistry
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.agents.lambda_agent import LambdaAgent, LambdaAgentConfig
from moya.tools.base_tool import BaseTool


def setup_agent():
    # Set up tool registry
    tool_registry = ToolRegistry()

    # Configure LambdaAgent
    config = LambdaAgentConfig(
        agent_name="lambda_agent",
        agent_type="LambdaAgent",
        description="An agent that invokes AWS Lambda functions",
        function_name=os.getenv("LAMBDA_FUNCTION_NAME"), # Function name is from environment variable - can be from a different source. This is for demonstration purposes.
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        tool_registry=tool_registry,
    )

    # Create LambdaAgent
    agent = LambdaAgent(config)

    # Set up registry and orchestrator
    agent_registry = AgentRegistry()
    agent_registry.register_agent(agent)
    orchestrator = SimpleOrchestrator(
        agent_registry=agent_registry,
        default_agent_name="lambda_agent"
    )

    return orchestrator, agent


def main():
    orchestrator, agent = setup_agent()

    print("Welcome to Lambda Agent Example! (Type 'quit' or 'exit' to end)")
    print("-" * 50)

    while True:
        # Get user input
        user_input = input("\nYou: ").strip()

        # Check for exit command
        if user_input.lower() in ['quit', 'exit']:
            print("\nGoodbye!")
            break

        # Print Assistant prompt
        print("\nLambda Response: ", end="", flush=True)

        # Define callback for streaming
        def stream_callback(chunk):
            print(chunk, end="", flush=True)

        # Get response using stream_callback
        response = orchestrator.orchestrate(
            thread_id="example_thread",
            user_message=user_input,
            stream_callback=stream_callback
        )

        # Print newline after response
        print()


if __name__ == "__main__":
    main()
