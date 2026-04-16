import { useEffect, useState } from "react";
import type { LoreEntry, Story, StoryDraftPayload } from "../api/types";
import { LORE_TAG_OPTIONS } from "../constants/loreTags";
import {
  AI_INSTRUCTION_PRESETS,
  DEFAULT_AI_INSTRUCTION_KEY,
  ROLE_OPTIONS,
  START_TEMPLATES,
  type PresetKey,
} from "../constants/storyDefaults";
import { generateStoryDraft, getStoryGenerateJob } from "../api/stories";

type StoryFormDialogProps = {
  open: boolean;
  title: string;
  story?: Story | null;
  onClose: () => void;
  onSubmit: (payload: StoryDraftPayload) => Promise<void>;
};

type LoreDraft = Omit<LoreEntry, "id"> & { id?: string };

type FormState = {
  title: string;
  aiInstructionKey: PresetKey;
  aiInstructions: string;
  plotEssentials: string;
  authorNote: string;
  description: string;
  tags: string;
  lore: LoreDraft[];
};

const emptyLore = (): LoreDraft => ({
  title: "",
  description: "",
  tag: "Character",
  triggers: "",
});

const emptyFormState = (): FormState => ({
  title: "",
  aiInstructionKey: DEFAULT_AI_INSTRUCTION_KEY,
  aiInstructions: AI_INSTRUCTION_PRESETS[DEFAULT_AI_INSTRUCTION_KEY].text,
  plotEssentials: "",
  authorNote: "",
  description: "",
  tags: "",
  lore: [],
});

function toFormState(story?: Story | null): FormState {
  if (!story) {
    return emptyFormState();
  }

  return {
    title: story.title,
    aiInstructionKey: (story.ai_instruction_key in AI_INSTRUCTION_PRESETS
      ? story.ai_instruction_key
      : DEFAULT_AI_INSTRUCTION_KEY) as PresetKey,
    aiInstructions: story.ai_instructions,
    plotEssentials: story.plot_essentials,
    authorNote: story.author_note,
    description: story.description,
    tags: story.tags.join(", "),
    lore: story.lore.map((entry) => ({ ...entry })),
  };
}

function toPayload(state: FormState): StoryDraftPayload {
  return {
    title: state.title.trim() || "Untitled Story",
    ai_instruction_key: state.aiInstructionKey,
    ai_instructions: state.aiInstructions.trim() || AI_INSTRUCTION_PRESETS[state.aiInstructionKey].text,
    plot_essentials: state.plotEssentials,
    author_note: state.authorNote,
    description: state.description,
    tags: state.tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean),
    lore: state.lore
      .filter((entry) => entry.title.trim() && entry.tag.trim())
      .map((entry) => ({
        id: entry.id,
        title: entry.title.trim(),
        description: entry.description.trim(),
        tag: entry.tag.trim(),
        triggers: entry.triggers.trim(),
      })),
  };
}

async function pollGeneratedDraft(jobId: string) {
  for (let attempt = 0; attempt < 90; attempt += 1) {
    const status = await getStoryGenerateJob(jobId);
    if (status.status === "error") {
      throw new Error(status.error || "Story generation failed.");
    }
    if (status.status === "done" && status.result) {
      return status.result;
    }
    await new Promise((resolve) => window.setTimeout(resolve, 2000));
  }
  throw new Error("Story generation timed out.");
}

export function StoryFormDialog({ open, title, story, onClose, onSubmit }: StoryFormDialogProps) {
  const [state, setState] = useState<FormState>(() => toFormState(story));
  const [isSaving, setIsSaving] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatorRole, setGeneratorRole] = useState(ROLE_OPTIONS[0]);
  const [generatorName, setGeneratorName] = useState("");
  const [generatorGender, setGeneratorGender] = useState("");
  const [generatorAge, setGeneratorAge] = useState("");
  const [generatorTraits, setGeneratorTraits] = useState("");
  const [generatorWorld, setGeneratorWorld] = useState("");
  const [generatorTemplate, setGeneratorTemplate] = useState(START_TEMPLATES[0]);
  const [generatorCustomStart, setGeneratorCustomStart] = useState("");

  useEffect(() => {
    if (!open) {
      return;
    }
    setState(toFormState(story));
    setError(null);
  }, [open, story]);

  if (!open) {
    return null;
  }

  const updateLore = (index: number, field: keyof LoreDraft, value: string) => {
    setState((current) => ({
      ...current,
      lore: current.lore.map((entry, entryIndex) => (entryIndex === index ? { ...entry, [field]: value } : entry)),
    }));
  };

  const handlePresetChange = (value: string) => {
    const preset = (value in AI_INSTRUCTION_PRESETS ? value : DEFAULT_AI_INSTRUCTION_KEY) as PresetKey;
    setState((current) => ({
      ...current,
      aiInstructionKey: preset,
      aiInstructions: AI_INSTRUCTION_PRESETS[preset].text,
    }));
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const job = await generateStoryDraft({
        ai_instruction_key: state.aiInstructionKey,
        role: generatorRole,
        name: generatorName,
        gender: generatorGender,
        age: generatorAge,
        traits: generatorTraits,
        world_input: generatorWorld,
        start_template: generatorTemplate,
        start_custom: generatorCustomStart,
      });

      const draft = await pollGeneratedDraft(job.job_id);
      setState((current) => ({
        ...current,
        title: draft.title,
        description: draft.description,
        plotEssentials: draft.plot_essentials,
        authorNote: draft.author_note,
        tags: draft.tags.join(", "),
        lore: draft.lore.map((entry) => ({ ...entry })),
      }));
    } catch (generationError) {
      setError(generationError instanceof Error ? generationError.message : "Story generation failed.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSubmit = async () => {
    setIsSaving(true);
    setError(null);
    try {
      await onSubmit(toPayload(state));
      onClose();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to save story.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <section
        className="modal panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="story-form-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal__header">
          <div>
            <p className="eyebrow">Story Editor</p>
            <h2 id="story-form-title">{title}</h2>
          </div>
          <button className="button button--ghost" onClick={onClose} aria-label="Close dialog">
            Close
          </button>
        </div>

        {error ? <p className="error-banner">{error}</p> : null}

        <div className="modal__body">
          <section className="form-section">
            <div className="form-section__header">
              <div>
                <p className="eyebrow">Generator</p>
                <h3>Generate a draft</h3>
              </div>
              <button className="button button--primary" disabled={isGenerating} onClick={handleGenerate}>
                {isGenerating ? "Generating..." : "Generate"}
              </button>
            </div>
            <div className="form-grid">
              <label>
                Role
                <select value={generatorRole} onChange={(event) => setGeneratorRole(event.target.value)}>
                  {ROLE_OPTIONS.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Name
                <input value={generatorName} onChange={(event) => setGeneratorName(event.target.value)} />
              </label>
              <label>
                Gender
                <input value={generatorGender} onChange={(event) => setGeneratorGender(event.target.value)} />
              </label>
              <label>
                Age
                <input value={generatorAge} onChange={(event) => setGeneratorAge(event.target.value)} />
              </label>
              <label className="field-span-2">
                Traits
                <textarea value={generatorTraits} onChange={(event) => setGeneratorTraits(event.target.value)} rows={4} />
              </label>
              <label className="field-span-2">
                World Input
                <textarea value={generatorWorld} onChange={(event) => setGeneratorWorld(event.target.value)} rows={4} />
              </label>
              <label>
                Start Template
                <select value={generatorTemplate} onChange={(event) => setGeneratorTemplate(event.target.value)}>
                  {START_TEMPLATES.map((template) => (
                    <option key={template} value={template}>
                      {template}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Custom Start
                <textarea value={generatorCustomStart} onChange={(event) => setGeneratorCustomStart(event.target.value)} rows={4} />
              </label>
            </div>
          </section>

          <section className="form-section">
            <div className="form-grid">
              <label>
                Title
                <input value={state.title} onChange={(event) => setState((current) => ({ ...current, title: event.target.value }))} />
              </label>
              <label>
                AI Preset
                <select value={state.aiInstructionKey} onChange={(event) => handlePresetChange(event.target.value)}>
                  {Object.entries(AI_INSTRUCTION_PRESETS).map(([key, preset]) => (
                    <option key={key} value={key}>
                      {preset.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field-span-2">
                AI Instructions
                <textarea
                  value={state.aiInstructions}
                  onChange={(event) => setState((current) => ({ ...current, aiInstructions: event.target.value }))}
                  rows={8}
                />
              </label>
              <label className="field-span-2">
                Plot Essentials
                <textarea
                  value={state.plotEssentials}
                  onChange={(event) => setState((current) => ({ ...current, plotEssentials: event.target.value }))}
                  rows={5}
                />
              </label>
              <label className="field-span-2">
                Author Note
                <textarea
                  value={state.authorNote}
                  onChange={(event) => setState((current) => ({ ...current, authorNote: event.target.value }))}
                  rows={5}
                />
              </label>
              <label className="field-span-2">
                Description
                <textarea
                  value={state.description}
                  onChange={(event) => setState((current) => ({ ...current, description: event.target.value }))}
                  rows={4}
                />
              </label>
              <label className="field-span-2">
                Tags
                <input
                  value={state.tags}
                  onChange={(event) => setState((current) => ({ ...current, tags: event.target.value }))}
                  placeholder="dark-fantasy, intrigue, frontier"
                />
              </label>
            </div>
          </section>

          <section className="form-section">
            <div className="form-section__header">
              <div>
                <p className="eyebrow">Lore</p>
                <h3>World context</h3>
              </div>
              <button
                className="button button--ghost"
                onClick={() => setState((current) => ({ ...current, lore: [...current.lore, emptyLore()] }))}
              >
                Add Lore Entry
              </button>
            </div>
            <div className="lore-editor">
              {state.lore.length === 0 ? <p className="muted">No lore entries yet.</p> : null}
              {state.lore.map((entry, index) => (
                <article key={`${entry.id || "new"}-${index}`} className="panel lore-draft-card">
                  <div className="form-grid">
                    <label>
                      Title
                      <input value={entry.title} onChange={(event) => updateLore(index, "title", event.target.value)} />
                    </label>
                    <label>
                      Tag
                      <select value={entry.tag} onChange={(event) => updateLore(index, "tag", event.target.value)}>
                        {LORE_TAG_OPTIONS.map((tag) => (
                          <option key={tag} value={tag}>
                            {tag}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="field-span-2">
                      Description
                      <textarea value={entry.description} onChange={(event) => updateLore(index, "description", event.target.value)} rows={4} />
                    </label>
                    <label className="field-span-2">
                      Triggers
                      <input value={entry.triggers} onChange={(event) => updateLore(index, "triggers", event.target.value)} />
                    </label>
                  </div>
                  <div className="button-row">
                    <button
                      className="button button--danger"
                      onClick={() =>
                        setState((current) => ({
                          ...current,
                          lore: current.lore.filter((_, loreIndex) => loreIndex !== index),
                        }))
                      }
                    >
                      Remove
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </section>
        </div>

        <div className="button-row">
          <button className="button button--ghost" onClick={onClose}>
            Cancel
          </button>
          <button className="button button--primary" disabled={isSaving} onClick={handleSubmit}>
            {isSaving ? "Saving..." : "Save Story"}
          </button>
        </div>
      </section>
    </div>
  );
}
