import { buildUrl, requestJson } from "./client";
import type {
  ChatMessage,
  Story,
  StoryDraftPayload,
  StoryGenerateJobResponse,
  StoryGenerateJobStatus,
  StoryGenerateRequest,
  StorySummary,
} from "./types";

type StoryPayload = StoryDraftPayload & {
  summary_prompt_key: string;
  plot_summary: string;
  messages: ChatMessage[];
};

function toStoryPayload(payload: StoryDraftPayload): StoryPayload {
  return {
    ...payload,
    summary_prompt_key: payload.ai_instruction_key === "dark_storyteller" ? "dark_summarizer" : "neutral_summarizer",
    plot_summary: "",
    messages: [],
  };
}

export function listStories() {
  return requestJson<StorySummary[]>("/stories");
}

export function getStory(storyId: string) {
  return requestJson<Story>(`/stories/${storyId}`);
}

export function createStory(payload: StoryDraftPayload) {
  return requestJson<Story>("/stories", {
    method: "POST",
    body: toStoryPayload(payload),
  });
}

export function updateStory(storyId: string, payload: Partial<StoryPayload>) {
  return requestJson<Story>(`/stories/${storyId}`, {
    method: "PUT",
    body: payload,
  });
}

export function deleteStory(storyId: string) {
  return requestJson<void>(`/stories/${storyId}`, {
    method: "DELETE",
  });
}

export function syncStoryLore(storyId: string) {
  return requestJson<void>(`/stories/${storyId}/lore/sync`, {
    method: "POST",
  });
}

export function acceptLoreSuggestion(storyId: string, suggestionId: string) {
  return requestJson<void>(`/stories/${storyId}/lore/review/${suggestionId}/accept`, {
    method: "POST",
  });
}

export function rejectLoreSuggestion(storyId: string, suggestionId: string) {
  return requestJson<void>(`/stories/${storyId}/lore/review/${suggestionId}/reject`, {
    method: "POST",
  });
}

export function generateStoryDraft(payload: StoryGenerateRequest) {
  return requestJson<StoryGenerateJobResponse>("/stories/generate", {
    method: "POST",
    body: payload,
  });
}

export function getStoryGenerateJob(jobId: string) {
  return requestJson<StoryGenerateJobStatus>(`/stories/generate/${jobId}`);
}

export async function streamTurn(
  storyId: string,
  text: string,
  mode: string,
  onChunk: (chunk: string) => void,
) {
  const response = await fetch(buildUrl("/turn/stream"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      text,
      mode,
      story_id: storyId,
      trigger: text || undefined,
    }),
  });

  if (!response.ok) {
    throw new Error((await response.text()) || `Stream failed with status ${response.status}`);
  }

  if (!response.body) {
    throw new Error("Streaming response body is missing.");
  }

  const decoder = new TextDecoder();
  const reader = response.body.getReader();
  let fullText = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    const chunk = decoder.decode(value, { stream: true });
    if (chunk) {
      fullText += chunk;
      onChunk(chunk);
    }
  }

  fullText += decoder.decode();
  return fullText;
}
