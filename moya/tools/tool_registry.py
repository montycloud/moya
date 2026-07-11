"""
ToolRegistry for Moya.

A centralized place where tools (e.g., MemoryTool) can be registered
and discovered by agents.
"""
import json
import time
from typing import Any, Dict, Optional, List, TYPE_CHECKING
from moya.tools.tool import Tool
from moya.utils.constants import LLMProviders

if TYPE_CHECKING:
    from moya.observability.event_bus import EventBus


class ToolRegistry:
    """
    Holds references to various tools and allows dynamic discovery
    by name. Agents can call 'get_tool("MemoryTool")' to retrieve
    and invoke the tool's methods.

    Optionally accepts an *event_bus* to emit ToolCalledEvent telemetry.
    """

    def __init__(self, event_bus: Optional["EventBus"] = None):
        self._tools: Dict[str, Tool] = {}
        self._event_bus = event_bus

    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool. If a tool with the same name exists, it gets overwritten.
        """
        self._tools[tool.name] = tool

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """
        Retrieve a registered tool by name.
        """
        return self._tools.get(tool_name)

    def get_tools(self) -> List[Tool]:
        """
        Returns all registered Tool objects.
        """
        return list(self._tools.values())

    def list_tools(self) -> List[str]:
        """
        Returns the names of all registered tools.
        """
        return list(self._tools.keys())

    def get_catalog(self) -> List[dict]:
        """
        Returns lightweight metadata for all registered tools — useful for
        discovery, documentation, and sharing the registry across agents.
        """
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters or {},
                "required": t.required or [],
            }
            for t in self._tools.values()
        ]
    
    
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
                t0 = time.monotonic()
                result = tool.function(**arguments)
                duration_ms = (time.monotonic() - t0) * 1000
                results.append({
                    "tool_call_id": tool_call.get("id", ""),
                    "name": tool_name,
                    "result": result
                })
                self._emit_tool_called(tool_name, arguments, duration_ms, True, None)
            except Exception as e:
                duration_ms = (time.monotonic() - t0) * 1000
                results.append({
                    "tool_call_id": tool_call.get("id", ""),
                    "name": tool_name,
                    "error": str(e)
                })
                self._emit_tool_called(tool_name, arguments, duration_ms, False, str(e))
                
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
            # Bedrock Converse API: response['output']['message']['content'] is a list
            # of content blocks; tool-use blocks look like:
            # {"toolUse": {"toolUseId": "...", "name": "...", "input": {...}}}
            content = []
            if isinstance(llm_response, dict):
                content = (
                    llm_response.get("output", {})
                    .get("message", {})
                    .get("content", [])
                )
            elif hasattr(llm_response, "toolUse"):
                # Legacy single-tool-use attribute
                tool_use = llm_response.toolUse
                return [{
                    "id": tool_use.get("toolUseId", ""),
                    "name": tool_use.get("name", ""),
                    "arguments": tool_use.get("input", tool_use.get("parameters", {})),
                }]

            tool_calls = []
            for block in content:
                if "toolUse" in block:
                    tu = block["toolUse"]
                    tool_calls.append({
                        "id": tu.get("toolUseId", ""),
                        "name": tu.get("name", ""),
                        "arguments": tu.get("input", {}),
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

    def _emit_tool_called(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        duration_ms: float,
        success: bool,
        error: Optional[str],
    ) -> None:
        if self._event_bus is None:
            return
        try:
            from moya.observability.events import ToolCalledEvent
            self._event_bus.publish(ToolCalledEvent(
                source="ToolRegistry",
                tool_name=tool_name,
                arguments=arguments,
                duration_ms=duration_ms,
                success=success,
                error=error,
            ))
        except Exception:
            pass
