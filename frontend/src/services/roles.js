import { api } from "./api";

// Reading services.
export function createTarotReading({ spread, cards, question }) {
  return api.post("/api/v1/readings/tarot", {
    spread,
    cards,
    question: question || null,
  });
}

export function uploadPalmReading(file) {
  const form = new FormData();
  form.append("image", file);
  return api.post("/api/v1/readings/palm", form);
}

export function listMyReadings(params = {}) {
  const query = new URLSearchParams();
  if (params.type) query.set("type", params.type);
  if (params.status) query.set("status", params.status);
  const qs = query.toString();
  return api.get(`/api/v1/readings${qs ? `?${qs}` : ""}`);
}

export function getMyReadingAnalytics() {
  return api.get("/api/v1/readings/analytics/me");
}

export function requestConsultation({ topic, message }) {
  return api.post("/api/v1/consultations", { topic, message });
}

export function listMyConsultations() {
  return api.get("/api/v1/consultations");
}

export function listConsultationMessages(consultationId) {
  return api.get(`/api/v1/consultations/${consultationId}/messages`);
}

export function postConsultationMessage(consultationId, { body }) {
  return api.post(`/api/v1/consultations/${consultationId}/messages`, { body });
}

// Tarot Reader workspace.
export function readerListReadings(params = {}) {
  const query = new URLSearchParams();
  if (params.type) query.set("type", params.type);
  if (params.status) query.set("status", params.status);
  const qs = query.toString();
  return api.get(`/api/v1/reader/readings${qs ? `?${qs}` : ""}`);
}

export function readerAnalytics() {
  return api.get("/api/v1/reader/readings/analytics");
}

export function readerReviewReading(readingId, { status, notes }) {
  return api.post(`/api/v1/reader/readings/${readingId}/review`, {
    status: status || null,
    notes: notes || null,
  });
}

// Spiritual Consultant.
export function consultantListConsultations() {
  return api.get("/api/v1/consultant/consultations");
}

export function consultantProvideGuidance(consultationId, { guidance, status }) {
  return api.post(`/api/v1/consultant/consultations/${consultationId}/guidance`, {
    guidance,
    status: status || null,
  });
}

export function consultantEffectiveness() {
  return api.get("/api/v1/consultant/insights/effectiveness");
}

export function consultantTrends() {
  return api.get("/api/v1/consultant/insights/trends");
}

export function consultantInsights() {
  return api.get("/api/v1/consultant/insights/consultations");
}

// Admin.
export function adminListUsers(params = {}) {
  const query = new URLSearchParams();
  if (params.role) query.set("role", params.role);
  if (params.search) query.set("search", params.search);
  const qs = query.toString();
  return api.get(`/api/v1/admin/users${qs ? `?${qs}` : ""}`);
}

export function adminUpdateUser(userId, updates) {
  return api.patch(`/api/v1/admin/users/${userId}`, updates);
}

export function adminPlatformAnalytics(days) {
  const qs = days ? `?days=${days}` : "";
  return api.get(`/api/v1/admin/analytics/platform${qs}`);
}

export function adminReadingStatistics(days) {
  const qs = days ? `?days=${days}` : "";
  return api.get(`/api/v1/admin/analytics/readings${qs}`);
}

export function adminListPlatformReadings(params = {}) {
  const query = new URLSearchParams();
  if (params.type) query.set("type", params.type);
  if (params.status) query.set("status", params.status);
  const qs = query.toString();
  return api.get(`/api/v1/admin/readings${qs ? `?${qs}` : ""}`);
}

export function adminListConsultations() {
  return api.get("/api/v1/admin/consultations");
}

export function adminGenerateSystemReport() {
  return api.post("/api/v1/admin/reports/system");
}

export function adminListAuditLogs() {
  return api.get("/api/v1/admin/audit-logs");
}

// Read-only session oversight.
export function adminSessionOversight(days = 30) {
  return api.get(`/api/v1/admin/analytics/sessions?days=${days}`);
}

// Live RBAC matrix with allowed roles.
export function adminPermissions() {
  return api.get("/api/v1/admin/permissions");
}

// Authentication posture.
export function adminAuthSettings() {
  return api.get("/api/v1/admin/settings/auth");
}

// Running configuration and release view.
export function adminSystemConfig() {
  return api.get("/api/v1/admin/settings/system");
}

// Operational error rows.
export function adminListErrors(params = {}) {
  const query = new URLSearchParams();
  if (params.level) query.set("level", params.level);
  if (params.kind) query.set("kind", params.kind);
  if (params.unresolvedOnly) query.set("unresolved_only", "true");
  if (params.limit) query.set("limit", String(params.limit));
  const qs = query.toString();
  return api.get(`/api/v1/admin/errors${qs ? `?${qs}` : ""}`);
}

export function adminErrorStats(hours = 24) {
  return api.get(`/api/v1/admin/errors/stats?hours=${hours}`);
}

export function adminAcknowledgeError(errorId) {
  return api.post(`/api/v1/admin/errors/${errorId}/acknowledge`);
}

// In-process latency aggregates.
export function adminPerformance() {
  return api.get("/api/v1/admin/system/performance");
}

// Persisted system reports (monitoring dashboards).
export function adminReportsOverview(days = 7) {
  return api.get(`/api/v1/admin/reports/overview?days=${days}`);
}

export function adminReportsHealth() {
  return api.get("/api/v1/admin/reports/health");
}

export function adminReportsErrors(days = 7, limit = 50) {
  const query = new URLSearchParams();
  query.set("days", String(days));
  query.set("limit", String(limit));
  return api.get(`/api/v1/admin/reports/errors?${query.toString()}`);
}

export function adminReportsPerformance(days = 7) {
  return api.get(`/api/v1/admin/reports/performance?days=${days}`);
}

// Public system health for the admin console.
export function fetchSystemHealth() {
  return api.get("/api/v1/health");
}

// Combined dashboard loaders.
export async function fetchUserDashboard() {
  const [readings, analytics, consultations] = await Promise.all([
    listMyReadings(),
    getMyReadingAnalytics(),
    listMyConsultations(),
  ]);
  return { readings, analytics, consultations };
}

export async function fetchReaderDashboard() {
  const [readings, analytics] = await Promise.all([readerListReadings(), readerAnalytics()]);
  return { readings, analytics };
}

export async function fetchConsultantDashboard() {
  const [queue, trends, effectiveness, insights] = await Promise.all([
    consultantListConsultations(),
    consultantTrends(),
    consultantEffectiveness(),
    consultantInsights(),
  ]);
  return { queue, trends, effectiveness, insights };
}

export async function fetchAdminDashboard(days = 7) {
  const [platform, readings, platformReadings, consultations, audit] = await Promise.all([
    adminPlatformAnalytics(days),
    adminReadingStatistics(days),
    adminListPlatformReadings(),
    adminListConsultations(),
    adminListAuditLogs(),
  ]);
  return { platform, readings, platformReadings, consultations, audit };
}

// Admin overview slice.
export async function fetchAdminOverview(days = 7) {
  const [platform, readings, sessions, audit, health] = await Promise.all([
    adminPlatformAnalytics(days),
    adminReadingStatistics(days),
    adminSessionOversight(30),
    adminListAuditLogs(),
    fetchSystemHealth(),
  ]);
  return { platform, readings, sessions, audit, health };
}

// Admin governance slice.
export async function fetchAdminGovernance() {
  const [users, permissions] = await Promise.all([adminListUsers({ limit: 200 }), adminPermissions()]);
  return { users, permissions };
}

// Admin security slice.
export async function fetchAdminSecurity(hours = 24) {
  const [errors, stats, audit] = await Promise.all([
    adminListErrors({ limit: 100 }),
    adminErrorStats(hours),
    adminListAuditLogs(),
  ]);
  return { errors, stats, audit };
}

// Admin system slice.
export async function fetchAdminSystem() {
  const [config, auth, performance, health] = await Promise.all([
    adminSystemConfig(),
    adminAuthSettings(),
    adminPerformance(),
    fetchSystemHealth(),
  ]);
  return { config, auth, performance, health };
}
