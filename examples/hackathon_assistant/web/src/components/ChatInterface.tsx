
import { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Message, ConnectionState } from '../lib/types';
import MessageList from './MessageList';
import InputArea from './InputArea';
import { toast } from '@/hooks/use-toast';
import { Button } from "@/components/ui/button";
import { ArrowLeft, RotateCcw } from 'lucide-react';

interface ChatInterfaceProps {
  initialPrompt: string | null;
  onReset: () => void;
}

const ChatInterface = ({ initialPrompt, onReset }: ChatInterfaceProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>({ 
    status: 'connected',
    message: '' 
  });
  const bottomRef = useRef<HTMLDivElement>(null);

  // Mock function to simulate message exchange - in production, this would call an actual API
  const mockMessageResponse = async (content: string): Promise<Message> => {
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Mock responses based on keywords in the prompt
    let response = "I'll help you understand more about the Moya framework. What specific aspect would you like to know about?";
    
    if (content.toLowerCase().includes('install') || content.toLowerCase().includes('setup')) {
      response = "To install Moya, you need to run:\n\n```bash\npip install moya-framework\n```\n\nThen you can initialize a new project with:\n\n```bash\nmoya init my-project\ncd my-project\n```\n\nThis creates a basic project structure with example configurations.";
    } else if (content.toLowerCase().includes('agent')) {
      response = "Moya's agent system is built around specialized AI agents for different tasks. A basic agent configuration looks like this:\n\n```python\nfrom moya import Agent\n\nmy_agent = Agent(\n    name=\"task_agent\",\n    model=\"gpt-4\",\n    system_prompt=\"You are a specialized CloudOps automation agent.\"\n)\n```\n\nAgents can communicate with each other and access registered tools.";
    } else if (content.toLowerCase().includes('architecture')) {
      response = "Moya uses a multi-agent architecture where different agents collaborate to solve complex tasks. The core components include:\n\n1. **Agent Registry** - Manages all available agents\n2. **Tool Registry** - Contains all tools agents can use\n3. **Memory System** - Provides short and long-term memory\n4. **Orchestrator** - Coordinates agent collaboration\n5. **Execution Engine** - Runs agent-generated code safely\n\nThis architecture allows for specialized agents to work together efficiently.";
    }
    
    return {
      id: uuidv4(),
      role: 'assistant',
      content: response,
      timestamp: new Date(),
      status: 'sent'
    };
  };

  // Send a message
  const sendMessage = async (content: string) => {
    if (!content.trim()) return;
    
    // Add user message
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date(),
      status: 'sending'
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsProcessing(true);
    
    try {
      // Update user message status to sent
      setMessages(prev => 
        prev.map(msg => 
          msg.id === userMessage.id ? { ...msg, status: 'sent' } : msg
        )
      );
      
      // Get AI response
      const aiMessage = await mockMessageResponse(content);
      setMessages(prev => [...prev, aiMessage]);
      
      // Success toast for demonstration
      // toast({ title: "Message sent successfully" });
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Update user message status to error
      setMessages(prev => 
        prev.map(msg => 
          msg.id === userMessage.id ? { ...msg, status: 'error' } : msg
        )
      );
      
      // Show error toast
      toast({ 
        title: "Failed to send message", 
        description: "Please try again", 
        variant: "destructive" 
      });
      
      // Update connection state
      setConnectionState({
        status: 'error',
        message: 'Could not connect to server'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle initial prompt
  useEffect(() => {
    if (initialPrompt) {
      sendMessage(initialPrompt);
    }
  }, [initialPrompt]);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Clear chat
  const clearChat = () => {
    setMessages([]);
  };

  // Retry connection
  const retryConnection = () => {
    setConnectionState({ status: 'loading', message: 'Reconnecting...' });
    
    // Simulate reconnection attempt
    setTimeout(() => {
      setConnectionState({ status: 'connected', message: '' });
      toast({ title: "Connection restored" });
    }, 1500);
  };

  return (
    <div className="flex flex-col w-full animate-fade-in">
      <div className="flex justify-between items-center mb-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={onReset}
          className="text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to prompts
        </Button>
        
        <div className="flex space-x-2">
          {messages.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={clearChat}
              aria-label="Clear chat history"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Clear chat
            </Button>
          )}
        </div>
      </div>
      
      {connectionState.status === 'error' && (
        <div className="bg-destructive/10 text-destructive rounded-md px-4 py-3 mb-4 flex justify-between items-center">
          <span>{connectionState.message}</span>
          <Button size="sm" onClick={retryConnection}>Reconnect</Button>
        </div>
      )}
      
      <div className="h-chat-area flex flex-col overflow-hidden rounded-lg border border-border glass-morphism">
        <MessageList messages={messages} />
        <div ref={bottomRef} />
        <InputArea 
          onSendMessage={sendMessage} 
          isProcessing={isProcessing} 
          disabled={connectionState.status !== 'connected'}
        />
      </div>
    </div>
  );
};

export default ChatInterface;
