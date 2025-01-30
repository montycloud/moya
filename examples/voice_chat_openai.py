"""
Interactive voice chat example using OpenAI agent with voice capabilities.
"""

from moya.messages.voice_message import VoiceMessage
from moya.agents.openai_agent import OpenAIAgent
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool_registry import ToolRegistry
from moya.tools.memory_tool import MemoryTool
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
import sounddevice as sd
import soundfile as sf
import numpy as np
import logging
import tempfile
import io

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_agent():
    """Set up OpenAI agent with necessary components."""
    # Set up memory components
    memory_repo = InMemoryRepository()
    memory_tool = MemoryTool(memory_repository=memory_repo)
    tool_registry = ToolRegistry()
    tool_registry.register_tool(memory_tool)

    # Create OpenAI agent
    agent = OpenAIAgent(
        agent_name="openai_assistant",
        description="An AI assistant powered by OpenAI with voice capabilities",
        model_name="gpt-4o",
        tool_registry=tool_registry,
        system_prompt="You are a helpful AI assistant. Be concise and clear."
    )
    
    # Setup agent and verify connection
    try:
        agent.setup()
        logger.info("Successfully connected to OpenAI")
    except Exception as e:
        logger.error(f"Failed to connect to OpenAI: {e}")
        raise

    # Set up registry and orchestrator
    agent_registry = AgentRegistry()
    agent_registry.register_agent(agent)
    orchestrator = SimpleOrchestrator(
        agent_registry=agent_registry,
        default_agent_name="openai_assistant"
    )

    return orchestrator, agent

def record_audio(duration: float = 5.0, sample_rate: int = 16000) -> VoiceMessage:
    """Record audio from microphone."""
    print(f"Recording for {duration} seconds...")
    audio_data = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype=np.float32
    )
    sd.wait()
    return VoiceMessage(
        audio_data=audio_data.flatten(),
        sample_rate=sample_rate
    )

def play_audio(voice_message: VoiceMessage):
    """Play audio from a VoiceMessage."""
    if isinstance(voice_message.audio_data, bytes):
        # Convert bytes to numpy array
        with io.BytesIO(voice_message.audio_data) as buf:
            data, sample_rate = sf.read(buf)
    else:
        data = voice_message.audio_data
        sample_rate = voice_message.sample_rate
    
    sd.play(data, sample_rate)
    sd.wait()

def main():
    orchestrator, agent = setup_agent()
    thread_id = "voice_chat_001"
    
    print("Welcome to Voice Chat! (Say 'quit' or press Ctrl+C to end)")
    print("Note: Using OpenAI for speech recognition and synthesis")
    print("-" * 50)
    
    try:
        while True:
            # Record voice input
            voice_msg = record_audio()
            
            try:
                # Convert speech to text
                text_input = agent.speech_to_text(voice_msg)
                print("\nYou said:", text_input)
                
                if text_input.lower() in ['quit', 'exit']:
                    print("\nGoodbye!")
                    break
                
                # Get conversation context
                previous_messages = agent.get_last_n_messages(thread_id, n=5)
                
                # Handle the conversation
                response = agent.handle_message(text_input)
                print("\nAssistant:", response)
                
                # Store the conversation
                agent.call_tool(
                    tool_name="MemoryTool",
                    method_name="store_message",
                    thread_id=thread_id,
                    sender="user",
                    content=text_input
                )
                
                agent.call_tool(
                    tool_name="MemoryTool",
                    method_name="store_message",
                    thread_id=thread_id,
                    sender="assistant",
                    content=response
                )
                
                # Convert response to speech
                voice_response = agent.text_to_speech(response)
                play_audio(voice_response)
                    
            except Exception as e:
                logger.error(f"Error during voice chat: {e}")
                print("\nAn error occurred. Please try again.")
                continue
                
    except KeyboardInterrupt:
        print("\nGoodbye!")

if __name__ == "__main__":
    main()
