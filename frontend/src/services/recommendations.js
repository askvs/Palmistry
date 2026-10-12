import { api } from "./api";

// Generate personalized recommendations.
export async function generateRecommendations(payload) {
  return api.post("/api/v1/recommendations/generate", payload);
}

// List the current user's stored recommendations.
export async function listMyRecommendations(params = {}) {
  const query = new URLSearchParams();
  if (params.rec_type) query.append("rec_type", params.rec_type);
  if (params.status) query.append("status", params.status);
  if (params.batch_id) query.append("batch_id", params.batch_id);
  if (params.limit) query.append("limit", String(params.limit));
  if (params.offset) query.append("offset", String(params.offset));
  const qs = query.toString();
  return api.get(`/api/v1/recommendations/me${qs ? `?${qs}` : ""}`);
}

// Submit feedback on a recommendation.
export async function submitRecommendationFeedback(recordId, action, rating = null) {
  if (!["accepted", "dismissed", "completed", "rated"].includes(action)) {
    throw new Error(`Invalid feedback action: ${action}`);
  }
  if (action === "rated" && (!rating || rating < 1 || rating > 5)) {
    throw new Error("Rating must be between 1 and 5 when action is 'rated'");
  }

  const payload = { action };
  if (rating !== null) payload.rating = rating;

  return api.patch(`/api/v1/recommendations/${recordId}/feedback`, payload);
}

// Recommendation effectiveness metrics.
export async function getRecommendationMetrics() {
  return api.get("/api/v1/recommendations/metrics");
}
