import { api } from "./api";

export async function buildPersonalityProfile(payload) {
  return api.post("/api/v1/personality/profile", payload);
}

export async function enrichPersonalityProfile(profile) {
  return api.post("/api/v1/personality/enrich", { profile });
}
