import type { ChatMessage } from "../api/types";

function formatUserMessage(message: ChatMessage) {
  const mode = (message.mode || "story").toLowerCase();
  if (mode === "say") {
    return message.text ? `You say: "${message.text}"` : "";
  }
  if (mode === "do") {
    return message.text ? `You do: ${message.text}` : "";
  }
  if (mode === "continue") {
    return "";
  }
  return message.text;
}

type ChatTranscriptProps = {
  messages: ChatMessage[];
};

export function ChatTranscript({ messages }: ChatTranscriptProps) {
  return (
    <div className="panel transcript" aria-live="polite">
      {messages.length === 0 ? <p className="muted">No turns yet.</p> : null}
      {messages.map((message, index) => {
        const key = `${message.role}-${index}`;
        if (message.role === "user") {
          const text = formatUserMessage(message);
          if (!text) {
            return null;
          }
          return (
            <p key={key} className="transcript__user">
              &gt; {text}
            </p>
          );
        }

        return (
          <div key={key} className="transcript__assistant">
            {message.text || <span className="muted">...</span>}
          </div>
        );
      })}
    </div>
  );
}
