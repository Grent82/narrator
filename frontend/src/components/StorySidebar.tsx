import type { LoreEntry, LoreSuggestion, Story } from "../api/types";

type StorySidebarProps = {
  story: Story;
  onAcceptSuggestion: (suggestionId: string) => void;
  onRejectSuggestion: (suggestionId: string) => void;
};

function LoreList({ entries }: { entries: LoreEntry[] }) {
  if (entries.length === 0) {
    return <p className="muted">No lore entries yet.</p>;
  }

  return (
    <div className="sidebar-list">
      {entries.map((entry) => (
        <article key={entry.id} className="sidebar-card">
          <div className="sidebar-card__header">
            <strong>{entry.title}</strong>
            <span className="tag">{entry.tag}</span>
          </div>
          <p>{entry.description || "No description."}</p>
          {entry.triggers ? <p className="muted">Triggers: {entry.triggers}</p> : null}
        </article>
      ))}
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
            <button className="button button--primary" onClick={() => onAcceptSuggestion(item.id)}>Accept</button>
            <button className="button button--ghost" onClick={() => onRejectSuggestion(item.id)}>Reject</button>
          </div>
        </article>
      ))}
    </div>
  );
}

export function StorySidebar({ story, onAcceptSuggestion, onRejectSuggestion }: StorySidebarProps) {
  return (
    <aside className="story-sidebar">
      <section className="panel">
        <p className="eyebrow">Story Info</p>
        <h2>{story.title}</h2>
        <p>{story.description || "No description."}</p>
        <p className="muted">{story.tags.length > 0 ? story.tags.join(", ") : "No tags."}</p>
      </section>

      <section className="panel">
        <p className="eyebrow">Plot Essentials</p>
        <p>{story.plot_essentials || "No plot essentials set."}</p>
      </section>

      <section className="panel">
        <p className="eyebrow">Author Note</p>
        <p>{story.author_note || "No author note set."}</p>
      </section>

      <section className="panel">
        <p className="eyebrow">Lore</p>
        <LoreList entries={story.lore} />
      </section>

      <section className="panel">
        <p className="eyebrow">Lore Review</p>
        <SuggestionList
          suggestions={story.lore_review}
          onAcceptSuggestion={onAcceptSuggestion}
          onRejectSuggestion={onRejectSuggestion}
        />
      </section>
    </aside>
  );
}
