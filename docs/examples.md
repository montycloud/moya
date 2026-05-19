# Using Examples in Moya

Moya provides a variety of example scripts to help you get started with different features and integrations. These examples are located in the `examples/` directory of the repository. Below is a guide to using these examples effectively.

## Quick Start Examples

### 1. OpenAI Integration

File: `quick_start_openai.py`

This example demonstrates how to set up and use an OpenAI agent. To run this example:

1. Ensure you have the required dependencies installed:
   ```bash
   pip install openai
   ```

2. Set up your OpenAI API key in the environment:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

3. Run the script:
   ```bash
   python examples/quick_start_openai.py
   ```

### 2. Azure OpenAI Integration

File: `quick_start_azure_openai.py`

This example shows how to use Azure's OpenAI service. To run this example:

1. Install the required dependencies:
   ```bash
   pip install azure-identity openai
   ```

2. Set up your Azure credentials in the environment:
   ```bash
   export AZURE_OPENAI_API_KEY="your-api-key"
   export AZURE_OPENAI_ENDPOINT="your-endpoint"
   ```

3. Run the script:
   ```bash
   python examples/quick_start_azure_openai.py
   ```

## Multi-Agent Examples

### 1. Multi-Agent React

File: `quick_start_multiagent_react.py`

This example demonstrates how to set up multiple agents that interact with each other. To run this example:

1. Install the required dependencies:
   ```bash
   pip install openai
   ```

2. Run the script:
   ```bash
   python examples/quick_start_multiagent_react.py
   ```

### 2. Multi-Agent Collaboration

File: `quick_start_multiagent.py`

This example shows how multiple agents can collaborate to solve tasks. To run this example:

1. Install the required dependencies:
   ```bash
   pip install openai
   ```

2. Run the script:
   ```bash
   python examples/quick_start_multiagent.py
   ```

## Tool Examples

### Quick Tools

File: `quick_tools.py`

This script demonstrates how to use various tools provided by Moya. To run this example:

1. Run the script:
   ```bash
   python examples/quick_tools.py
   ```

## Remote Agent Examples

### Remote Agent with Authentication

File: `remote_agent_server_with_auth.py`

This example demonstrates how to set up a remote agent server with authentication. To run this example:

1. Install the required dependencies:
   ```bash
   pip install fastapi uvicorn python-dotenv
   ```

2. Set up your environment variables in a `.env` file:
   ```env
   AUTH_TOKEN="your-auth-token"
   ```

3. Run the script:
   ```bash
   python examples/remote_agent_server_with_auth.py
   ```

## Additional Notes

- Ensure you have the necessary API keys and credentials set up before running the examples.
- Refer to the individual scripts for more details on configuration and usage.
- For further assistance, consult the [Getting Started Guide](getting-started.md).