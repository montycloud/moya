"""
GeminiAgent for Moya.

An Agent that uses Google's Gemini API to generate responses.
"""

import os
import google.generativeai as genai
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Iterator
from moya.agents.base_agent import Agent, AgentConfig


@dataclass
class GeminiAgentConfig(AgentConfig):
    """
    Configuration data for a GeminiAgent.
    """
    model_name: str = "gemini-1.5-flash"
    api_key: str = None
    generation_config: Optional[Dict[str, Any]] = None


class GeminiAgent(Agent):
    """
    A simple Google Gemini-based agent that uses the Gemini API.
    """

    def __init__(
        self,
        config: GeminiAgentConfig
    ):
        """
        Initialize the GeminiAgent.

        :param config: Configuration for the agent.
        """
        super().__init__(config=config)
        self.model_name = config.model_name
        
        if not config.api_key:
            raise ValueError("Google API key is required for GeminiAgent.")
            
        # googlegenai initialization
        genai.configure(api_key=config.api_key)
        
        # generation config
        self.generation_config = config.generation_config or {
            "temperature": self.llm_config.get("temperature", 0.7),
            "top_p": self.llm_config.get("top_p", 1.0),
            "top_k": self.llm_config.get("top_k", 40),
            "max_output_tokens": self.llm_config.get("max_tokens", 2048),
        }
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config
        )
        self.system_prompt = config.system_prompt
        # conversation per thread id
        self.conversations = {}


    def setup(self) -> None:
        """
        Set up the agent (check API connectivity, etc.).
        """
        try:
            # api test
            response = self.model.generate_content("test")
            if not response:
                raise Exception("Unable to connect to Gemini API")
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Gemini client: {str(e)}")


    def _get_conversation(self, thread_id):
        """
        Get or create a conversation for a specific thread.
        """
        if thread_id not in self.conversations:
            # Start new conversation with system prompt
            convo = self.model.start_chat(history=[
                {"role": "user", "parts": [self.system_prompt]},
                {"role": "model", "parts": ["I understand. I'll help you."]}
            ])
            self.conversations[thread_id] = convo
            
        return self.conversations[thread_id]
    

    def handle_message(self, message: str, **kwargs) -> str:
        """
        Calls the Gemini API to handle the user's message.
        """
        thread_id = kwargs.get("thread_id", "default")
        
        try:
            # conversation id of this thread
            convo = self._get_conversation(thread_id)
            
            # feed context to memory if free
            if self.memory:
                previous_messages = self.get_last_n_messages(thread_id, n=5)
                if previous_messages:
                    context = self._format_conversation_context(previous_messages)
                    message = f"{context}\nCurrent user message: {message}"
            
            response = convo.send_message(message)
            
            return response.text

        except Exception as e:
            return f"[GeminiAgent error: {str(e)}]"

    def handle_message_stream(self, message: str, **kwargs):
        """
        Calls the Gemini API to handle the user's message with streaming support.
        """
        thread_id = kwargs.get("thread_id", "default")
        
        try:
            # create conversation
            convo = self._get_conversation(thread_id)
            
            # context from memory ( if available)
            if self.memory:
                previous_messages = self.get_last_n_messages(thread_id, n=5)
                if previous_messages:
                    context = self._format_conversation_context(previous_messages)
                    message = f"{context}\nCurrent user message: {message}"
            
            response = convo.send_message(message, stream=True)
            
            response_text = ""
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    response_text += chunk.text

        except Exception as e:
            error_message = f"[GeminiAgent error: {str(e)}]"
            print(error_message)
            yield error_message
            
    def _format_conversation_context(self, messages):
        """Format conversation history for context."""
        context = "\nPrevious conversation:\n"
        for msg in messages:
            sender = "User" if msg["sender"] == "user" else "Assistant"
            context += f"{sender}: {msg['content']}\n"
        return context
