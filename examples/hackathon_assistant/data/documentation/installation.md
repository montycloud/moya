# Installing and Setting Up Moya

## Installation Methods

### 1. Using pip (Recommended)
```bash
# Install latest stable release
pip install moya-framework

# For development version
pip install git+https://github.com/your-org/moya.git
```

### 2. From Source
```bash
git clone https://github.com/your-org/moya.git
cd moya
pip install -e .
```

## Initial Setup

### 1. Environment Configuration
```bash
# Set up OpenAI API key
export OPENAI_API_KEY="your-api-key"

# For AWS Bedrock (optional)
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### 2. Basic Project Structure
```
my_moya_project/
├── agents/             # Custom agent implementations
├── tools/              # Custom tools
├── config/            
│   └── config.yml     # Agent configurations
└── main.py            # Entry point
```

### 3. Minimal Working Example
```python
from moya.agents import OpenAIAgent
from moya.tools import ToolRegistry
from moya.memory import InMemoryRepository

# Initialize components
tool_registry = ToolRegistry()
memory_repo = InMemoryRepository()

# Configure agent
agent = OpenAIAgent(
    agent_name="test_agent",
    description="Basic test agent",
    tool_registry=tool_registry
)

# Test the setup
response = agent.handle_message("Hello!")
print(response)
```

## Verification

Run this test script to verify your installation:
```python
from moya import __version__
print(f"Moya version: {__version__}")

# Test OpenAI integration
from moya.agents import OpenAIAgent
agent = OpenAIAgent(agent_name="test")
agent.setup()  # This will verify API key and connections
```
