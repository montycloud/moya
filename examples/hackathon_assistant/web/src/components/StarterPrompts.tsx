
import { useState } from 'react';
import { PromptCategory } from '../lib/types';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface StarterPromptsProps {
  categories: PromptCategory[];
  onPromptSelect: (prompt: string) => void;
}

const StarterPrompts = ({ categories, onPromptSelect }: StarterPromptsProps) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {categories.map((category, index) => (
        <CategoryCard 
          key={category.title} 
          category={category} 
          onPromptSelect={onPromptSelect}
          index={index}
        />
      ))}
    </div>
  );
};

interface CategoryCardProps {
  category: PromptCategory;
  onPromptSelect: (prompt: string) => void;
  index: number;
}

const CategoryCard = ({ category, onPromptSelect, index }: CategoryCardProps) => {
  const [isHovered, setIsHovered] = useState(false);
  
  // Stagger animation based on index
  const animationDelay = index * 0.1;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: animationDelay }}
      className="relative overflow-hidden rounded-lg border border-border bg-card shadow-sm"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="p-6">
        <h2 className="text-xl font-semibold mb-2">{category.title}</h2>
        <p className="text-sm text-muted-foreground mb-4">{category.description}</p>
        
        <div className="space-y-2">
          {category.prompts.map((prompt) => (
            <PromptButton
              key={prompt.text}
              text={prompt.text}
              icon={prompt.icon}
              onClick={() => onPromptSelect(prompt.text)}
              isHovered={isHovered}
            />
          ))}
        </div>
      </div>
      
      {/* Subtle background gradient */}
      <div className={cn(
        "absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none transition-opacity duration-500",
        isHovered ? "opacity-100" : "opacity-0"
      )} />
    </motion.div>
  );
};

interface PromptButtonProps {
  text: string;
  icon?: string;
  onClick: () => void;
  isHovered: boolean;
}

const PromptButton = ({ text, icon, onClick, isHovered }: PromptButtonProps) => {
  const [isButtonHovered, setIsButtonHovered] = useState(false);
  
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left p-3 rounded-md border border-border flex items-center gap-2 transition-all duration-300",
        "hover:border-primary/30 hover:bg-primary/5",
        isButtonHovered && "translate-x-1"
      )}
      onMouseEnter={() => setIsButtonHovered(true)}
      onMouseLeave={() => setIsButtonHovered(false)}
    >
      <span className="text-sm">{text}</span>
      
      {/* Arrow that appears on hover */}
      <span className={cn(
        "ml-auto text-primary transition-all duration-300",
        isButtonHovered ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-2"
      )}>
        →
      </span>
    </button>
  );
};

export default StarterPrompts;
