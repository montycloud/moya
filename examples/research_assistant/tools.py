"""
Plain Python tools for the Research Assistant example.

These are ordinary functions with type hints and docstrings — MOYA turns them
into agent-callable tools automatically. They're deterministic and need no
network, so the example runs anywhere.
"""

# A tiny in-memory "knowledge base" the researcher can look things up in.
_KNOWLEDGE = {
    "quantum computing": (
        "Quantum computing uses qubits, which can be 0, 1, or a superposition of "
        "both. Entanglement links qubits so their states are correlated. This lets "
        "certain algorithms (Shor's, Grover's) outperform classical ones."
    ),
    "classical computing": (
        "Classical computing stores information in bits that are strictly 0 or 1 "
        "and processes them with deterministic logic gates."
    ),
    "climate change": (
        "Climate change is the long-term shift in temperatures and weather patterns, "
        "largely driven since the 1800s by burning fossil fuels which raises "
        "atmospheric CO2 and traps heat."
    ),
    "moya": (
        "MOYA is a Python framework for building multi-agent LLM systems: agents, "
        "tools, skills, memory, pipelines, delegation, MCP and A2A — all composable."
    ),
}

_RELATED = {
    "quantum computing": ["classical computing", "cryptography", "superposition"],
    "climate change": ["renewable energy", "carbon capture", "policy"],
    "moya": ["agents", "tools", "memory", "pipelines"],
}


def search_knowledge(topic: str) -> str:
    """
    Look up factual notes on a topic from the knowledge base.

    :param topic: The subject to look up (e.g. "quantum computing").
    :return: A short factual summary, or a not-found message.
    """
    return _KNOWLEDGE.get(
        topic.strip().lower(),
        f"No knowledge-base entry for '{topic}'. Answer from general knowledge and say so.",
    )


def list_related_topics(topic: str) -> str:
    """
    List topics related to the given topic.

    :param topic: The subject to find related topics for.
    :return: A comma-separated list of related topics.
    """
    related = _RELATED.get(topic.strip().lower())
    return ", ".join(related) if related else "No related topics found."
