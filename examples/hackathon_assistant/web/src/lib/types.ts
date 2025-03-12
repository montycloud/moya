
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  status: 'sending' | 'sent' | 'error';
}

export interface Prompt {
  text: string;
}

export interface PromptCategory {
  title: string;
  description: string;
  prompts: Prompt[];
}

export interface ConnectionState {
  status: 'connected' | 'loading' | 'error';
  message: string;
}
