# Moya Framework

MOYA is a reference implementation of the research paper titled "Engineering LLM Powered Multi-agent Framework for Autonomous CloudOps". The framework provides a flexible and extensible architecture for creating, managing, and orchestrating multiple AI agents to handle various tasks autonomously.

## Core Features

- **Agent Management**: Create, register, and manage multiple AI agents
- **Orchestration**: Orchestrate conversations and tasks across multiple agents
- **Memory Tools**: Integrate memory tools to maintain conversation context and history
- **Streaming Responses**: Support for streaming responses from agents
- **Extensibility**: Easily extend the framework with new agents, tools, and orchestrators

## Architecture Components

1. **Agents**
   - OpenAI Agent
   - Bedrock Agent
   - Ollama Agent
   - Remote Agent

2. **Orchestrators**
   - Simple Orchestrator
   - Multi-Agent Orchestrator
   - Task-based routing

3. **Tools System**
   - Memory Tool
   - Tool Registry
   - Custom tool support

For more details, refer to the paper at [arXiv](https://arxiv.org/abs/2501.08243).
