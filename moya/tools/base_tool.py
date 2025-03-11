"""
BaseTool for Moya.

Describes a generic interface for a "tool" that an agent can discover and call.
"""

import abc
from typing import Any, Callable, Dict, List, Optional, Union


class BaseTool(abc.ABC):
    """
    Abstract base class for all Moya tools.
    Tools are callable utilities that agents can invoke (e.g., MemoryTool, WebSearchTool).
    """

    def __init__(
        self, 
        name: str, 
        description: str, 
        function: Optional[Callable] = None,
        parameters: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        """
        :param name: Unique name for the tool (e.g., 'MemoryTool').
        :param description: Short explanation of the tool's functionality.
        :param function: Callable that implements the tool's logic.
        :param parameters: Dictionary of parameters the function expects.
            Format: {
                "param_name": {
                    "type": "string|integer|number|boolean|object|array",
                    "description": "Parameter description",
                    "required": True|False
                }
            }
        """
        self._name = name
        self._description = description
        self._function = function
        
        # Validate parameters format if provided
        if parameters is not None:
            self._validate_parameters(parameters)
        self._parameters = parameters or {}

    @property
    def name(self) -> str:
        """
        Returns the name of the tool.
        """
        return self._name
    
    @property
    def description(self) -> str:
        """
        Returns the description of the tool.
        """
        return self._description   
    
    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns the parameters of the tool.
        """
        return self._parameters
    


    def _validate_parameters(self, parameters: Dict[str, Dict[str, Any]]) -> None:
        """
        Validates the parameters dictionary format.
        
        :param parameters: Dictionary of parameters to validate.
        :raises ValueError: If the parameters dictionary is not correctly formatted.
        """
        for param_name, param_info in parameters.items():
            if not isinstance(param_info, dict):
                raise ValueError(f"Parameter {param_name} info must be a dictionary")
            
            required_keys = ["type", "description"]
            for key in required_keys:
                if key not in param_info:
                    raise ValueError(f"Parameter {param_name} missing required info: {key}")
            
            # Validate type
            valid_types = ["string", "integer", "number", "boolean", "object", "array"]
            if param_info["type"] not in valid_types:
                raise ValueError(f"Parameter {param_name} has invalid type. Must be one of: {', '.join(valid_types)}")

    def get_bedrock_definition(self) -> Dict[str, Any]:
        """
        Returns the tool definition in a format compatible with Bedrock.
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    name: {
                        "type": info["type"],
                        "description": info["description"]
                    } for name, info in self.parameters.items()
                },
                "required": [
                    name for name, info in self.parameters.items() 
                    if info.get("required", False)
                ]
            }
        }
    
    def get_openai_definition(self) -> Dict[str, Any]:
        """
        Returns the tool definition in a format compatible with OpenAI.
        """
        return {
            "name": self.name,
            "description": self.description,
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        name: {
                            "type": info["type"],
                            "description": info["description"]
                        } for name, info in self.parameters.items()
                    },
                    "required": [
                        name for name, info in self.parameters.items() 
                        if info.get("required", False)
                    ]
                }
            }
        }
    
    def get_ollama_definition(self) -> Dict[str, Any]:
        """
        Returns the tool definition in a format compatible with Ollama.
        """
        # Ollama follows OpenAI format
        return self.get_openai_definition()