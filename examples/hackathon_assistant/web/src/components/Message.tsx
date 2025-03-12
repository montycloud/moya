
import React from 'react';
import { Message as MessageType } from '../lib/types';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Check, Clock, AlertTriangle, Copy } from 'lucide-react';

interface MessageProps {
  message: MessageType;
}

const Message: React.FC<MessageProps> = ({ message }) => {
  const [copied, setCopied] = React.useState(false);
  
  const isUser = message.role === 'user';
  const formattedTime = formatDistanceToNow(new Date(message.timestamp), { addSuffix: true });
  
  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  const StatusIcon = () => {
    switch (message.status) {
      case 'sending':
        return <Clock className="h-3 w-3" />;
      case 'sent':
        return <Check className="h-3 w-3" />;
      case 'error':
        return <AlertTriangle className="h-3 w-3" />;
      default:
        return null;
    }
  };
  
  return (
    <div
      className={cn(
        "px-4 py-2 mb-4",
        isUser ? "self-end" : "self-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-message px-4 py-3 shadow-sm",
          isUser ? "ml-auto bg-primary text-primary-foreground" : "mr-auto bg-secondary text-secondary-foreground"
        )}
      >
        <div className="chat-message">
          <ReactMarkdown
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                
                return !inline && match ? (
                  <div className="relative code-block">
                    <div className="language-indicator">{match[1]}</div>
                    <button 
                      className="copy-button"
                      onClick={() => handleCopyCode(String(children).replace(/\n$/, ''))}
                    >
                      {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </button>
                    <SyntaxHighlighter
                      language={match[1]}
                      style={atomDark}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  </div>
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              }
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
      
      <div
        className={cn(
          "flex items-center text-xs text-muted-foreground mt-1",
          isUser ? "justify-end" : "justify-start"
        )}
      >
        <StatusIcon />
        <span className="ml-1">{formattedTime}</span>
      </div>
    </div>
  );
};

export default Message;
