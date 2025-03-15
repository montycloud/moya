# MOYA - Meta Orchestration framework for Your Agents

MOYA is a reference implementation of our research paper titled "Engineering LLM Powered Multi-agent Framework for Autonomous CloudOps". The framework provides a flexible and extensible architecture for creating, managing, and orchestrating multiple AI agents to handle various tasks autonomously.

Preprint of the paper can be accessed at [arXiv](https://arxiv.org/abs/2501.08243).

## Features

- **Agent Management**: Create, register, and manage multiple AI agents.
- **Orchestration**: Orchestrate conversations and tasks across multiple agents.
- **Memory Tools**: Integrate memory tools to maintain conversation context and history.
- **Streaming Responses**: Support for streaming responses from agents.
- **Extensibility**: Easily extend the framework with new agents, tools, and orchestrators.

## Getting Started

```bash
pip install moya  # Only core framework
pip install moya[all] # All the supported services such as OpenAI, Bedrock, Ollama, Crewai
# or install specific ones - for example openai and ollama
pip install moya[openai, ollama]
```


# Contributing to MOYA

We accept contributions exclusively through forked repositories. Please follow these steps:

1. Fork this repository to your GitHub account
2. Create a new branch in your fork for your changes
3. Make your changes and commit them to your branch
4. Submit a pull request from your fork's branch to our main repository

### Prerequisites

- Python 3.10+
- Install required dependencies:
  ```bash
  pip install .
  ```

### Quick Start Examples

#### OpenAI Agent

Interactive chat example using OpenAI agent with conversation memory.

```python
# filepath: ~/github/moya/examples/quick_start_openai.py

python -m examples.quick_start_openai

```

#### Bedrock Agent

Interactive chat example using BedrockAgent with conversation memory.

```python
# filepath: ~/github/moya/examples/quick_start_bedrock.py

AWS_PROFILE=my_profile_name python -m examples.quick_start_bedrock
```

#### Multi-Agent Orchestration

Example demonstrating multi-agent orchestration with language and task classification.

```python
# filepath: ~/github/moya/examples/quick_start_multiagent.py

python -m examples.quick_start_multiagent
```

#### Dynamic Agent Creation

Example demonstrating dynamic agent creation and registration during runtime.
![moya](./media/Dynamic_Agents.mov)

```python
# filepath: ~/github/moya/examples/dynamic_agents.py


python -m examples.dynamic_agents
```

### Directory Structure

```
moya/
├── agents/                # Agent implementations (OpenAI, Bedrock, Ollama, Remote)
├── classifiers/           # Classifier implementations for agent selection
├── memory/                # Memory repository implementations
├── orchestrators/         # Orchestrator implementations for managing agent interactions
├── registry/              # Agent registry and repository implementations
├── tools/                 # Tool implementations (e.g., MemoryTool)
├── examples/              # Example scripts demonstrating various use cases
└── README.md              # This README file
```

### Contributing

We welcome contributions to the MOYA framework. Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Make your changes and commit them with descriptive messages.
4. Push your changes to your fork.
5. Create a pull request to the main repository.

### License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

### Contact

For any questions or inquiries, please contact the authors of the research paper or open an issue on the GitHub repository.
