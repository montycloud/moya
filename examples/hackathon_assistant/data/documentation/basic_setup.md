# Installing and Setting Up Moya

## Quick Installation

```bash
# Install latest stable version
pip install moya-framework

# Or install from source
git clone https://github.com/your-org/moya.git
cd moya
pip install -e .
```

## Basic Setup Steps

1. Install Dependencies:
   ```bash
   pip install moya-framework
   ```

2. Set Environment Variables:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

3. Create Basic Project:
   ```python
   from moya.agents import OpenAIAgent
   from moya.tools import ToolRegistry

   # Initialize agent
   agent = OpenAIAgent(
       agent_name="my_assistant",
       description="Basic Moya agent"
   )

   # Test setup
   response = agent.handle_message("Hello!")
   print(response)
   ```

## Prerequisites
- Python 3.10+
- OpenAI API key for GPT models
- Git (for source installation)

## Configuration
Store your configuration in `config.yml`:
```yaml
agent:
  name: my_assistant
  model: gpt-4
  temperature: 0.7
```

## Next Steps
1. Set up memory persistence
2. Add custom tools
3. Configure multiple agents
4. Implement orchestration
