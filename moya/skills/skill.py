"""
Skill — a named, reusable agent capability.

A Skill bundles a prompt snippet and/or a set of tools (and optionally a
custom execution handler) under a single name.  Attaching a Skill to an agent
automatically enriches its system prompt, registers its tools, and ensures
all skill dependencies are also attached.

Usage::

    from moya.skills import Skill
    from moya.tools.tool import Tool

    def search(query: str) -> str:
        \"\"\"Search the web.
        Parameters:
        - query: The search query.
        \"\"\"
        ...

    web_search = Skill(
        name="web_search",
        description="Search the web for up-to-date information.",
        version="1.0.0",
        prompt_snippet="You have access to a web search tool. Use it for current facts.",
        tools_factory=lambda: [Tool(name="search", function=search)],
        input_schema={"query": {"type": "string", "description": "Search terms"}},
        output_schema={"result": {"type": "string"}},
    )

    # A skill that requires web_search to already be attached
    summariser = Skill(
        name="summarise_search",
        description="Search and summarise results.",
        dependencies=["web_search"],
        prompt_snippet="When asked to summarise a topic, first search then condense.",
    )
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Skill:
    """
    Describes a reusable agent capability.

    Attributes:
        name:            Unique identifier (e.g. ``"web_search"``).
        description:     Human-readable description used for discovery.
        version:         Semantic version string (e.g. ``"1.2.0"``).
        tags:            Optional labels for filtering (e.g. ``["search", "web"]``).
        prompt_snippet:  Text appended to the agent's system prompt when attached.
        tools_factory:   Callable returning a list of Tool objects to register.
        handler:         Optional callable invoked when this skill is executed
                         programmatically (beyond prompt enrichment).
                         Signature: ``handler(input: dict) -> dict``.
        input_schema:    JSON-Schema-style dict describing expected inputs.
        output_schema:   JSON-Schema-style dict describing outputs.
        dependencies:    Names of other skills that must be attached before this
                         one.  The registry resolves these transitively.
    """

    name: str
    description: str
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    prompt_snippet: Optional[str] = None
    tools_factory: Optional[Callable[[], List[Any]]] = None
    handler: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute this skill's handler with *input_data*.

        Raises ``NotImplementedError`` when no handler is defined.
        """
        if self.handler is None:
            raise NotImplementedError(
                f"Skill '{self.name}' has no handler. "
                "Set 'handler' to make it programmatically executable."
            )
        return self.handler(input_data)
