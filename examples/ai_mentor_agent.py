import os
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

def create_academic_advisor(tool_registry) -> OpenAIAgent:
    """Create academic advisor agent."""
    agent_config = OpenAIAgentConfig(
        system_prompt="""You are an Academic Advisor AI specializing in helping students with:
        - Answering study-related questions
        - Homework assistance and explanations
        - Study planning and organization
        - Subject matter guidance
        
        Always provide detailed explanations and encourage critical thinking.
        Focus on helping students understand concepts rather than just giving answers.""",
        model_name="gpt-4",
        temperature=0.7
    )
    
    agent = OpenAIAgent(
        agent_name="academic_advisor",
        description="Academic advisor specializing in study help and subject guidance",
        agent_config=agent_config,
        tool_registry=tool_registry
    )
    agent.setup()
    return agent

def create_career_coach(tool_registry) -> OpenAIAgent:
    """Create career coach agent."""
    agent_config = OpenAIAgentConfig(
        system_prompt="""You are a Career Coach AI specializing in:
        - Resume review and improvement
        - Interview preparation
        - Career path guidance
        - Skill development advice
        
        Provide professional, actionable advice focused on student career development.
        Always be encouraging while maintaining professionalism.""",
        model_name="gpt-4",
        temperature=0.7
    )
    
    agent = OpenAIAgent(
        agent_name="career_coach",
        description="Career coach for professional development and job preparation",
        agent_config=agent_config,
        tool_registry=tool_registry
    )
    agent.setup()
    return agent

def create_job_search_agent(tool_registry) -> OpenAIAgent:
    """Create job search agent."""
    agent_config = OpenAIAgentConfig(
        system_prompt="""You are an Internship & Job Search AI specializing in:
        - Finding relevant internship opportunities
        - Job application strategies
        - Industry insights
        - Application tracking and follow-up
        
        Focus on student-friendly opportunities and entry-level positions.
        Provide practical advice for job searching and application processes.""",
        model_name="gpt-4",
        temperature=0.7
    )
    
    agent = OpenAIAgent(
        agent_name="job_search",
        description="Job search specialist focusing on internships and entry-level positions",
        agent_config=agent_config,
        tool_registry=tool_registry
    )
    agent.setup()
    return agent

def create_classifier_agent() -> OpenAIAgent:
    """Create classifier agent for task routing."""
    agent_config = OpenAIAgentConfig(
        system_prompt="""You are a classifier that routes student queries to specialized agents:
        1. academic_advisor: For study help, homework questions, and academic guidance
        2. career_coach: For resume review, interview prep, and career guidance
        3. job_search: For internship search, job applications, and opportunity finding
        
        Analyze the query and return ONLY the most appropriate agent name.""",
        model_name="gpt-4"
    )
    
    agent = OpenAIAgent(
        agent_name="classifier",
        description="Query classifier for routing to specialized agents",
        agent_config=agent_config
    )
    agent.setup()
    return agent

def setup_orchestrator():
    """Set up the multi-agent orchestrator."""
    tool_registry = setup_memory_components()
    
    # Create specialized agents
    academic_agent = create_academic_advisor(tool_registry)
    career_agent = create_career_coach(tool_registry)
    job_agent = create_job_search_agent(tool_registry)
    classifier_agent = create_classifier_agent()
    
    # Register agents
    registry = AgentRegistry()
    registry.register_agent(academic_agent)
    registry.register_agent(career_agent)
    registry.register_agent(job_agent)
    
    # Setup classifier and orchestrator
    classifier = LLMClassifier(classifier_agent)
    orchestrator = MultiAgentOrchestrator(
        agent_registry=registry,
        classifier=classifier
    )
    
    return orchestrator

def format_conversation_context(messages):
    """Format conversation history for context."""
    context = "\nPrevious conversation:\n"
    for msg in messages:
        sender = "Student" if msg.sender == "user" else "Mentor"
        context += f"{sender}: {msg.content}\n"
    return context

def main():
    orchestrator = setup_orchestrator()
    thread_id = "mentor_session"
    
    print("🎓 Welcome to AI Student Mentor!")
    print("I can help you with:")
    print("- Academic questions and study help")
    print("- Career guidance and resume review")
    print("- Internship and job search")
    print("(Type 'exit' to end the session)")
    print("-" * 50)
    
    def stream_callback(chunk):
        print(chunk, end="", flush=True)
    
    while True:
        user_message = input("\nStudent: ").strip()
        
        if user_message.lower() == 'exit':
            print("\nGoodbye! Good luck with your studies! 🎓")
            break
        
        agents = orchestrator.agent_registry.list_agents()
        if not agents:
            print("\nNo mentors available!")
            continue
        
        # Get last agent or default to first
        last_agent = orchestrator.agent_registry.get_agent(agents[0])
        
        # Store message in memory
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
                print(f"Error storing message: {e}")
        
        # Get conversation context
        previous_messages = last_agent.get_last_n_messages(thread_id, n=5)
        
        # Enhance input with context
        if previous_messages:
            context = format_conversation_context(previous_messages)
            enhanced_input = f"{context}\nCurrent question: {user_message}"
        else:
            enhanced_input = user_message
        
        print("\nMentor: ", end="", flush=True)
        response = orchestrator.orchestrate(
            thread_id=thread_id,
            user_message=enhanced_input,
            stream_callback=stream_callback
        )
        print()

if __name__ == "__main__":
    main()
