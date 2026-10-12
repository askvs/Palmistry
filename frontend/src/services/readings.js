import { api } from "./api";

export async function listReadings({ type, status, limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams();
  if (type) params.append("type", type);
  if (status) params.append("status", status);
  if (limit) params.append("limit", String(limit));
  if (offset) params.append("offset", String(offset));
  const query = params.toString() ? `?${params.toString()}` : "";
  return api.get(`/api/v1/readings${query}`);
}

export async function getReading(readingId) {
  return api.get(`/api/v1/readings/${readingId}`);
}

export async function updateReading(readingId, updates) {
  return api.patch(`/api/v1/readings/${readingId}`, updates);
}

export async function deleteReading(readingId) {
  return api.delete(`/api/v1/readings/${readingId}`);
}

export async function getReadingAnalytics() {
  return api.get("/api/v1/readings/analytics/me");
}

// AI interpretation.
export async function interpretPalm(readingId, question = null) {
  const cleanQ = question && question.trim() ? question.trim() : null;
  const params = new URLSearchParams();
  if (cleanQ) params.append("question", cleanQ);
  const query = params.toString() ? `?${params.toString()}` : "";
  return api.post(`/api/v1/interpret/palm${query}`, {
    reading_id: readingId,
    question: cleanQ,
  });
}

export async function interpretTarot(readingId, question = null, tarotData = null) {
  const cleanQ = question && question.trim() ? question.trim() : null;
  const payload = { question: cleanQ };
  if (readingId) payload.reading_id = readingId;
  else if (tarotData) payload.tarot_data = tarotData;
  const params = new URLSearchParams();
  if (cleanQ) params.append("question", cleanQ);
  const query = params.toString() ? `?${params.toString()}` : "";
  return api.post(`/api/v1/interpret/tarot${query}`, payload);
}

export async function synthesizeReadings(palmReadingId, tarotReadingId, question = null) {
  const cleanQ = question && question.trim() ? question.trim() : null;
  const params = new URLSearchParams();
  if (cleanQ) params.append("question", cleanQ);
  const query = params.toString() ? `?${params.toString()}` : "";
  return api.post(`/api/v1/interpret/synthesize${query}`, {
    palm_reading_id: palmReadingId,
    tarot_reading_id: tarotReadingId,
    question: cleanQ,
  });
}

// Interpretation from raw palm data without a reading id.
export async function interpretPalmDirect(palmData, question = null) {
  const cleanQ = question && question.trim() ? question.trim() : null;
  return api.post("/api/v1/interpret/palm", {
    palm_data: palmData,
    question: cleanQ,
  });
}

// Chat with AI about a reading.
export async function chatWithReadingAI(readingId, readingType, question, conversationHistory = []) {
  const cleanQ = question && question.trim() ? question.trim() : null;
  if (!cleanQ) throw new Error("Question cannot be empty.");

  return api.post("/api/v1/interpret/chat", {
    reading_id: readingId,
    reading_type: readingType,
    question: cleanQ,
    conversation_history: conversationHistory,
  });
}
