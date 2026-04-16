import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  acceptLoreSuggestion,
  getStory,
  rejectLoreSuggestion,
  syncStoryLore,
  streamTurn,
  updateStory,
} from "../api/stories";
import type { ChatMessage, Story } from "../api/types";
import { ChatTranscript } from "../components/ChatTranscript";
import { StoryFormDialog } from "../components/StoryFormDialog";
import { StorySidebar } from "../components/StorySidebar";

type TurnMode = "story" | "say" | "do" | "continue";

function cloneMessages(messages: ChatMessage[]) {
  return messages.map((message) => ({ ...message }));
}

export function StoryPage() {
  const { storyId } = useParams();
  const navigate = useNavigate();
  const [story, setStory] = useState<Story | null>(null);
  const storyRef = useRef<Story | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [command, setCommand] = useState("");
  const [mode, setMode] = useState<TurnMode>("story");
  const [isEditOpen, setIsEditOpen] = useState(false);

  const applyStory = (updater: (current: Story) => Story) => {
    setStory((current) => {
      if (!current) {
        return current;
      }
      const next = updater(current);
      storyRef.current = next;
      return next;
    });
  };

  const loadStory = async () => {
    if (!storyId) {
      setError("Story id is missing.");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      await syncStoryLore(storyId);
      const loadedStory = await getStory(storyId);
      setStory(loadedStory);
      storyRef.current = loadedStory;
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load story.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadStory();
  }, [storyId]);

  const persistMessages = async (messages: ChatMessage[]) => {
    if (!storyId) {
      return;
    }
    await updateStory(storyId, { messages });
  };

  const handleSendTurn = async (text: string, currentMode: TurnMode, showUser: boolean) => {
    if (!storyId || !storyRef.current || isStreaming) {
      return;
    }

    setIsStreaming(true);
    setError(null);
    setCommand("");

    let messages = cloneMessages(storyRef.current.messages);
    if (showUser) {
      messages.push({ role: "user", text, mode: currentMode });
    }
    messages.push({ role: "assistant", text: "" });

    applyStory((current) => ({
      ...current,
      messages,
    }));

    try {
      await streamTurn(storyId, text, currentMode, (chunk) => {
        messages = messages.map((message, index) =>
          index === messages.length - 1 ? { ...message, text: `${message.text}${chunk}` } : message,
        );
        applyStory((current) => ({
          ...current,
          messages,
        }));
      });
      await persistMessages(messages);
    } catch (streamError) {
      const message = streamError instanceof Error ? streamError.message : "Turn failed.";
      messages = messages.map((entry, index) =>
        index === messages.length - 1 ? { ...entry, text: `Backend error: ${message}` } : entry,
      );
      applyStory((current) => ({
        ...current,
        messages,
      }));
      setError(message);
      await persistMessages(messages);
    } finally {
      setIsStreaming(false);
    }
  };

  const findLastUser = (messages: ChatMessage[]) => {
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      if (messages[index]?.role === "user") {
        return messages[index];
      }
    }
    return null;
  };

  const handleContinue = async () => {
    await handleSendTurn("", "continue", false);
  };

  const handleRetry = async () => {
    if (!storyRef.current) {
      return;
    }

    const currentMessages = cloneMessages(storyRef.current.messages);
    if (currentMessages.length === 0) {
      return;
    }

    const lastMessage = currentMessages[currentMessages.length - 1];
    if (!lastMessage) {
      return;
    }

    if (lastMessage.role === "assistant") {
      currentMessages.pop();
      applyStory((current) => ({
        ...current,
        messages: currentMessages,
      }));
      const lastUser = findLastUser(currentMessages);
      if (lastUser) {
        await persistMessages(currentMessages);
        await handleSendTurn(lastUser.text, (lastUser.mode as TurnMode) || "story", false);
        return;
      }
      await persistMessages(currentMessages);
      await handleSendTurn("", "continue", false);
      return;
    }

    await handleSendTurn(lastMessage.text, (lastMessage.mode as TurnMode) || "story", false);
  };

  const handleErase = async () => {
    if (!storyRef.current || isSaving) {
      return;
    }

    const messages = cloneMessages(storyRef.current.messages);
    if (messages.length === 0) {
      return;
    }

    messages.pop();
    applyStory((current) => ({
      ...current,
      messages,
    }));

    setIsSaving(true);
    try {
      await persistMessages(messages);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to persist erased message.");
    } finally {
      setIsSaving(false);
    }
  };

  const refreshStory = async (action: () => Promise<void>) => {
    try {
      await action();
      await loadStory();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Action failed.");
    }
  };

  if (isLoading) {
    return (
      <main className="shell">
        <p className="muted">Loading story...</p>
      </main>
    );
  }

  if (!story) {
    return (
      <main className="shell">
        <p className="error-banner">{error || "Story not found."}</p>
        <Link className="button button--ghost" to="/">
          Back to stories
        </Link>
      </main>
    );
  }

  return (
    <main className="shell shell--wide">
      <section className="hero panel">
        <div>
          <p className="eyebrow">Story Session</p>
          <h1>{story.title}</h1>
          <p className="muted">{story.description || "No description."}</p>
        </div>
        <div className="button-row">
          <button className="button button--ghost" onClick={() => navigate("/")}>
            Back
          </button>
          <button className="button button--primary" onClick={() => setIsEditOpen(true)}>
            Edit Story
          </button>
        </div>
      </section>

      {error ? <p className="error-banner">{error}</p> : null}

      <section className="story-layout">
        <div className="story-main">
          <ChatTranscript messages={story.messages} />

          <section className="panel controls">
            <div className="button-row">
              <button className="button button--ghost" onClick={handleContinue} disabled={isStreaming}>
                Continue
              </button>
              <button className="button button--ghost" onClick={() => void handleRetry()} disabled={isStreaming}>
                Retry
              </button>
              <button className="button button--ghost" onClick={() => void handleErase()} disabled={isStreaming || isSaving}>
                Erase
              </button>
            </div>

            <label>
              Turn Mode
              <select value={mode} onChange={(event) => setMode(event.target.value as TurnMode)}>
                <option value="story">Story</option>
                <option value="say">Say</option>
                <option value="do">Do</option>
              </select>
            </label>

            <label>
              Input
              <textarea
                rows={4}
                value={command}
                onChange={(event) => setCommand(event.target.value)}
                placeholder="Describe what happens next."
              />
            </label>

            <div className="button-row">
              <button
                className="button button--primary"
                onClick={() => void handleSendTurn(command.trim(), mode, true)}
                disabled={isStreaming || !command.trim()}
              >
                {isStreaming ? "Streaming..." : "Take a Turn"}
              </button>
            </div>
          </section>
        </div>

        <StorySidebar
          story={story}
          onAcceptSuggestion={(suggestionId) => void refreshStory(() => acceptLoreSuggestion(story.id, suggestionId))}
          onRejectSuggestion={(suggestionId) => void refreshStory(() => rejectLoreSuggestion(story.id, suggestionId))}
        />
      </section>

      <StoryFormDialog
        open={isEditOpen}
        title="Edit Story"
        story={story}
        onClose={() => setIsEditOpen(false)}
        onSubmit={async (payload) => {
          await updateStory(story.id, payload);
          setIsEditOpen(false);
          await loadStory();
        }}
      />
    </main>
  );
}
