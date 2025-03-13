import click
import logging
import os
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool_registry import ToolRegistry
from moya.tools.memory_tool import MemoryTool
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator

from ..agents.documentation_agent import DocumentationAgent
from ..tools.knowledge_base_tool import KnowledgeBaseTool

logger = logging.getLogger(__name__)
console = Console()

def setup_agent():
    """Initialize the documentation agent with memory capabilities."""
    # Get package directory path
    package_dir = Path(__file__).parent.parent
    docs_path = package_dir / "data" / "documentation"
    
    logger.info(f"Setting up agent with docs path: {docs_path}")
    
    # Validate documentation path
    if not docs_path.exists():
        raise ValueError(f"Documentation path not found: {docs_path}")
        
    # Log available documentation files
    doc_files = list(docs_path.glob("*.md"))
    logger.info(f"Found documentation files: {[f.name for f in doc_files]}")
    if not doc_files:
        raise ValueError("No documentation files found!")

    # Set up memory components
    memory_repo = InMemoryRepository()
    memory_tool = MemoryTool(memory_repository=memory_repo)
    tool_registry = ToolRegistry()
    tool_registry.register_tool(memory_tool)

    # Set up knowledge base with validation
    try:
        knowledge_tool = KnowledgeBaseTool(
            name="KnowledgeBaseTool",
            description="Tool for searching Moya documentation",
            docs_path=str(docs_path)
        )
        # Validate tool initialization
        test_doc = knowledge_tool.get_doc("core-concepts.md")
        if not test_doc:
            raise ValueError("Failed to read core documentation")
            
        tool_registry.register_tool(knowledge_tool)
        logger.info("Successfully initialized knowledge base tool")
    except Exception as e:
        logger.error(f"Failed to initialize knowledge base: {e}")
        raise

    # Create documentation agent
    agent = DocumentationAgent(tool_registry=tool_registry)
    agent.setup()
    logger.info("Documentation agent initialized successfully")

    # Set up registry and orchestrator
    registry = AgentRegistry()
    registry.register_agent(agent)
    orchestrator = SimpleOrchestrator(
        agent_registry=registry,
        default_agent_name="documentation_agent"
    )

    return orchestrator, agent

@click.group()
def cli():
    """Moya Hackathon Assistant - Your guide to the framework and hackathon."""
    pass

@cli.command()
def chat():
    """Start an interactive chat session with the assistant."""
    orchestrator, agent = setup_agent()
    thread_id = "hackathon_chat"

    console.print(Panel.fit(
        "[bold green]Welcome to Moya Hackathon Assistant![/]\n"
        "I can help you with:\n"
        "• Framework documentation\n"
        "• Technical questions\n"
        "• Best practices\n"
        "(Type 'exit' to end the session)"
    ))

    while True:
        user_input = console.input("\n[bold blue]You:[/] ").strip()
        
        if user_input.lower() in ['exit', 'quit']:
            console.print("\n[bold green]Goodbye! Happy hacking![/]")
            break

        try:
            # Store user message
            agent.call_tool(
                tool_name="MemoryTool",
                method_name="store_message",
                thread_id=thread_id,
                sender="user",
                content=user_input
            )

            console.print("\n[bold green]Assistant:[/] ", end="")
            
            def stream_callback(chunk):
                console.print(chunk, end="")

            response = orchestrator.orchestrate(
                thread_id=thread_id,
                user_message=user_input,
                stream_callback=stream_callback
            )
            console.print()

        except Exception as e:
            console.print(f"\n[bold red]Error:[/] {str(e)}")

if __name__ == "__main__":
    cli()
