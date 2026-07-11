"""
MCP Server example — expose MOYA tools as an MCP-compliant server.

Run this script directly and it starts an MCP server on stdio.
Another process (or quick_start_mcp_client.py) can connect to it
using MCPClient.from_subprocess().

Usage::

    python3 examples/quick_start_mcp_server.py

The server blocks until killed. It serves three tools:
  - word_count  : count words in text
  - sentiment   : classify text as positive/negative/neutral
  - reverse_text: reverse text word-by-word
"""

from moya.mcp import MCPServer
from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry


# ---------------------------------------------------------------------------
# Define tools
# ---------------------------------------------------------------------------

def word_count(text: str) -> str:
    """Count the words in a piece of text.

    Parameters:
    - text: The text to count words in.
    """
    count = len(text.split())
    return f"{count} words"


def sentiment(text: str) -> str:
    """Classify text sentiment as positive, negative, or neutral.

    Parameters:
    - text: The text to classify.
    """
    positive_words = {"great", "good", "excellent", "wonderful", "love", "best", "happy", "fantastic"}
    negative_words = {"bad", "terrible", "awful", "hate", "worst", "horrible", "poor", "sad"}
    words = set(text.lower().split())
    pos = len(words & positive_words)
    neg = len(words & negative_words)
    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    return "neutral"


def reverse_text(text: str) -> str:
    """Reverse a piece of text word by word.

    Parameters:
    - text: The text to reverse.
    """
    return " ".join(text.split()[::-1])


# ---------------------------------------------------------------------------
# Build registry and start server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    registry = ToolRegistry()
    registry.register_tool(Tool(name="word_count", function=word_count))
    registry.register_tool(Tool(name="sentiment", function=sentiment))
    registry.register_tool(Tool(name="reverse_text", function=reverse_text))

    server = MCPServer(name="text_tools", tool_registry=registry)
    server.run()   # blocks — serves MCP requests over stdio
