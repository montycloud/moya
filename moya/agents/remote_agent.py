"""
RemoteAgent for Moya.

An Agent that communicates with a remote API endpoint to generate responses.
"""

import requests
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Iterator
from moya.agents.base_agent import Agent, AgentConfig


@dataclass
class RemoteAgentConfig:
    """Configuration for RemoteAgent, separate from AgentConfig to avoid inheritance issues"""
    base_url: str
    auth_token: Optional[str] = None
    verify_ssl: bool = True
    system_prompt: Optional[str] = None


class RemoteAgent(Agent):
    """
    An agent that forwards requests to a remote API endpoint.
    """

    def __init__(
        self,
        agent_name: str,
        description: str,
        config: Optional[Dict[str, Any]] = None,
        tool_registry: Optional[Any] = None,
        agent_config: Optional[RemoteAgentConfig] = None,
    ):
        """
        Initialize a RemoteAgent.
        
        :param agent_name: Unique name for the agent
        :param description: Description of the agent's capabilities
        :param config: Optional configuration dictionary
        :param tool_registry: Optional ToolRegistry for tool support
        :param agent_config: Optional configuration for the RemoteAgent
        """
        super().__init__(
            agent_name=agent_name,
            agent_type="RemoteAgent",
            description=description,
            config=config,
            tool_registry=tool_registry
        )
        if not agent_config:
            raise ValueError("RemoteAgentConfig is required")
            
        self.agent_config = agent_config
        self.base_url = agent_config.base_url.rstrip('/')
        self.system_prompt = agent_config.system_prompt
        self.session = requests.Session()
        
        # Configure authentication if provided
        if agent_config.auth_token:
            self.session.headers.update({
                "Authorization": f"Bearer {agent_config.auth_token}"
            })
        
        # Configure SSL verification
        self.session.verify = agent_config.verify_ssl

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
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return "[RemoteAgent error: Authentication failed]"
            return f"[RemoteAgent error: {str(e)}]"
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
