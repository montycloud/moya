"""
Backend configuration for the Startup Idea Validator.

Priority:
  - OPENAI_API_KEY set  →  OpenAI (gpt-4o-mini)
  - otherwise           →  Ollama (llama3.1 @ localhost:11434)

Override any value with the corresponding environment variable.
"""

import os

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1")

USE_OPENAI: bool = bool(OPENAI_API_KEY)

AGENT_TYPE: str = "openai" if USE_OPENAI else "ollama"
MODEL_NAME: str = OPENAI_MODEL if USE_OPENAI else OLLAMA_MODEL

MAX_DELEGATION_DEPTH: int = 3


def agent_extra_kwargs() -> dict:
    """Return agent-type-specific constructor kwargs for SubAgentSpec.extra_kwargs."""
    if USE_OPENAI:
        return {"api_key": OPENAI_API_KEY, "model_name": MODEL_NAME}
    return {"model_name": MODEL_NAME, "base_url": OLLAMA_BASE_URL}
