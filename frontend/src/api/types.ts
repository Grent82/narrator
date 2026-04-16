export type LoreEntry = {
  id: string;
  title: string;
  description: string;
  tag: string;
  triggers: string;
};

export type LoreSuggestion = {
  id: string;
  kind: string;
  status: string;
  title: string;
  tag: string;
  description: string;
  triggers: string;
  target_lore_id?: string | null;
  created_at?: string | null;
};

export type ChatMessage = {
  role: string;
  text: string;
  mode?: string | null;
};

export type StorySummary = {
  id: string;
  title: string;
  description: string;
  tags: string[];
};

export type Story = {
  id: string;
  title: string;
  ai_instruction_key: string;
  ai_instructions: string;
  summary_prompt_key: string;
  plot_summary: string;
  plot_essentials: string;
  author_note: string;
  description: string;
  tags: string[];
  lore: LoreEntry[];
  lore_review: LoreSuggestion[];
  messages: ChatMessage[];
};

export type StoryDraftPayload = {
  title: string;
  ai_instruction_key: string;
  ai_instructions: string;
  plot_essentials: string;
  author_note: string;
  description: string;
  tags: string[];
  lore: Array<Omit<LoreEntry, "id"> & { id?: string }>;
};

export type StoryGenerateRequest = {
  ai_instruction_key: string;
  role: string;
  name: string;
  gender: string;
  age: string;
  traits: string;
  world_input: string;
  start_template: string;
  start_custom: string;
};

export type StoryGenerateJobResponse = {
  job_id: string;
  status: string;
};

export type StoryGenerateResult = {
  title: string;
  description: string;
  plot_essentials: string;
  author_note: string;
  tags: string[];
  lore: Array<Omit<LoreEntry, "id">>;
};

export type StoryGenerateJobStatus = {
  job_id: string;
  status: string;
  result?: StoryGenerateResult | null;
  error?: string | null;
};
