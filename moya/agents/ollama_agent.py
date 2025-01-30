"""
OllamaAgent for Moya.

An Agent that uses Ollama's API to generate responses using locally hosted models.
"""

import requests
import json
from typing import Any, Dict, Optional
from moya.agents.base_agent import Agent
from ..messages.voice_message import VoiceMessage


class OllamaAgent(Agent):
    """
    A simple Ollama-based agent that uses the local Ollama API.
    """

    def __init__(
        self,
        agent_name: str,
        description: str,
        model_name: str = "llama2",
        config: Optional[Dict[str, Any]] = None,
        tool_registry: Optional[Any] = None,
        system_prompt: str = "You are a helpful AI assistant.",
        base_url: str = "http://localhost:11434"
    ):
        """
        :param agent_name: Unique name or identifier for the agent.
        :param description: A brief explanation of the agent's capabilities.
        :param model_name: The Ollama model name (e.g., "llama2", "mistral").
        :param config: Optional config dict (unused by default).
        :param tool_registry: Optional ToolRegistry to enable tool calling.
        :param system_prompt: Default system prompt for context.
        :param base_url: Ollama API base URL.
        """
        super().__init__(
            agent_name=agent_name,
            agent_type="OllamaAgent",
            description=description,
            config=config,
            tool_registry=tool_registry
        )
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.base_url = base_url.rstrip('/')

    def setup(self) -> None:
        """
        Verify Ollama server is accessible.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                raise ConnectionError("Unable to connect to Ollama server")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Ollama server: {str(e)}")

    def handle_message(self, message: str, **kwargs) -> str:
        """
        Calls Ollama API to handle the user's message.
        """
        try:
            # Combine system prompt and user message
            prompt = f"{self.system_prompt}\n\nUser: {message}\nAssistant:"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            return f"[OllamaAgent error: {str(e)}]"

    def handle_message_stream(self, message: str, **kwargs):
        """
        Calls Ollama API to handle the user's message with streaming support.
        """
        try:
            # Combine system prompt and user message
            prompt = f"{self.system_prompt}\n\nUser: {message}\nAssistant:"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": True
                },
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        if "response" in chunk:
                            yield chunk["response"]
                    except json.JSONDecodeError:
                        continue
                            
        except Exception as e:
            error_message = f"[OllamaAgent error: {str(e)}]"
            print(error_message)
            yield error_message

    def handle_voice(self, voice_message: VoiceMessage) -> str:
        """Process a voice message by converting it to text and handling the text."""
        text = self.speech_to_text(voice_message)
        return self.handle_message(text)
    
    def text_to_speech(self, text: str) -> VoiceMessage:
        """
        Convert text to speech using Ollama's TTS capability if available.
        Note: This is a placeholder - implement when Ollama adds TTS support.
        """
        raise NotImplementedError("Text-to-speech not yet supported by Ollama")
    
    def speech_to_text(self, voice_message: VoiceMessage) -> str:
        """
        Convert speech to text using Ollama's STT capability if available.
        Note: This is a placeholder - implement when Ollama adds STT support.
        """
        raise NotImplementedError("Speech-to-text not yet supported by Ollama")
