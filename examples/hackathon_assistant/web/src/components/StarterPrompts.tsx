import { PromptCategory } from '../lib/types';

interface StarterPromptsProps {
  categories: PromptCategory[];
  onPromptSelect: (prompt: string) => void;
}

const StarterPrompts = ({ categories, onPromptSelect }: StarterPromptsProps) => {
  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {categories.map((category, idx) => (
        <div key={idx} className="card border rounded-lg p-4">
          <h2 className="font-semibold mb-2">{category.title}</h2>
          <p className="text-muted-foreground text-sm mb-4">{category.description}</p>
          <ul className="space-y-2">
            {category.prompts.map((prompt, promptIdx) => (
              <li key={promptIdx}>
                <button
                  onClick={() => onPromptSelect(prompt.text)}
                  className="text-left hover:text-primary text-sm"
                >
                  {prompt.text}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
};

export default StarterPrompts;
