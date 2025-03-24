import os
from moya.agents.azure_openai_agent import AzureOpenAIAgent, AzureOpenAIAgentConfig
from moya.agents.remote_agent import RemoteAgent, RemoteAgentConfig
from moya.classifiers.llm_team_classifier import LLMTeamClassifier
from moya.orchestrators.team_orchestrator import TeamOrchestrator
from moya.registry.agent_registry import AgentRegistry
from moya.tools.ephemeral_memory import EphemeralMemory
from moya.memory.file_system_repo import FileSystemRepository
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool_registry import ToolRegistry
from moya.tools.base_tool import BaseTool
import io
import contextlib
import boto3

AZURE_OPENAI_ENDPOINT="https://day2openai.openai.azure.com/"
AZURE_OPENAI_API_VERSION="2025-02-01-preview"

def setup_memory_components():
    """Set up memory components for the agents."""
    tool_registry = ToolRegistry()
    EphemeralMemory.configure_memory_tools(tool_registry)
    return tool_registry

def run_python_code(code_snippet : str) -> str:
    """
    Run Python code snippet and return the output.

    Parameters:
        - code_snippet : The Python code snippet to run.
    """
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        # Very unsafe, only for demonstration purposes
        exec(code_snippet)
    return f.getvalue()

def append_to_file(file_path : str, content : str) -> str:
    """
    Append content to a file.

    Parameters:
        - file_path : The path to the file.
        - content : The content to append.
    """
    with open(file_path, "a") as f:
        f.write(content)
    return f"Appended content to {file_path}"

def read_from_file(file_path :str) -> str:
    """
    Read contents of a file.

    Parameters:
        - file_path : The path to the file.
    """
    with open(file_path, "r") as f:
        return f.read()
    
def write_to_file(file_path : str, content : str) ->str:
    """
    Write content to a file, this overwrites the existing contents of a file.
    Use this if the content of the files are to be replaced with a summary or with newer version.

    Parameters:
        - file_path : The path to the file.
        - content : The content to write.
    """
    with open(file_path, "w") as f:
        f.write(content)
    return f"Wrote content to {file_path}"

def create_wafr_agent(tool_registry) -> AzureOpenAIAgent:
    """Create a WAFR agent for code execution and file writing."""
    agent_config = AzureOpenAIAgentConfig(
        agent_name="wafr_agent",
        agent_type="ChatAgent",
        description="Agent that is an expert in AWS Well-Architected Framework Review (WAFR), asks as a consultant and provides guidance on best practices and checks to validate them.",
        system_prompt="""You are WAFRAgent, a professional AWS cloud expert and you are a part of a team of specialized agents working to solve customer's queries.
                        Your primary goal is to help customers by providing guidance on the best practices for AWS cloud architecture or work with other agents to provide expertise on the best practices.
                        You undestand the AWS Well architected review framework and can provide guidance on the best practices.
                        If asked about a specific pillar, provide detailed information and best practices for that pillar.
                        You should also provide any resource specific checks that can be performed to validate the best practices.
                        for example, if asked about the security pillar, you should provide detailed information on the best practices for security and the checks that can be performed to validate the best practices.
                        for even specific example, is asked about security best practices for S3, you should provifde detailed information on a list of checks like 'check if the S3 bucket is encrypted', 'check if a bucket is open to public' etc.
                        Suggest all possible checks that can be performed to validate the best practices.
                        You should not provide any other information except about the AWS Well architected review framework.
                        You act as an advisor, you cannot perform any tests or generate reports on your own.""",
        llm_config={
            'temperature': 0.7
        },
        model_name="o3-mini",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_OPENAI_API_VERSION
    )
    return AzureOpenAIAgent(config=agent_config)

def create_check_agent(tool_registry) -> AzureOpenAIAgent:
    """Create a check agent for code execution and file writing."""
    agent_config = AzureOpenAIAgentConfig(
        agent_name="check_agent",
        agent_type="ChatAgent",
        description="Agent that can perform checks on an AWS resource by generating python code and running it",
        system_prompt="""You are a professional AWS cloud expert and an expert in writing safe Python code, and you are a part of a team of specialized agents working to solve customer's queries.
                        You understand boto3 and can write code to check if a best practice has been implemented on a AWS resource.
                        You can also run the code to check if the best practice has been implemented.
                        Assume that AWS credentials are available in the environment and the boto3 library is installed.
                        The AWS credentials only have read-only access to the AWS resources. Do not write code that modifies resources.
                        Write code for all the checks that are asked or mentioned in the user input and are requested by other specilist agents and provide the output of the code.
                        In your code you can use the boto3 library to interact with AWS resources to list, read and get detailed info on the resources.
                        When you write code, make sure you are clear and concise and are looking for only the resorces in scope.
                        Run the code and provide the output of the code, if the code fails to run capture the errors, fix the errors and run the code again.
                        Keep an detailed log of your activity, the input you saw, code you generated and captured output of the code should all be stored in a file called 'check_log.txt'.
                        Always store your intent and code first before you run any code. Apart from logging you will provide a detailed summary of the code results in your response""",
        llm_config={
            'temperature': 0.7
        },
        model_name="o3-mini",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        tool_registry=tool_registry,
        api_base=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_OPENAI_API_VERSION
    )
    return AzureOpenAIAgent(config=agent_config)

def create_test_report_agent(tool_registry) -> AzureOpenAIAgent:
    """Create a test report agent for a WAFR test consisting of series of checks."""
    agent_config = AzureOpenAIAgentConfig(
        agent_name="test_report_agent",
        agent_type="ChatAgent",
        description="Agent that can generate reports for any cloudops activity or check like WAFR test detailing the results and expert opinion.",
        system_prompt="""You are a professional AWS cloud expert and a certified AWS Cloud practitioner. 
                        You are a part of multi agentic workflow where other agents perform checks and you generate a detailed test report.
                        You understand the AWS Well architected review framework and can provide guidance on the best practices.
                        You are also an excellent technical writer and can generate a detailed test report for a WAFR test.
                        You can provide detailed information on the checks performed, the results of the checks and the recommendations for the checks.
                        You can also provide detailed information on the best practices and the reasons for the best practices.
                        You should not provide any other information except about the AWS Well architected review framework and the test report.
                        For best practices, provide detailed information and examples.
                        Write your test report in a file called 'test_report.md if no explicit file name is specified.
                        Write your report in markdown format, summarize the content ot rewrite the report as 
                        Assume that the test results are available in the user input and you will be called multiple times with the test results.""",
        llm_config={
            'temperature': 0.7
        },
        model_name="o3-mini",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=AZURE_OPENAI_ENDPOINT,
        tool_registry=tool_registry,
        api_version=AZURE_OPENAI_API_VERSION
    )
    return AzureOpenAIAgent(config=agent_config)

def create_cloudops_advisor_agent(tool_registry) -> AzureOpenAIAgent:
    """Create a cloudops advisor agent for cloud operations and monitoring."""
    agent_config = AzureOpenAIAgentConfig(
        agent_name="cloudops_advisor_agent",
        agent_type="ChatAgent",
        description="A helpful Agent that is an expert in cloud operations and monitoring, acts as a consultant and provides guidance to users for their queries.",
        system_prompt="""You are a professional AWS cloud expert.
                        You undestand the AWS cloud operations and monitoring best practices.
                        You can provide guidance on how to accomplish a cloudops outcome. 
                        If asked about a specific outcome, provide a list of actions that can be performed to achieve the outcome.
                        Do not provide detailed information unless asked. Be concise and clear in your responses.
                        Always begin with taking a look at the user message, if there is any information that is covered or answered already do not repeat it. It is okay to say you do not have any more advice to offer.
                        Your response should be action oriented, specify exact steps that can be performed to achieve the outcome.
                        for example if asked about how to check for an EC2 instance, you should provide a list of actions like 'run a python script to list all EC2 instances', 'use the AWS console to list all EC2 instances' etc.
                        You are always the first and only point of contact for any user queries related to cloud, cloudops and monitoring.""",
        llm_config={
            'temperature': 0.7
        },
        model_name="o3-mini",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_OPENAI_API_VERSION
    )
    return AzureOpenAIAgent(config=agent_config)


def create_classifier_agent() -> AzureOpenAIAgent:
    """Create a classifier agent for language and task detection."""

    agent_config = AzureOpenAIAgentConfig(
        agent_name="classifier",
        agent_type="AgentClassifier",
        description="Language and task classifier for routing messages",
        tool_registry=None,
        model_name="o3-mini",    
        system_prompt="You are a helpful agent classifier.",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_OPENAI_API_VERSION
    )

    return AzureOpenAIAgent(config=agent_config)



def setup_orchestrator():
    """Set up the multi-agent orchestrator with all components."""
    # Set up shared components
    tool_registry = setup_memory_components()
    tool_registry.register_tool(BaseTool(name="RunPythonCode", function=run_python_code))
    tool_registry.register_tool(BaseTool(name="AppendToFile", function=append_to_file))
    tool_registry.register_tool(BaseTool(name="ReadFile", function=read_from_file))
    tool_registry.register_tool(BaseTool(name="UpdateFile", function=write_to_file))

    # Create agents
    classifier_agent = create_classifier_agent()

    # Set up agent registry
    registry = AgentRegistry()
    registry.register_agent(create_wafr_agent(tool_registry))
    registry.register_agent(create_check_agent(tool_registry))
    registry.register_agent(create_test_report_agent(tool_registry))
    registry.register_agent(create_cloudops_advisor_agent(tool_registry))

    # Create and configure the classifier
    classifier = LLMTeamClassifier(classifier_agent, default_agent="cloudops_advisor_agent")

    # Create the orchestrator
    orchestrator = TeamOrchestrator(
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
    # Setup file system memory 
    EphemeralMemory.memory_repository = FileSystemRepository(base_path="./tmp/moya_memory")
    # Set up the orchestrator and all components
    orchestrator = setup_orchestrator()
    thread_id = "test_conversation"

    print("Starting multi-agent chat (type 'exit' to quit)")
    print("You can chat in English or Spanish, or request responses in either language.")
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
