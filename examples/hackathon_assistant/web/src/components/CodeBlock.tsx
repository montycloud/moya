
import { useState, useEffect } from 'react';
import { Check, Copy } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface CodeBlockProps {
  language: string;
  value: string;
}

const CodeBlock = ({ language, value }: CodeBlockProps) => {
  const [copied, setCopied] = useState(false);
  
  useEffect(() => {
    if (copied) {
      const timeout = setTimeout(() => setCopied(false), 2000);
      return () => clearTimeout(timeout);
    }
  }, [copied]);
  
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
    } catch (error) {
      console.error('Failed to copy code:', error);
    }
  };
  
  // Display a more user-friendly language name
  const displayLanguage = {
    js: 'JavaScript',
    jsx: 'React',
    ts: 'TypeScript',
    tsx: 'React TypeScript',
    py: 'Python',
    bash: 'Terminal',
    json: 'JSON',
    css: 'CSS',
    html: 'HTML',
  }[language] || language;
  
  return (
    <div className="code-block group relative">
      <div className="absolute top-2 right-2 z-10 flex items-center space-x-2">
        <span className="text-xs text-muted-foreground">{displayLanguage}</span>
        <button 
          onClick={handleCopy} 
          className={cn(
            "p-1 rounded-md transition-colors",
            "text-muted-foreground hover:text-foreground",
            "bg-secondary/40 hover:bg-secondary"
          )}
          aria-label={copied ? "Copied" : "Copy code"}
        >
          {copied ? (
            <Check className="h-4 w-4 text-green-500" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
        </button>
      </div>
      
      <SyntaxHighlighter
        language={language}
        style={oneDark}
        customStyle={{
          margin: 0,
          padding: '2rem 1rem 1rem',
          borderRadius: '0.75rem',
          background: 'transparent',
        }}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  );
};

export default CodeBlock;
