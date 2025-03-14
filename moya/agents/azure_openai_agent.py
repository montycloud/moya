"""
OpenAIAgent for Moya.

An Agent that uses OpenAI's ChatCompletion or Completion API
to generate responses, pulling API key from the environment.
"""


import os
from openai import AzureOpenAI
from dataclasses import dataclass

from typing import Any, Dict, List, Optional
from moya.agents.base_agent import Agent, AgentConfig


@dataclass
class AzureOpenAIAgentConfig(AgentConfig):
    """
    Configuration data for an OpenAIAgent.
    """
    model_name: str = "gpt-4o"
    api_key: str = None
    tool_choice: Optional[str] = None

    api_base: Optional[str] = None
    api_version: Optional[str] = None
    organization: Optional[str] = None


class AzureOpenAIAgent(Agent):
    """
    A simple AzureOpenAI-based agent that uses the ChatCompletion API.
    """

    def __init__(
        self,
        config: AzureOpenAIAgentConfig 
    ):
        """
        :param agent_name: Unique name or identifier for the agent.
        :param description: A brief explanation of the agent's capabilities.
        :param model_name: The OpenAI model name (e.g., "gpt-3.5-turbo").
        :param config: Optional config dict (unused by default).
        :param tool_registry: Optional ToolRegistry to enable tool calling.
        :param config: Optional configuration for the agent.
        """
        super().__init__(config=config)
        self.model_name = config.model_name
        self.system_prompt = config.system_prompt
        self.tool_choice = config.tool_choice if config.tool_choice else None
        self.max_iterations = 5
        api_key = config.api_key if config.api_key else os.environ.get("AZURE_OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "AZURE_OPENAI_API_KEY is not found. Either set it in the environment or pass it in the agent config."
            )
        api_base = config.api_base if config.api_base else os.environ.get("AZURE_OPENAI_ENDPOINT")
        if not api_base:
            raise EnvironmentError(
                "AZURE_OPENAI_ENDPOINT is not found. Either set it in the environment or pass it in the agent config."
            )
        api_version = config.api_version if config.api_version else os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

        params = {
            "api_key": api_key,
            "azure_endpoint": api_base,
            "api_version": api_version
        }
        if config.organization:  
            params["organization"] = config.organization
        self.client = AzureOpenAI(
            **params
        )

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Discover tools available for this agent.
        """
        if not self.tool_registry:
            return None
        
        # Generate tool definitions for OpenAI ChatCompletion
        tools = [
            {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        name: {
                            "type": info["type"],
                            "description": info["description"]
                        } for name, info in tool.parameters.items()
                    },
                    "required": [
                        name for name, info in tool.parameters.items() 
                        if info.get("required", False)
                    ]
                }
            }
        }
        for tool in self.tool_registry.get_tools()
        ]
        return tools

    
    def handle_message(self, message: str, **kwargs) -> str:
        """
        Calls OpenAI ChatCompletion to handle the user's message.
        """
        return self.run_chat(message)

    def handle_message_stream(self, message: str, **kwargs):
        """
        Calls OpenAI ChatCompletion to handle the user's message with streaming support.
        """
        self.run_chat(message)

    def run_chat(self, user_message):
        """
        Handle a chat session with the user and resolve tool calls iteratively.
        
        Args:
            user_message (str): The initial message from the user.
        
        Returns:
            str: Final response after tool call processing.
        """
        conversation = [{"role": "user", "content": user_message}]
        iteration = 0

        while iteration < self.max_iterations:
            message = self.get_response(conversation)
            
            # Extract message content
            if isinstance(message, dict):
                content = message.get("content", "")
                tool_calls = message.get("tool_calls", [])
            else:
                content = message.content if message.content is not None else ""
                tool_calls = message.tool_calls if hasattr(message, "tool_calls") and message.tool_calls else []
                # Convert to list of dicts if it's not already
                if tool_calls and not isinstance(tool_calls[0], dict):
                    tool_calls = [tc.dict() for tc in tool_calls]
                    
            # Create assistant message entry
            entry = {"role": "assistant", "content": content}
            if tool_calls:
                entry["tool_calls"] = tool_calls
            conversation.append(entry)

            # Process tool calls if any
            if tool_calls:
                for tool_call in tool_calls:
                    tool_response = self.handle_tool_call(tool_call)
                    
                    conversation.append({
                            "role": "tool",
                            "tool_call_id": tool_call.get("id"),
                            "content": tool_response
                    })
                iteration += 1
            else:
                break

        final_message = conversation[-1].get("content", "")
        return final_message

    def get_response(self, conversation):
        """
        Generate a response via the OpenAI ChatCompletion API with tool call support.
        
        Args:
            conversation (list): Current chat messages.
        
        Returns:
            dict: Message from the assistant, which may include 'tool_calls'.
        """
        
        if self.is_streaming:
            tools_available = self.get_tool_definitions() or None
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=conversation,
                tools=tools_available,
                tool_choice=self.tool_choice if self.tool_registry else None,
                stream=True
            )
            response_text = ""
            tool_calls = []
            current_tool_call = None
            
            for chunk in response:
                delta = chunk.choices[0].delta
                if delta:
                    if delta.content is not None:
                        response_text += delta.content
                        print(delta.content, end="", flush=True)
                        
                    if delta.tool_calls:
                        for tool_call_delta in delta.tool_calls:
                            tool_call_index = tool_call_delta.index
                            
                            # Ensure we have enough slots in our tool_calls list
                            while len(tool_calls) <= tool_call_index:
                                tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                                
                            current_tool_call = tool_calls[tool_call_index]
                            
                            # Update tool call information from this chunk
                            if tool_call_delta.id:
                                current_tool_call["id"] = tool_call_delta.id
                                
                            if tool_call_delta.function:
                                if tool_call_delta.function.name:
                                    current_tool_call["function"]["name"] = tool_call_delta.function.name
                                    
                                if tool_call_delta.function.arguments:
                                    current_tool_call["function"]["arguments"] = (
                                        current_tool_call["function"].get("arguments", "") + 
                                        tool_call_delta.function.arguments
                                    )
            
            print()  # New line after streaming output
            result = {"content": response_text}
            if tool_calls:
                result["tool_calls"] = tool_calls
            return result
        else:
            tools_available = self.get_tool_definitions() or None
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=conversation,
                tools=tools_available,
                tool_choice=self.tool_choice if self.tool_registry else None
            )
            message = response.choices[0].message
            
            # Convert the response to a dict for uniform handling
            result = {"content": message.content or ""}
            
            if message.tool_calls:
                # Convert tool_calls to a list of dicts
                if isinstance(message.tool_calls, list):
                    if not isinstance(message.tool_calls[0], dict):
                        result["tool_calls"] = [tc.dict() for tc in message.tool_calls]
                    else:
                        result["tool_calls"] = message.tool_calls
                else:
                    result["tool_calls"] = [message.tool_calls.dict()]
                    
            return result

    def handle_tool_call(self, tool_call):
        """
        Execute the tool specified in the tool call.
        Implements tools: 'echo' and 'reverse'.
        
        Args:
            tool_call (dict): Contains 'id', 'type', and 'function' (with 'name' and 'arguments').
        
        Returns:
            str: The output from executing the tool.
        """        
        function_data = tool_call.get("function", {})
        name = function_data.get("name")
        
        # Parse arguments if provided; they are passed as a JSON string by the API
        import json
        try:
            args = json.loads(function_data.get("arguments", "{}"))
        except json.JSONDecodeError:
            args = {}

        tool = self.tool_registry.get_tool(name)
        if tool:
            result = tool.function(**args)
            return result

        return f"[Tool '{name}' not found]"

