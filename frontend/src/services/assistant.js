// Dashboard AI assistant for every role.
import { api } from "./api";

// Role-scoped snapshot for the assistant.
export async function fetchAssistantContext() {
  return api.get("/api/v1/assistant/context");
}

// Ask one question or request the full analysis.
export async function askAssistant(question, { intent = "question", history = [] } = {}) {
  return api.post("/api/v1/assistant/chat", {
    question,
    intent,
    conversation_history: history.map((m) => ({ role: m.role, content: m.content })),
  });
}
