import type { UIMessage } from "ai";

export function MessageBubble({ message }: { message: UIMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`message message-${isUser ? "user" : "ai"}`}>
      <div className="message-content">
        {message.parts.map((part, i) => {
          if (part.type === "text") {
            return part.text.split("\n").map((line, j) => (
              <p key={`${i}-${j}`}>{line}</p>
            ));
          }
          return null;
        })}
      </div>
    </div>
  );
}
