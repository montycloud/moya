# Getting Started with Moya

This guide will help you set up Moya and create your first AI-powered application.

## Installation

1. Clone the Moya repository:
```bash
   git clone https://github.com/your-repo/moya.git
   cd moya
```

2. Install the required dependencies:
```bash
   pip install -r requirements.txt
```

## Creating Your First Agent

1. Create a Python script, `my_agent.py`: 
```python
   from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig

   # Configure the agent
   agent_config = OpenAIAgentConfig(
       system_prompt="You are a helpful AI assistant.",
       model_name="gpt-4o",
       temperature=0.7,
       max_tokens=2000
   )

   # Create the agent
   agent = OpenAIAgent(
       agent_name="my_agent",
       description="A simple AI assistant",
       agent_config=agent_config
   )

   # Set up the agent
   agent.setup()

   # Handle a message
   response = agent.handle_message("Hello, how can I help you?")
   print(response)
```

2. Run the script:
```bash
   python my_agent.py
```

## Next Steps

- Learn about [Agents](agents.md).
- Explore [Memory Management](memory.md).
- Understand [Tool Registry](tools.md).