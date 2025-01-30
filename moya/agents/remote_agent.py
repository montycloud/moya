"""
RemoteAgent for Moya.

An Agent that communicates with a remote API endpoint to generate responses.

"""
# TODO: setup agent authentication and error handling, use sseclient.


import requests
from typing import Any, Dict, Optional, Iterator
from moya.agents.base_agent import Agent

class RemoteAgent(Agent):
    """
    An agent that forwards requests to a remote API endpoint.
    """

    def __init__(
        self,
        agent_name: str,
        description: str,
        base_url: str,
        config: Optional[Dict[str, Any]] = None,
        tool_registry: Optional[Any] = None,
    ):
        """
        Initialize a RemoteAgent.
        
        :param agent_name: Unique name for the agent
        :param description: Description of the agent's capabilities
        :param base_url: Base URL of the remote API (e.g., "http://localhost:8000")
        :param config: Optional configuration dictionary
        :param tool_registry: Optional ToolRegistry for tool support
        """
        super().__init__(
            agent_name=agent_name,
            agent_type="RemoteAgent",
            description=description,
            config=config,
            tool_registry=tool_registry
        )
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def setup(self) -> None:
        """
        Set up the remote agent - test connection and configure session.
        """
        try:
            health_url = f"{self.base_url}/health"
            response = self.session.get(health_url)
            response.raise_for_status()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to remote agent at {self.base_url}: {str(e)}")

    def handle_message(self, message: str, **kwargs) -> str:
        """
        Send message to remote endpoint and get response.
        
        :param message: The message to process
        :param kwargs: Additional parameters to pass to the remote API
        :return: Response from the remote agent
        """
        try:
            endpoint = f"{self.base_url}/chat"
            data = {
                "message": message,
                "thread_id": kwargs.get("thread_id"),
                **kwargs
            }
            
            response = self.session.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()["response"]
            
        except Exception as e:
            return f"[RemoteAgent error: {str(e)}]"

    def handle_message_stream(self, message: str, **kwargs) -> Iterator[str]:
        """
        Send message to remote endpoint and stream the response.
        """
        try:
            endpoint = f"{self.base_url}/chat/stream"
            data = {
                "message": message,
                "thread_id": kwargs.get("thread_id"),
                **kwargs
            }
            
            with self.session.post(
                endpoint,
                json=data,
                stream=True,
                headers={"Accept": "text/event-stream"}
            ) as response:
                response.raise_for_status()
                current_text = ""
                
                for line in response.iter_lines(decode_unicode=True):
                    if line and line.startswith("data:"):
                        content = line[5:].strip()
                        if content and content != "done":
                            # Clean up content
                            clean_content = (
                                content
                                .encode('utf-8')
                                .decode('utf-8')
                                .replace('\u00A0', ' ')
                            )
                            
                            # Add to current text
                            current_text += clean_content
                            
                            # Find word boundaries
                            words = []
                            remaining = ""
                            
                            # Split into words while preserving punctuation
                            for word in current_text.split(' '):
                                if word:
                                    if any(c.isalnum() for c in word):
                                        words.append(word)
                                    else:
                                        # Handle punctuation
                                        if words:
                                            last_word = words[-1]
                                            words[-1] = last_word + word
                                        else:
                                            words.append(word)
                            
                            # If we have complete words, yield them
                            if words:
                                text_to_yield = ' '.join(words)
                                yield text_to_yield + ' '
                                current_text = ""
                
                # Yield any remaining text
                if current_text.strip():
                    yield current_text
                            
        except Exception as e:
            error_message = f"[RemoteAgent error: {str(e)}]"
            print(error_message)
            yield error_message

    def __del__(self):
        """Cleanup the session when the agent is destroyed."""
        if hasattr(self, 'session'):
            self.session.close()
