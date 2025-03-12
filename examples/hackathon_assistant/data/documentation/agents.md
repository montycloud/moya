# Moya Agents Documentation

## Agent Types

### OpenAI Agent
- Uses OpenAI's ChatCompletion API
- Environment-based API key configuration
- Streaming support
- Configuration via OpenAIAgentConfig

### Bedrock Agent
- AWS Bedrock integration
- Support for Claude and other models
- AWS credential management
- Streaming capabilities

### Ollama Agent
- Local model deployment
- Streaming support
- Custom model configuration
- Direct API integration

### Remote Agent
- Remote API communication
- Authentication support
- Streaming capabilities
- Error handling and reconnection

## Common Features
1. **Message Handling**
   - Synchronous responses
   - Streaming support
   - Error handling

2. **Tool Integration**
   - ToolRegistry support
   - Memory tool usage
   - Custom tool compatibility

3. **Configuration**
   - Model parameters
   - API settings
   - System prompts
