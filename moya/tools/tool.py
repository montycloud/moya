"""
Tool for Moya.

Describes a generic interface for a "tool" that an agent can discover and call.
Tools are provider-agnostic — each agent implementation is responsible for
converting the generic schema into the format required by its LLM provider.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, get_type_hints


@dataclass
class Tool:
    name: str
    description: Optional[str] = None
    function: Optional[Callable] = None
    parameters: Optional[Dict[str, Dict[str, Any]]] = None
    required: Optional[List[str]] = None
    # Optional metadata — does not affect runtime behaviour
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    deprecated: bool = False
    deprecation_message: Optional[str] = None
    allowed_agents: Optional[List[str]] = None

    def __post_init__(self):
        if self.function is None:
            raise ValueError("Function is required for a tool: ", self.name)

        docstring = self.function.__doc__ or ""

        if self.description is None:
            self.description = docstring.split("\n\n")[0].strip()

        _json_type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            dict: "object",
            list: "array",
            Any: "string",
        }

        if self.parameters is None:
            self.parameters = {}
            for line in docstring.split("\n"):
                if line.strip().startswith("- "):
                    parts = line.strip().split(":", 1)
                    if len(parts) == 2:
                        param_name = parts[0].strip().replace("- ", "").replace("Optional", "").strip()
                        if not param_name or param_name == "self":
                            continue
                        param_desc = parts[1].strip()
                        param_type = get_type_hints(self.function).get(param_name, Any)
                        self.parameters[param_name] = {
                            "type": _json_type_map.get(param_type, "string"),
                            "description": param_desc,
                        }
        else:
            self._validate_parameters(self.parameters)

    def _validate_parameters(self, parameters: Dict[str, Dict[str, Any]]) -> None:
        valid_types = {"string", "integer", "number", "boolean", "object", "array"}
        for param_name, param_info in parameters.items():
            if not isinstance(param_info, dict):
                raise ValueError(f"Parameter '{param_name}' info must be a dict")
            for key in ("type", "description"):
                if key not in param_info:
                    raise ValueError(f"Parameter '{param_name}' is missing required key: '{key}'")
            if param_info["type"] not in valid_types:
                raise ValueError(
                    f"Parameter '{param_name}' has invalid type '{param_info['type']}'. "
                    f"Must be one of: {', '.join(sorted(valid_types))}"
                )
