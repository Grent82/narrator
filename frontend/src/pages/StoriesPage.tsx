import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createStory, deleteStory, getStory, listStories, updateStory } from "../api/stories";
import type { Story, StoryDraftPayload, StorySummary } from "../api/types";
import { StoryCard } from "../components/StoryCard";
import { StoryFormDialog } from "../components/StoryFormDialog";

export function StoriesPage() {
  const navigate = useNavigate();
  const [stories, setStories] = useState<StorySummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingStory, setEditingStory] = useState<Story | null>(null);

  const loadStories = async () => {
    setIsLoading(true);
    setError(null);
    try {
      setStories(await listStories());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load stories.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadStories();
  }, []);

  const handleCreate = async (payload: StoryDraftPayload) => {
    const story = await createStory(payload);
    setIsCreateOpen(false);
    navigate(`/story/${story.id}`);
  };

  const handleEditRequest = async (storyId: string) => {
    try {
      setEditingStory(await getStory(storyId));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load story.");
    }
  };

  const handleEdit = async (payload: StoryDraftPayload) => {
    if (!editingStory) {
      return;
    }
    await updateStory(editingStory.id, payload);
    setEditingStory(null);
    await loadStories();
  };

  const handleDelete = async (storyId: string) => {
    const confirmed = window.confirm("Delete this story?");
    if (!confirmed) {
      return;
    }

    try {
      await deleteStory(storyId);
      await loadStories();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Unable to delete story.");
    }
  };

  return (
    <main className="shell">
      <section className="hero panel">
        <div>
          <p className="eyebrow">Narrator</p>
          <h1>Stories</h1>
          <p className="muted">Create a story or continue an existing one.</p>
        </div>
        <div className="button-row">
          <button className="button button--primary" onClick={() => setIsCreateOpen(true)}>
            New Story
          </button>
        </div>
      </section>

      {error ? <p className="error-banner">{error}</p> : null}

      {isLoading ? <p className="muted">Loading stories...</p> : null}

      {!isLoading && stories.length === 0 ? <section className="panel"><p className="muted">No stories yet.</p></section> : null}

      <section className="story-grid">
        {stories.map((story) => (
          <StoryCard
            key={story.id}
            story={story}
            onOpen={() => navigate(`/story/${story.id}`)}
            onEdit={() => void handleEditRequest(story.id)}
            onDelete={() => void handleDelete(story.id)}
          />
        ))}
      </section>

      <StoryFormDialog
        open={isCreateOpen}
        title="Create Story"
        onClose={() => setIsCreateOpen(false)}
        onSubmit={handleCreate}
      />

      <StoryFormDialog
        open={editingStory !== null}
        title="Edit Story"
        story={editingStory}
        onClose={() => setEditingStory(null)}
        onSubmit={handleEdit}
      />
    </main>
  );
}
