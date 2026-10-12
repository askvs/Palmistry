// Tarot Reader workspace services.
import { api } from "./api";

// Spread authoring.
// Standard plus owned and shared spreads.
export function listReaderSpreads() {
  return api.get("/api/v1/reader/spreads");
}

export function createCustomSpread(payload) {
  return api.post("/api/v1/reader/spreads", {
    name: payload.name,
    description: payload.description || null,
    category: payload.category || "custom",
    positions: payload.positions.map((position) => ({
      name: position.name,
      description: position.description || null,
    })),
    visibility: payload.visibility || "private",
  });
}

export function updateCustomSpread(spreadId, payload) {
  const body = {};
  if (payload.name !== undefined) body.name = payload.name;
  if (payload.description !== undefined) body.description = payload.description;
  if (payload.category !== undefined) body.category = payload.category;
  if (payload.positions !== undefined) {
    body.positions = payload.positions.map((position) => ({
      name: position.name,
      description: position.description || null,
    }));
  }
  if (payload.visibility !== undefined) body.visibility = payload.visibility;
  return api.patch(`/api/v1/reader/spreads/${spreadId}`, body);
}

export function deleteCustomSpread(spreadId) {
  return api.delete(`/api/v1/reader/spreads/${spreadId}`);
}

// Reading report management.
export function listReaderReports(params = {}) {
  const query = new URLSearchParams();
  if (params.type) query.set("type", params.type);
  if (params.status) query.set("status", params.status);
  if (params.reviewed !== undefined && params.reviewed !== null) {
    query.set("reviewed", String(params.reviewed));
  }
  if (params.search) query.set("search", params.search);
  if (params.ownerEmail) query.set("owner_email", params.ownerEmail);
  if (params.limit) query.set("limit", String(params.limit));
  const qs = query.toString();
  return api.get(`/api/v1/reader/reports${qs ? `?${qs}` : ""}`);
}

// Engagement insights.
export function readerEngagement(days = 30) {
  return api.get(`/api/v1/reader/engagement?days=${days}`);
}
