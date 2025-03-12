
import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Send, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface InputAreaProps {
  onSendMessage: (message: string) => void;
  isProcessing: boolean;
  disabled?: boolean;
}

const InputArea = ({ onSendMessage, isProcessing, disabled = false }: InputAreaProps) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isProcessing && !disabled) {
      onSendMessage(message);
      setMessage('');
      
      // Reset textarea height after sending
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };
  
  // Auto-focus the input field when the component mounts
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isProcessing]);
  
  // Auto-resize textarea as user types
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const textarea = e.target;
    setMessage(textarea.value);
    
    // Reset height to calculate it properly
    textarea.style.height = 'auto';
    
    // Set the height based on scrollHeight (with a max height)
    const maxHeight = 120; // Maximum height in pixels
    textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`;
  };
  
  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
    
    // Clear on Escape
    if (e.key === 'Escape') {
      setMessage('');
      textareaRef.current?.focus();
      
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };
  
  return (
    <form 
      onSubmit={handleSubmit}
      role="form"
      aria-label="Message input form"
      className={cn(
        "h-auto min-h-input-area flex items-end p-4 border-t border-border bg-background/70 backdrop-blur-sm",
        disabled && "opacity-60"
      )}
    >
      <div className="relative flex-1 mr-2">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleTextareaChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask about Moya framework..."
          disabled={disabled || isProcessing}
          rows={1}
          className="w-full min-h-[44px] max-h-[120px] py-3 px-4 pr-10 rounded-full bg-background/80 border border-input focus:border-ring focus:ring-1 focus:ring-ring focus-visible:outline-none resize-none transition-all shadow-sm"
          aria-label="Message input"
        />
      </div>
      
      <Button
        type="submit"
        disabled={!message.trim() || isProcessing || disabled}
        className="h-11 w-11 rounded-full p-0 flex items-center justify-center shadow-md hover:shadow-lg transition-all"
        aria-label="Send message"
      >
        {isProcessing ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : (
          <Send className="h-5 w-5" />
        )}
      </Button>
    </form>
  );
};

export default InputArea;
