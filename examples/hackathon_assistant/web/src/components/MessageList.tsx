
import { useRef, useEffect } from 'react';
import { Message as MessageType } from '../lib/types';
import Message from './Message';
import { useToast } from '@/hooks/use-toast';

interface MessageListProps {
  messages: MessageType[];
}

const MessageList = ({ messages }: MessageListProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const handleRetry = (messageId: string) => {
    toast({
      title: "Retrying message",
      description: "Attempting to resend the message"
    });
    // In a real app, this would actually retry sending the message
  };

  // Auto-scroll to the bottom when new messages come in
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <div 
      ref={containerRef}
      role="log"
      aria-live="polite"
      className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin"
    >
      {messages.length === 0 ? (
        <div className="h-full flex items-center justify-center">
          <p className="text-muted-foreground text-center">
            Start a conversation or select a prompt to learn about Moya.
          </p>
        </div>
      ) : (
        messages.map((message, index) => (
          <Message 
            key={message.id} 
            message={message} 
            onRetry={() => handleRetry(message.id)}
            isFirst={index === 0} 
            isLast={index === messages.length - 1}
          />
        ))
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
