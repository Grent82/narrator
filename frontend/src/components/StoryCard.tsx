import type { StorySummary } from "../api/types";

type StoryCardProps = {
  story: StorySummary;
  onOpen: () => void;
  onEdit: () => void;
  onDelete: () => void;
};

export function StoryCard({ story, onOpen, onEdit, onDelete }: StoryCardProps) {
  return (
    <article className="panel story-card">
      <div className="story-card__body">
        <div>
          <p className="eyebrow">Story</p>
          <h2>{story.title}</h2>
          <p className="muted">{story.description || "No description yet."}</p>
        </div>
        <div className="tag-row">
          {story.tags.length > 0 ? story.tags.map((tag) => <span key={tag} className="tag">{tag}</span>) : <span className="muted">No tags</span>}
        </div>
      </div>
      <div className="button-row">
        <button className="button button--primary" onClick={onOpen}>Open</button>
        <button className="button button--ghost" onClick={onEdit}>Edit</button>
        <button className="button button--danger" onClick={onDelete}>Delete</button>
      </div>
    </article>
  );
}
