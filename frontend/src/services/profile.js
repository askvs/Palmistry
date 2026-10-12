// Profile service with lazy backend rows and blob avatars.
import { api, apiBlob } from "./api";

export const INTEREST_OPTIONS = [
  "Tarot",
  "Palmistry",
  "Numerology",
  "Meditation",
  "Astrology",
  "Crystal Healing",
  "Energy Work",
  "Manifestation",
  "Dream Interpretation",
  "Runes",
  "Chakras",
  "Mindfulness",
];

export const AGE_GROUP_OPTIONS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"];

export const DECK_OPTIONS = ["Rider-Waite-Smith"];

export const SPREAD_OPTIONS = [
  "Single Card",
  "Three Card",
  "Relationship",
  "Career",
  "Celtic Cross",
  "Life Path",
];

export const TONE_OPTIONS = ["Gentle", "Direct", "Balanced"];

export async function fetchProfile() {
  return api.get("/api/v1/profile");
}

export async function updateProfile(patch) {
  return api.patch("/api/v1/profile", patch);
}

export async function replaceInterests(interests) {
  return api.put("/api/v1/profile/interests", { interests });
}

export async function createGoal(text) {
  return api.post("/api/v1/profile/goals", { text });
}

export async function updateGoal(goalId, text) {
  return api.patch(`/api/v1/profile/goals/${goalId}`, { text });
}

export async function deleteGoal(goalId) {
  return api.delete(`/api/v1/profile/goals/${goalId}`);
}

export async function uploadAvatar(file) {
  const form = new FormData();
  form.append("avatar", file);
  return api.put("/api/v1/profile/avatar", form);
}

export async function removeAvatar() {
  return api.delete("/api/v1/profile/avatar");
}

export async function fetchAvatarBlobUrl(version) {
  const query = version ? `?v=${encodeURIComponent(version)}` : "";
  const blob = await apiBlob(`/api/v1/profile/avatar${query}`);
  return URL.createObjectURL(blob);
}
