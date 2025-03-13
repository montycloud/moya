export interface Prompt {
  text: string;
}

export interface PromptCategory {
  title: string;
  description: string;
  prompts: Prompt[];
}
