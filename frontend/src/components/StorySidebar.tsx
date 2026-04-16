import { useEffect, useState } from "react";
import type { LoreEntry, LoreSuggestion, Story } from "../api/types";
import { LORE_TAG_OPTIONS } from "../constants/loreTags";

type StorySidebarProps = {
  story: Story;
  open: boolean;
  onClose: () => void;
  onSavePlot: (fields: { plot_essentials: string; author_note: string }) => Promise<void>;
  onSaveDetails: (fields: { title: string; description: string; tags: string[] }) => Promise<void>;
  onAddLore: (entry: Omit<LoreEntry, "id"> & { id?: string }) => Promise<void>;
  onUpdateLore: (entry: LoreEntry) => Promise<void>;
  onDeleteLore: (entryId: string) => Promise<void>;
  onDuplicateLore: (entry: LoreEntry) => Promise<void>;
  onAcceptSuggestion: (suggestionId: string) => void;
  onRejectSuggestion: (suggestionId: string) => void;
};

type SidebarTab = "story" | "lore" | "details";

type LoreDraft = {
  id?: string;
  title: string;
  description: string;
  tag: string;
  triggers: string;
};

function parseTags(value: string) {
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function emptyLore(): LoreDraft {
  return { title: "", description: "", tag: "Character", triggers: "" };
}

function LoreDialog({
  open,
  title,
  entry,
  onClose,
  onSave,
}: {
  open: boolean;
  title: string;
  entry: LoreDraft;
  onClose: () => void;
  onSave: (entry: LoreDraft) => Promise<void>;
}) {
  const [draft, setDraft] = useState<LoreDraft>(entry);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setDraft(entry);
    }
  }, [entry, open]);

  if (!open) {
    return null;
  }

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <section
        className="modal panel modal--narrow"
        role="dialog"
        aria-modal="true"
        aria-labelledby="lore-dialog-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal__header">
          <div>
            <p className="eyebrow">Lore Entry</p>
            <h2 id="lore-dialog-title">{title}</h2>
          </div>
          <button className="button button--ghost" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="form-grid">
          <label>
            Title
            <input value={draft.title} onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))} />
          </label>
          <label>
            Tag
            <select value={draft.tag} onChange={(event) => setDraft((current) => ({ ...current, tag: event.target.value }))}>
              {LORE_TAG_OPTIONS.map((tag) => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
          </label>
          <label className="field-span-2">
            Description
            <textarea
              rows={5}
              value={draft.description}
              onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))}
            />
          </label>
          <label className="field-span-2">
            Triggers
            <input
              value={draft.triggers}
              onChange={(event) => setDraft((current) => ({ ...current, triggers: event.target.value }))}
            />
          </label>
        </div>

        <div className="button-row">
          <button className="button button--ghost" onClick={onClose}>
            Cancel
          </button>
          <button
            className="button button--primary"
            disabled={isSaving}
            onClick={async () => {
              setIsSaving(true);
              try {
                await onSave(draft);
                onClose();
              } finally {
                setIsSaving(false);
              }
            }}
          >
            {isSaving ? "Saving..." : "Save"}
          </button>
        </div>
      </section>
    </div>
  );
}

function SuggestionList({
  suggestions,
  onAcceptSuggestion,
  onRejectSuggestion,
}: {
  suggestions: LoreSuggestion[];
  onAcceptSuggestion: (suggestionId: string) => void;
  onRejectSuggestion: (suggestionId: string) => void;
}) {
  if (suggestions.length === 0) {
    return <p className="muted">No pending review items.</p>;
  }

  return (
    <div className="sidebar-list">
      {suggestions.map((item) => (
        <article key={item.id} className="sidebar-card">
          <div className="sidebar-card__header">
            <strong>{item.title}</strong>
            <span className="tag">{item.kind}</span>
          </div>
          <p>{item.description || "No description."}</p>
          <p className="muted">Tag: {item.tag}</p>
          <div className="button-row">
            <button className="button button--primary" onClick={() => onAcceptSuggestion(item.id)}>
              Accept
            </button>
            <button className="button button--ghost" onClick={() => onRejectSuggestion(item.id)}>
              Reject
            </button>
          </div>
        </article>
      ))}
    </div>
  );
}

export function StorySidebar({
  story,
  open,
  onClose,
  onSavePlot,
  onSaveDetails,
  onAddLore,
  onUpdateLore,
  onDeleteLore,
  onDuplicateLore,
  onAcceptSuggestion,
  onRejectSuggestion,
}: StorySidebarProps) {
  const [activeTab, setActiveTab] = useState<SidebarTab>("story");
  const [plotEssentials, setPlotEssentials] = useState(story.plot_essentials);
  const [authorNote, setAuthorNote] = useState(story.author_note);
  const [title, setTitle] = useState(story.title);
  const [description, setDescription] = useState(story.description);
  const [tags, setTags] = useState(story.tags.join(", "));
  const [editingLore, setEditingLore] = useState<LoreDraft | null>(null);
  const [isLoreDialogOpen, setIsLoreDialogOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setPlotEssentials(story.plot_essentials);
    setAuthorNote(story.author_note);
    setTitle(story.title);
    setDescription(story.description);
    setTags(story.tags.join(", "));
  }, [story]);

  const panelClassName = open ? "story-drawer story-drawer--open" : "story-drawer";

  return (
    <>
      <aside className={panelClassName} aria-hidden={!open}>
        <div className="story-drawer__header">
          <div>
            <p className="eyebrow">Story Panel</p>
            <h2>{story.title}</h2>
          </div>
          <button className="button button--ghost" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="story-drawer__tabs" role="tablist" aria-label="Story side panel tabs">
          <button className={activeTab === "story" ? "tab-button tab-button--active" : "tab-button"} onClick={() => setActiveTab("story")}>
            Story
          </button>
          <button className={activeTab === "lore" ? "tab-button tab-button--active" : "tab-button"} onClick={() => setActiveTab("lore")}>
            Lore
          </button>
          <button className={activeTab === "details" ? "tab-button tab-button--active" : "tab-button"} onClick={() => setActiveTab("details")}>
            Details
          </button>
        </div>

        <div className="story-drawer__body">
          {activeTab === "story" ? (
            <section className="panel panel--inner">
              <div className="drawer-section">
                <label>
                  AI Instructions
                  <textarea rows={10} value={story.ai_instructions} readOnly />
                </label>
                <label>
                  Plot Summary
                  <textarea rows={6} value={story.plot_summary} readOnly />
                </label>
                <label>
                  Plot Essentials
                  <textarea rows={6} value={plotEssentials} onChange={(event) => setPlotEssentials(event.target.value)} />
                </label>
                <label>
                  Author Note
                  <textarea rows={6} value={authorNote} onChange={(event) => setAuthorNote(event.target.value)} />
                </label>
                <div className="button-row">
                  <button
                    className="button button--primary"
                    disabled={isSaving}
                    onClick={async () => {
                      setIsSaving(true);
                      try {
                        await onSavePlot({ plot_essentials: plotEssentials, author_note: authorNote });
                      } finally {
                        setIsSaving(false);
                      }
                    }}
                  >
                    Save Plot
                  </button>
                </div>
              </div>
            </section>
          ) : null}

          {activeTab === "lore" ? (
            <section className="panel panel--inner">
              <div className="drawer-section">
                <div className="story-drawer__section-header">
                  <div>
                    <p className="eyebrow">Lore</p>
                    <h3>World entries</h3>
                  </div>
                  <button
                    className="button button--primary"
                    onClick={() => {
                      setEditingLore(emptyLore());
                      setIsLoreDialogOpen(true);
                    }}
                  >
                    Add Entry
                  </button>
                </div>

                <div className="sidebar-list">
                  <button
                    className="lore-add-card"
                    onClick={() => {
                      setEditingLore(emptyLore());
                      setIsLoreDialogOpen(true);
                    }}
                  >
                    <span className="lore-add-card__icon">+</span>
                    <span className="lore-add-card__text">Add character info, location, faction, and more</span>
                  </button>
                  {story.lore.length === 0 ? <p className="muted">No lore entries yet.</p> : null}
                  {story.lore.map((entry) => (
                    <article key={entry.id} className="sidebar-card">
                      <div className="sidebar-card__header">
                        <strong>{entry.title}</strong>
                        <span className="tag">{entry.tag}</span>
                      </div>
                      <p>{entry.description || "No description."}</p>
                      {entry.triggers ? <p className="muted">Triggers: {entry.triggers}</p> : null}
                      <div className="button-row">
                        <button
                          className="button button--ghost"
                          onClick={() => {
                            setEditingLore(entry);
                            setIsLoreDialogOpen(true);
                          }}
                        >
                          Edit
                        </button>
                        <button className="button button--ghost" onClick={() => void onDuplicateLore(entry)}>
                          Duplicate
                        </button>
                        <button className="button button--danger" onClick={() => void onDeleteLore(entry.id)}>
                          Delete
                        </button>
                      </div>
                    </article>
                  ))}
                </div>

                <div className="story-drawer__section-header">
                  <div>
                    <p className="eyebrow">Review</p>
                    <h3>Pending suggestions</h3>
                  </div>
                </div>
                <SuggestionList
                  suggestions={story.lore_review}
                  onAcceptSuggestion={onAcceptSuggestion}
                  onRejectSuggestion={onRejectSuggestion}
                />
              </div>
            </section>
          ) : null}

          {activeTab === "details" ? (
            <section className="panel panel--inner">
              <div className="drawer-section">
                <label>
                  Title
                  <input value={title} onChange={(event) => setTitle(event.target.value)} />
                </label>
                <label>
                  Description
                  <textarea rows={5} value={description} onChange={(event) => setDescription(event.target.value)} />
                </label>
                <label>
                  Tags
                  <input value={tags} onChange={(event) => setTags(event.target.value)} />
                </label>
                <div className="button-row">
                  <button
                    className="button button--primary"
                    disabled={isSaving}
                    onClick={async () => {
                      setIsSaving(true);
                      try {
                        await onSaveDetails({ title, description, tags: parseTags(tags) });
                      } finally {
                        setIsSaving(false);
                      }
                    }}
                  >
                    Save Details
                  </button>
                </div>
              </div>
            </section>
          ) : null}
        </div>
      </aside>

      <LoreDialog
        open={isLoreDialogOpen}
        title={editingLore?.id ? editingLore.title || "Lore Entry" : "New Lore Entry"}
        entry={editingLore || emptyLore()}
        onClose={() => {
          setIsLoreDialogOpen(false);
          setEditingLore(null);
        }}
        onSave={async (entry) => {
          if (editingLore?.id) {
            await onUpdateLore({
              id: editingLore.id,
              title: entry.title,
              description: entry.description,
              tag: entry.tag,
              triggers: entry.triggers,
            });
            return;
          }
          await onAddLore(entry);
        }}
      />
    </>
  );
}
