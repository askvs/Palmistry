import { apiFetch, setAccessToken, clearAccessToken, requestRefresh } from "./api";

// Auth service: memory access token plus httpOnly refresh cookie.
export async function registerUser({ email, password, fullName }) {
  const payload = await apiFetch("/api/v1/auth/register", {
    method: "POST",
    body: { email, password, full_name: fullName },
  });
  setAccessToken(payload.access_token);
  return payload;
}

export async function loginUser({ email, password }) {
  const payload = await apiFetch("/api/v1/auth/login", {
    method: "POST",
    body: { email, password },
  });
  setAccessToken(payload.access_token);
  return payload;
}

// Per-role portals mapped to backend /auth/{portal} routes.
export const ROLE_PORTALS = [
  {
    slug: "user",
    role: "user",
    label: "User",
    tagline: "Readings, insights, and personal guidance.",
    accent: "from-violet-600 to-fuchsia-500",
    tint: "bg-violet-50 text-violet-700 border-violet-200",
  },
  {
    slug: "tarot-reader",
    role: "tarot_reader",
    label: "Tarot Reader",
    tagline: "Manage readings, sessions, and reports.",
    accent: "from-amber-400 to-orange-500",
    tint: "bg-amber-50 text-amber-700 border-amber-200",
  },
  {
    slug: "spiritual-consultant",
    role: "spiritual_consultant",
    label: "Spiritual Consultant",
    tagline: "Analyze trends and provide guidance.",
    accent: "from-emerald-500 to-teal-500",
    tint: "bg-emerald-50 text-emerald-700 border-emerald-200",
  },
  {
    slug: "admin",
    role: "admin",
    label: "Administrator",
    tagline: "Manage users and the whole platform.",
    accent: "from-rose-500 to-red-500",
    tint: "bg-rose-50 text-rose-700 border-rose-200",
    inviteOnly: true,
  },
];

export function findPortal(slug) {
  return ROLE_PORTALS.find((p) => p.slug === slug) || null;
}

export async function loginViaPortal(slug, { email, password }) {
  const payload = await apiFetch(`/api/v1/auth/${slug}/login`, {
    method: "POST",
    body: { email, password },
  });
  setAccessToken(payload.access_token);
  return payload;
}

export async function registerViaPortal(slug, { email, password, fullName, adminInviteCode }) {
  const payload = await apiFetch(`/api/v1/auth/${slug}/register`, {
    method: "POST",
    body: {
      email,
      password,
      full_name: fullName,
      admin_invite_code: adminInviteCode || null,
    },
  });
  setAccessToken(payload.access_token);
  return payload;
}

export async function refreshSession() {
  // Shares the single-flight refresh with the 401-retry path.
  return requestRefresh();
}

export async function fetchCurrentUser() {
  return apiFetch("/api/v1/auth/me");
}

export async function logoutUser() {
  await apiFetch("/api/v1/auth/logout", { method: "POST" });
  clearAccessToken();
}

export function googleAuthorizeUrl() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  return `${base}/api/v1/auth/google/authorize`;
}
