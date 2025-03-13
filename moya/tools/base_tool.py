"""
BaseTool for Moya.

Describes a generic interface for a "tool" that an agent can discover and call.
"""

import abc
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, get_type_hints
import logging

@dataclass
class BaseTool():
    name: str
    description: Optional[str] = None
    function: Optional[Callable] = None
    parameters: Optional[Dict[str, Dict[str, Any]]] = None
    required: Optional[List[str]] = None

    def __post_init__(self):
        if self.function is None:
            raise ValueError("Function is required for a tool: ", self.name)
        
        # Use function docstring to extract optional parameters if not provided
        # This is the standard docstring format for Python functions:
        #     def my_function(param1: str, param2: int) -> str:
        #         """
        #         My function description.
        #
        #         Parameters:
        #         - param1: Description of param1. 
        #         - param2: Description of param2.
        #
        #         Returns:
        #         - Description of the return value.
        #         """
        docstring = self.function.__doc__ or ""

        if self.description is None:
            self.description = docstring.split("\n\n")[0].strip()

        json_type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            dict: "object",
            list: "array",
            Any: "string"
        }
        
        if self.parameters is None:
            self.parameters = {}
            for line in docstring.split("\n"):
                if line.strip().startswith("- "):
                    parts = line.strip().split(":")
                    if len(parts) == 2:
                        param_name, param_desc = parts
                        param_name = param_name.strip().replace("- ", "")
                        if param_name and param_name == "self":
                            continue

                        if "Optional" in param_name:
                            # Remove "Optional" from parameter name
                            param_name = param_name.replace("Optional", "").strip()
                    
                        param_desc = param_desc.strip()
                        param_type = get_type_hints(self.function).get(param_name, Any)
                        param_json_type = json_type_map.get(param_type, "string")

                        self.parameters[param_name] = {
                            "type": param_json_type,
                            "description": param_desc
                        }
        else:
        # Validate parameters format if provided
            self._validate_parameters(self.parameters)


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