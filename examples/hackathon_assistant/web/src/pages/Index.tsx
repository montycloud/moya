
import { useState, useEffect } from 'react';
import Header from '../components/Header';
import ChatInterface from '../components/ChatInterface';
import StarterPrompts from '../components/StarterPrompts';
import AnimatedBackground from '../components/AnimatedBackground';
import { PromptCategory } from '../lib/types';

const promptCategories: PromptCategory[] = [
  {
    title: "Framework Introduction",
    description: "Learn about the core concepts of Moya",
    prompts: [
      { text: "What is Moya and how does it help with CloudOps automation?" },
      { text: "Can you explain Moya's multi-agent architecture?" },
      { text: "What are the key components of the Moya framework?" },
      { text: "How does Moya handle agent orchestration?" }
    ]
  },
  {
    title: "Getting Started",
    description: "Begin your journey with Moya",
    prompts: [
      { text: "How do I install and set up Moya?" },
      { text: "What are the prerequisites for using Moya?" },
      { text: "Can you show me a basic example of using Moya?" },
      { text: "How do I create my first agent in Moya?" }
    ]
  },
  {
    title: "Agent System",
    description: "Explore Moya's agent capabilities",
    prompts: [
      { text: "What types of agents are available in Moya?" },
      { text: "How do I configure OpenAI agents in Moya?" },
      { text: "How do I create a custom agent?" },
      { text: "How does agent communication work?" }
    ]
  },
  {
    title: "Memory & Tools",
    description: "Learn about memory systems and tool integration",
    prompts: [
      { text: "How does Moya's memory system work?" },
      { text: "What built-in tools are available?" },
      { text: "How do I create custom tools?" },
      { text: "How does the tool registry work?" }
    ]
  },
  {
    title: "CloudOps Integration",
    description: "Connect Moya with cloud infrastructure",
    prompts: [
      { text: "How does Moya integrate with cloud services?" },
      { text: "Can you explain Moya's AWS integration?" },
      { text: "How to use Moya for cloud automation?" },
      { text: "What CloudOps tasks can Moya handle?" }
    ]
  },
  {
    title: "Best Practices",
    description: "Optimize your Moya implementation",
    prompts: [
      { text: "What are the best practices for agent design?" },
      { text: "How should I structure my Moya project?" },
      { text: "What are common pitfalls to avoid?" },
      { text: "How do I debug Moya applications?" }
    ]
  }
];

const Index = () => {
  const [showPrompts, setShowPrompts] = useState(true);
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);

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
