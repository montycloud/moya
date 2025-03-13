const API_BASE_URL = 'http://localhost:8000';

export const submitMessage = async (content: string, threadId: string = 'default') => {
  const params = new URLSearchParams({ message: content });
  const response = await fetch(`${API_BASE_URL}/chat/stream?${params.toString()}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    },
  });
  
  if (!response.ok) {
    throw new Error('Failed to send message');
  }
  
  return response;
};

export const fetchStarterPrompts = async () => {
  const response = await fetch(`${API_BASE_URL}/starter-prompts`);
  if (!response.ok) {
    throw new Error('Failed to fetch prompts');
  }
  return response.json();
};

export const getResponseStream = (content: string): EventSource => {
  const params = new URLSearchParams({ message: content });
  return new EventSource(`${API_BASE_URL}/chat/stream?${params.toString()}`);
};

export const API_ENDPOINTS = {
  CHAT_STREAM: `${API_BASE_URL}/chat/stream`,
  STARTER_PROMPTS: `${API_BASE_URL}/starter-prompts`,
};
