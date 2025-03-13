"""
ToolRegistry for Moya.

A centralized place where tools (e.g., MemoryTool) can be registered
and discovered by agents.
"""
import json
from typing import Any, Dict, Optional, List
from moya.tools.base_tool import BaseTool
from moya.utils.constants import LLMProviders


class ToolRegistry:
    """
    Holds references to various tools and allows dynamic discovery
    by name. Agents can call 'get_tool("MemoryTool")' to retrieve
    and invoke the tool's methods.
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool. If a tool with the same name exists, it gets overwritten.
        """
        self._tools[tool.name] = tool

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Retrieve a registered tool by name.
        """
        return self._tools.get(tool_name)

    def get_tools(self) -> List[BaseTool]:
        """
        Returns the tool definition in a format compatible with the specified LLM provider.
        
        :param llm_provider: LLM provider name (e.g., 'openai', 'bedrock', 'ollama')
        :return: Tool definition as a dictionary
        """
        return self._tools.values() or []
    
    
    def handle_tool_call(self, llm_response: Any, llm_provider: str) -> Dict[str, Any]:
        """
        Handles tool calling based on the LLM response.
        
        :param llm_response: Response from the LLM
        :param llm_provider: LLM provider name (e.g., 'openai', 'bedrock', 'ollama')
        :return: Result of the tool call or None if no tool call was needed
        """
        
        tool_calls = self._extract_tool_calls(llm_response, llm_provider)
        
        if not tool_calls:
            return None
            
        results = []
        for tool_call in tool_calls:
            # Execute function with the given arguments
            tool_name = tool_call.get("name")
            arguments = tool_call.get("arguments", {})
            
            tool = self.get_tool(tool_name)
            if tool is None:
                results.append({
                    "tool_call_id": tool_call.get("id", ""),
                    "name": tool_name,
                    "error": f"Tool '{tool_name}' not found in the registry"
                })
                continue
                
            if tool.function is None:
                results.append({
                    "tool_call_id": tool_call.get("id", ""),
                    "name": tool_name,
                    "error": f"Tool '{tool_name}' does not have an implementation function"
                })
                continue
                
            try:
                result = tool.function(**arguments)
                results.append({
                    "tool_call_id": tool_call.get("id", ""),
                    "name": tool_name,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "tool_call_id": tool_call.get("id", ""),
                    "name": tool_name,
                    "error": str(e)
                })
                
        return results
    
    def _extract_tool_calls(self, llm_response: Any, llm_provider: str) -> List[Dict[str, Any]]:
        """
        Extracts tool calls from the LLM response based on provider format.
        
        :param llm_response: Response from the LLM
        :param llm_provider: LLM provider name
        :return: List of tool calls with name, arguments, and optional ID
        """
        
        if llm_provider == LLMProviders.OPENAI:
            # OpenAI format
            message = llm_response.choices[0].message
            if not hasattr(message, 'tool_calls') or not message.tool_calls: 
                return []
                
            tool_calls = []
            for call in message.tool_calls:
                try:
                    arguments = json.loads(call.function.arguments)
                except:
                    arguments = {}
                    
                tool_calls.append({
                    "id": call.id,
                    "name": call.function.name,
                    "arguments": arguments
                })
            return tool_calls
                
        elif llm_provider == LLMProviders.BEDROCK:
            # Bedrock format varies by model
            # This is a simplified example that may need to be adjusted
            if not hasattr(llm_response, 'tool_use') and not hasattr(llm_response, 'toolUse'):
                return []
                
            tool_calls = []
            if hasattr(llm_response, 'tool_use'):
                for call in llm_response.tool_calls:
                    tool_calls.append({
                        "id": tool_use.get("toolUseId"),
                        "name": call.get("name"),
                        "arguments": call.get("parameters", {})
                    })
            elif hasattr(llm_response, 'toolUse'):
                tool_use = llm_response.toolUse
                tool_calls.append({
                    "id": tool_use.get("toolUseId"),
                    "name": tool_use.get("name"),
                    "arguments": tool_use.get("parameters", {})
                })
                
            return tool_calls
            
        elif llm_provider == LLMProviders.OLLAMA:
            # Ollama may follow a similar structure to OpenAI
            # This would need to be adjusted based on Ollama's actual response format
            if not isinstance(llm_response, dict) or "tool_calls" not in llm_response:
                return []
                
            tool_calls = []
            for call in llm_response.get("tool_calls", []):
                tool_calls.append({
                    "name": call.get("name"),
                    "arguments": call.get("arguments", {})
                })
            return tool_calls
            
        return []
