# Installation Guide

## Installation Methods

### Method 1: Using pip (Recommended)
```bash
# Install latest stable release
pip install moya-framework
```

### Method 2: From Source
```bash
git clone https://github.com/your-org/moya.git
cd moya
pip install -e .
```

## Environment Setup

### 1. OpenAI Integration
```bash
export OPENAI_API_KEY="your-api-key"
```

### 2. AWS Bedrock Integration
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### 3. Ollama Setup
1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Start the Ollama service
3. Pull your desired model:
```bash
ollama pull llama2
```

## Project Structure
```
my_moya_project/
├── agents/          # Custom agent implementations
├── tools/           # Custom tools
├── config/          # Configuration files
└── main.py         # Entry point
```

## Verification

```python
from moya import __version__
print(f"Moya version: {__version__}")

# Test agent setup
from moya.agents import OpenAIAgent
agent = OpenAIAgent(
    agent_name="test",
    description="Test agent"
)
agent.setup()  # Verifies configuration
```

## Troubleshooting

1. **API Key Issues**
   - Verify environment variables are set
   - Check API key permissions
   - Ensure proper key format

2. **Model Access**
   - Confirm model availability in your region
   - Verify API quota and limits
   - Check model access permissions

3. **Ollama Issues**
   - Verify Ollama service is running
   - Check model download status
   - Confirm port availability (default: 11434)
