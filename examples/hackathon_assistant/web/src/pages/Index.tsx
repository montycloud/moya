import { useState, useEffect } from 'react';
import Header from '../components/Header';
import ChatInterface from '../components/ChatInterface';
import StarterPrompts from '../components/StarterPrompts';
import AnimatedBackground from '../components/AnimatedBackground';
import { fetchStarterPrompts } from '../lib/api';
import { PromptCategory } from '../lib/types';

const Index = () => {
  const [showPrompts, setShowPrompts] = useState(true);
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);
  const [promptCategories, setPromptCategories] = useState<PromptCategory[]>([]);

  useEffect(() => {
    const loadPrompts = async () => {
      try {
        const data = await fetchStarterPrompts();
        setPromptCategories(data.prompts || []); // Add fallback for empty response
      } catch (error) {
        console.error('Failed to load starter prompts:', error);
        // Initialize with empty array on error
        setPromptCategories([]);
      }
    };
    loadPrompts();
  }, []);

  const handlePromptSelect = (prompt: string) => {
    setSelectedPrompt(prompt);
    setShowPrompts(false);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center">
      <AnimatedBackground />
      <div className="w-full max-w-chat px-4 sm:px-6 md:px-8 relative z-10">
        <Header />
        
        <main role="main" className="flex flex-col w-full">
          {showPrompts ? (
            <div className="animate-fade-in">
              <h1 className="text-2xl sm:text-3xl font-semibold text-gradient mb-2">
                Moya AI Framework Assistant
              </h1>
              <p className="text-muted-foreground mb-8">
                Explore the Multi-agent Orchestration Framework for CloudOps automation
              </p>
              <StarterPrompts 
                categories={promptCategories}
                onPromptSelect={handlePromptSelect}
              />
            </div>
          ) : (
            <ChatInterface initialPrompt={selectedPrompt} onReset={() => setShowPrompts(true)} />
          )}
        </main>
      </div>
    </div>
  );
};

export default Index;
