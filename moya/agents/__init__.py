from moya.agents.agent import Agent, AgentConfig
from moya.agents.agent_info import AgentInfo
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.agents.ollama_agent import OllamaAgent, OllamaAgentConfig
from moya.agents.remote_agent import RemoteAgent, RemoteAgentConfig

# Optional providers — imported lazily to avoid hard dependency errors
try:
    from moya.agents.azure_openai_agent import AzureOpenAIAgent, AzureOpenAIAgentConfig
    __all_azure = ["AzureOpenAIAgent", "AzureOpenAIAgentConfig"]
except ImportError:
    __all_azure = []

try:
    from moya.agents.bedrock_agent import BedrockAgent, BedrockAgentConfig
    __all_bedrock = ["BedrockAgent", "BedrockAgentConfig"]
except ImportError:
    __all_bedrock = []

try:
    from moya.agents.crewai_agent import CrewAIAgent, CrewAIAgentConfig
    __all_crewai = ["CrewAIAgent", "CrewAIAgentConfig"]
except ImportError:
    __all_crewai = []

__all__ = [
    "Agent", "AgentConfig", "AgentInfo",
    "OpenAIAgent", "OpenAIAgentConfig",
    "OllamaAgent", "OllamaAgentConfig",
    "RemoteAgent", "RemoteAgentConfig",
    *__all_azure,
    *__all_bedrock,
    *__all_crewai,
]
