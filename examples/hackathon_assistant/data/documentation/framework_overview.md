# Moya Framework Overview

## Core Components

### 1. Agents
- Base abstract agent class with standard interface
- Supported Agent Types:
  - OpenAI Agent
  - Bedrock Agent
  - Ollama Agent
  - Remote Agent

### 2. Orchestrators
- **BaseOrchestrator**: Abstract orchestration interface
- **SimpleOrchestrator**: Single-agent message routing
- **MultiAgentOrchestrator**: Intelligent multi-agent coordination

### 3. Memory System
- Thread-based conversation storage
- Message tracking and retrieval
- Support for conversation context

### 4. Tools System
- **ToolRegistry**: Central tool management
- **MemoryTool**: Conversation memory operations
- Extensible tool interface

## Key Features
1. **Agent Management**
   - Dynamic agent registration
   - Flexible agent configuration
   - Multi-agent coordination

2. **Memory Management**
   - Thread-based conversations
   - Context preservation
   - Message history tracking

3. **Tool Integration**
   - Pluggable tool system
   - Memory tools
   - Custom tool support
