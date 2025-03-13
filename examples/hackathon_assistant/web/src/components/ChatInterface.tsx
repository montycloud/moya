import { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Message, ConnectionState } from '../lib/types';
import MessageList from './MessageList';
import InputArea from './InputArea';
import { toast } from '@/hooks/use-toast';
import { Button } from "@/components/ui/button";
import { ArrowLeft, RotateCcw } from 'lucide-react';
import { submitMessage, getResponseStream } from '../lib/api';

const ChatInterface = ({ initialPrompt, onReset }: ChatInterfaceProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    status: 'connected',
    message: ''
  });
  const bottomRef = useRef<HTMLDivElement>(null);
  const [threadId] = useState(`chat_${uuidv4()}`);

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;
    
    const messageId = uuidv4();
    const userMessage: Message = {
      id: messageId,
      role: 'user',
      content,
      timestamp: new Date(),
      status: 'sending'
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsProcessing(true);

    let eventSource: EventSource | null = null;
    
    try {
      // Update user message status first
      setMessages(prev => 
        prev.map(msg => 
          msg.id === messageId ? { ...msg, status: 'sent' } : msg
        )
      );

      const assistantId = uuidv4();
      // Add assistant message placeholder
      setMessages(prev => [...prev, {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        status: 'streaming'
      }]);

      eventSource = getResponseStream(content);
      let accumulatedContent = '';

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.content) {
            accumulatedContent += data.content;
            setMessages(prev => 
              prev.map(msg =>
                msg.id === assistantId 
                  ? { 
                      ...msg, 
                      content: accumulatedContent,
                      status: 'streaming'
                    }
                  : msg
              )
            );
          }
        } catch (e) {
          console.error('Error parsing SSE data:', e);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        if (eventSource) {
          eventSource.close();
        }
        
        // Only update message status, don't remove it
        setMessages(prev =>
          prev.map(msg =>
            msg.id === assistantId 
              ? { ...msg, status: 'sent' }
              : msg
          )
        );
        setIsProcessing(false);
      };

      // Cleanup function
      return () => {
        if (eventSource) {
          console.log('Cleaning up EventSource');
          eventSource.close();
        }
      };

    } catch (error) {
      console.error('Error sending message:', error);
      toast({
        title: "Failed to send message",
        description: "Please try again",
        variant: "destructive"
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
