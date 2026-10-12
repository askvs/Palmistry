// Consultant service: single entry point for live, demo, and local slices.
import { api } from "./api";
import {
  consultantEffectiveness,
  consultantInsights,
  consultantListConsultations,
  consultantProvideGuidance,
  consultantTrends,
} from "./roles";
import { getReadingReport } from "./reports";
import {
  DEMO_CLIENTS,
  DEMO_CONSULTATION_INSIGHTS,
  DEMO_EFFECTIVENESS_OVER_TIME,
  DEMO_GUIDANCE_AREAS,
  DEMO_GUIDANCE_BREAKDOWN,
  DEMO_UPCOMING_CONSULTATIONS,
  CONSULTATION_PURPOSES,
  demoClientTrendSeries,
  demoRosterTrendSeries,
  getDemoClient,
  getDemoReport,
} from "./consultantDemoData";
import { greeting, initialsOf, relativeDays } from "@/lib/format";
import { buildPdfBlob, downloadBlob } from "@/lib/pdf";

export { CONSULTATION_PURPOSES };

const LIVE = "live";
const DEMO = "demo";
const LOCAL = "local";

// Live client roster with guidance threads.
export async function fetchLiveClients() {
  const payload = await api.get("/api/v1/consultant/clients");
  return payload?.items || [];
}

const NOTES_STORAGE_KEY = "palmistry:consultant:notes:v1";
const SESSION_STORAGE_KEY = "palmistry:consultant:sessions:v1";

const DAY_MS = 24 * 60 * 60 * 1000;

// Small helpers.
function safeReadJson(key, fallback) {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function safeWriteJson(key, value) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Storage unavailable; notes stay in memory.
  }
}

function shortId(value = "") {
  return String(value).slice(0, 8);
}

// Roster assembly.
function liveOnlyClients(queueItems = [], liveClients = []) {
  const rosterById = new Map(liveClients.map((client) => [String(client.user_id), client]));
  const byUser = new Map();
  queueItems.forEach((item) => {
    if (!item?.user_id) return;
    const existing = byUser.get(item.user_id);
    if (!existing) {
      const profile = rosterById.get(String(item.user_id));
      byUser.set(item.user_id, {
        id: `live-${item.user_id}`,
        liveUserId: item.user_id,
        source: LIVE,
        profilePending: !profile,
        name: profile?.full_name || `Seeker ${shortId(item.user_id)}`,
        email: profile?.email || null,
        ageGroup: profile?.age_group || "—",
        location: "—",
        interests: profile?.interests || [],
        goals: profile?.goals || [],
        engagement: profile?.engagement || null,
        status: item.status === "resolved" ? "recent" : "follow_up",
        trend: "stable",
        latestReading: "—",
        lastConsultationAt: item.updated_at || item.created_at,
        latestReadingAt: profile?.engagement?.last_reading_at || null,
        consultationCount: 1,
        readingCount: profile?.engagement?.readings ?? 0,
        metrics: null,
        palm: { features: [], analyzedAt: null },
        tarotHistory: [],
        aiInsights: [],
        personality: null,
        recommendations: [],
        consultations: [],
        reports: [],
        threads: [],
      });
      return;
    }
    existing.consultationCount += 1;
    if (new Date(item.updated_at || item.created_at) > new Date(existing.lastConsultationAt)) {
      existing.lastConsultationAt = item.updated_at || item.created_at;
    }
  });

  byUser.forEach((client) => {
    client.threads = queueItems
      .filter((item) => item.user_id === client.liveUserId)
      .map((item) => ({
        id: item.id,
        liveConsultationId: item.id,
        purpose: item.topic,
        status: item.status,
        startedAt: item.created_at,
        message: item.message,
        guidance: item.guidance,
        notes: "",
        followUpDate: null,
        type: "live_thread",
      }));
    client.consultations = client.threads;
  });

  return [...byUser.values()];
}

function demoClientView(client) {
  return {
    ...client,
    source: DEMO,
    profilePending: false,
    liveUserId: null,
    metrics: client.metrics,
    threads: [],
  };
}

// Dashboard.
async function fetchLiveQueue() {
  try {
    const queue = await consultantListConsultations();
    return { queue: queue || { items: [], total: 0 }, error: null };
  } catch (error) {
    return { queue: null, error };
  }
}

async function fetchLiveInsights() {
  const [effectiveness, trends, insights] = await Promise.allSettled([
    consultantEffectiveness(),
    consultantTrends(),
    consultantInsights(),
  ]);
  return {
    effectiveness: effectiveness.status === "fulfilled" ? effectiveness.value : null,
    trends: trends.status === "fulfilled" ? trends.value : null,
    insights: insights.status === "fulfilled" ? insights.value : null,
  };
}

// Assembled dashboard payload: queue, insights, roster, sessions.
async function fetchConsultantWorkspaceData() {
  const [{ queue, error }, live, bookings, liveClients] = await Promise.all([
    fetchLiveQueue(),
    fetchLiveInsights(),
    fetchConsultantBookings(),
    fetchLiveClients().catch(() => []),
  ]);

  const queueItems = queue?.items || [];
  const roster = [
    ...DEMO_CLIENTS.map(demoClientView),
    ...liveOnlyClients(queueItems, liveClients),
  ];

  const pendingFollowUps = roster.filter((client) => client.status === "follow_up").length;
  const openThreads = queueItems.filter((item) => item.status !== "resolved").length;

  const monthStart = new Date();
  monthStart.setDate(1);
  monthStart.setHours(0, 0, 0, 0);
  const thisMonth = queueItems.filter((item) => new Date(item.created_at) >= monthStart).length;

  const scheduled = bookings
    ? bookings.map(mapBookingToSession)
    : DEMO_UPCOMING_CONSULTATIONS.filter((item) => {
        const when = new Date(item.date);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return when >= today;
      });

  return {
    source: queue ? LIVE : DEMO,
    error,
    queue,
    effectiveness: live.effectiveness,
    trends: live.trends,
    insights: live.insights,
    roster,
    scheduled,
    scheduledSource: bookings ? LIVE : DEMO,
    summary: {
      activeClients: roster.length,
      activeClientsLive: roster.filter((client) => client.source === LIVE).length,
      consultationsThisMonth: thisMonth,
      guidanceEffectiveness: live.effectiveness ? live.effectiveness.resolution_rate : null,
      pendingFollowUps,
      openThreads,
      awaitingReply: live.effectiveness?.awaiting_reply ?? 0,
      avgFirstResponseMinutes: live.effectiveness?.avg_first_response_minutes ?? null,
    },
    greeting: greeting(),
  };
}

// Public dashboard loader.
export async function fetchConsultantWorkspace() {
  return fetchConsultantWorkspaceData();
}

// Scheduled sessions, with demo calendar fallback.
export async function fetchConsultantBookings() {
  if (typeof window === "undefined") return null;
  try {
    const payload = await api.get("/api/v1/consultants/me/bookings");
    const items = payload?.items || payload?.bookings || [];
    return Array.isArray(items) ? items : [];
  } catch {
    return null;
  }
}

function mapBookingToSession(booking) {
  const start = new Date(booking.start_time);
  return {
    id: `booking-${booking.id}`,
    clientId: null,
    liveClientName: booking.seeker_name || booking.seeker_email || "Seeker",
    liveClientUserId: booking.seeker_user_id || null,
    time: start.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false }),
    date: booking.start_time,
    type: booking.subject || "Consultation",
    status: mapBookingStatus(booking.status),
  };
}

function mapBookingStatus(status) {
  if (status === "accepted") return "upcoming";
  if (status === "pending") return "pending";
  if (status === "completed") return "completed";
  if (status === "rejected" || status === "cancelled") return "pending";
  return "upcoming";
}

// Clients.
export async function fetchConsultantClients({ search = "", status = "all", sort = "recent" } = {}) {
  const { roster, source } = await fetchConsultantWorkspace();
  const query = search.trim().toLowerCase();

  let clients = roster.filter((client) => {
    if (status !== "all" && client.status !== status) return false;
    if (!query) return true;
    return (
      client.name.toLowerCase().includes(query) ||
      client.interests.some((interest) => interest.toLowerCase().includes(query)) ||
      (client.latestReading || "").toLowerCase().includes(query)
    );
  });

  clients = [...clients].sort((a, b) => {
    if (sort === "name") return a.name.localeCompare(b.name);
    if (sort === "consultations") return b.consultationCount - a.consultationCount;
    return new Date(b.lastConsultationAt || 0) - new Date(a.lastConsultationAt || 0);
  });

  return { source, clients, total: clients.length };
}

export async function fetchConsultantClient(clientId) {
  const { roster, queue, source } = await fetchConsultantWorkspace();
  const client = roster.find((item) => item.id === clientId) || null;
  if (!client) return { source, client: null, queue };

  const notes = loadClientNotes(client.id);

  return {
    source,
    queue,
    client: {
      ...client,
      initials: initialsOf(client.name),
      lastConsultationDays: relativeDays(client.lastConsultationAt),
      savedNotes: notes,
    },
  };
}

// Trend series.
export async function fetchClientTrendSeries({ clientId = "all", category = "overall", window: windowValue = "30d" }) {
  const points =
    clientId === "all" || !clientId
      ? demoRosterTrendSeries(category, windowValue)
      : demoClientTrendSeries(clientId, category, windowValue);

  return {
    source: DEMO,
    category,
    window: windowValue,
    clientId,
    points,
  };
}

// Insights.
export async function fetchGuidanceEffectiveness() {
  const { effectiveness } = await fetchConsultantWorkspace();
  return {
    source: DEMO,
    overall: effectiveness?.resolution_rate ?? 0.86,
    breakdown: DEMO_GUIDANCE_BREAKDOWN,
    overTime: DEMO_EFFECTIVENESS_OVER_TIME,
    guidanceAreas: DEMO_GUIDANCE_AREAS,
    live: effectiveness,
  };
}

export async function fetchConsultationInsightFeed() {
  const { insights, trends, roster } = await fetchConsultantWorkspace();

  const livePen = (insights?.top_topics || []).map((topic) => ({
    id: `live-topic-${topic.topic}`,
    title: `${topic.topic} is the most frequent inquiry theme`,
    explanation: `${topic.count} consultation thread(s) on the platform open with this topic.`,
    category: "Live theme",
    date: null,
    icon: "pattern",
  }));

  return {
    source: insights?.total_requests ? LIVE : DEMO,
    items: [...livePen, ...DEMO_CONSULTATION_INSIGHTS],
    live: insights,
    trends,
    roster,
  };
}

// Consultations.
function loadSessions() {
  return safeReadJson(SESSION_STORAGE_KEY, {});
}

function buildLocalSessionPayload(sessionId) {
  const session = loadSessions()[sessionId] || null;
  const client = session ? getDemoClient(session.clientId) : null;
  return {
    source: session ? LOCAL : DEMO,
    session,
    client,
    liveConsultation: null,
    demoConsultations: client?.consultations || [],
  };
}

function saveSessions(sessions) {
  safeWriteJson(SESSION_STORAGE_KEY, sessions);
}

// Start a local consultation session.
export async function startConsultationSession({ clientId, purpose }) {
  const sessions = loadSessions();
  const id = `session-${Date.now()}`;
  const client = getDemoClient(clientId);
  const session = {
    id,
    clientId,
    clientName: client?.name || clientId,
    purpose: purpose || "General Guidance",
    status: "in_progress",
    startedAt: new Date().toISOString(),
    notes: "",
    guidance: "",
    followUpDate: null,
    source: LOCAL,
  };
  sessions[id] = session;
  saveSessions(sessions);
  return { session };
}

export async function fetchConsultationSessions() {
  return { source: LOCAL, sessions: Object.values(loadSessions()) };
}

export async function fetchConsultationSession(sessionId) {
  return buildLocalSessionPayload(sessionId);
}

// Resolve a consultation id to local, live, or demo session.
export async function fetchConsultationWorkspace(consultationId) {
  const local = loadSessions()[consultationId];
  if (local) {
    return buildLocalSessionPayload(local.id);
  }

  const { queue, roster } = await fetchConsultantWorkspaceData();

  const liveConsultation = (queue?.items || []).find((item) => item.id === consultationId) || null;
  if (liveConsultation) {
    const client =
      roster.find((item) => item.liveUserId === liveConsultation.user_id) || null;
    return {
      source: LIVE,
      session: {
        id: liveConsultation.id,
        clientId: client?.id || null,
        clientName: client?.name || `Seeker ${shortId(liveConsultation.user_id)}`,
        purpose: liveConsultation.topic,
        status: liveConsultation.status,
        startedAt: liveConsultation.created_at,
        notes: "",
        guidance: liveConsultation.guidance || "",
        followUpDate: null,
        liveConsultationId: liveConsultation.id,
        liveMessage: liveConsultation.message,
      },
      client,
      liveConsultation,
      demoConsultations: client?.consultations || [],
    };
  }

  for (const demoClient of DEMO_CLIENTS) {
    const demoSession = demoClient.consultations.find((item) => item.id === consultationId);
    if (demoSession) {
      return {
        source: DEMO,
        session: { ...demoSession, clientName: demoClient.name },
        client: demoClient,
        liveConsultation: null,
        demoConsultations: demoClient.consultations,
      };
    }
  }

  return { source: DEMO, session: null, client: null, liveConsultation: null, demoConsultations: [] };
}

// Persist consultant notes locally.
export async function saveConsultationNotes(sessionId, { notes, guidance, followUpDate, status }) {
  const sessions = loadSessions();
  const existing = sessions[sessionId];
  if (!existing) return { source: LOCAL, session: null };

  const updated = {
    ...existing,
    notes: notes ?? existing.notes,
    guidance: guidance ?? existing.guidance,
    followUpDate: followUpDate ?? existing.followUpDate,
    status: status || existing.status,
    updatedAt: new Date().toISOString(),
  };
  sessions[sessionId] = updated;
  saveSessions(sessions);
  return { source: LOCAL, session: updated };
}

function loadClientNotes(clientId) {
  const all = safeReadJson(NOTES_STORAGE_KEY, {});
  return all[clientId] || "";
}

export async function fetchClientNotes(clientId) {
  return { source: LOCAL, notes: loadClientNotes(clientId) };
}

export async function saveClientNotes(clientId, notes) {
  const all = safeReadJson(NOTES_STORAGE_KEY, {});
  all[clientId] = notes;
  safeWriteJson(NOTES_STORAGE_KEY, all);
  return { source: LOCAL, notes };
}

// Send guidance through the live consultant API.
export async function sendConsultantGuidance(liveConsultationId, { guidance, status }) {
  const updated = await consultantProvideGuidance(liveConsultationId, { guidance, status });
  return { source: LIVE, consultation: updated };
}

// Reports.
export async function fetchConsultationReports({ clientId = "", status = "all" } = {}) {
  let rows = [];
  DEMO_CLIENTS.forEach((client) => {
    if (clientId && client.id !== clientId) return;
    client.reports.forEach((report) => {
      rows.push({
        ...report,
        clientName: client.name,
        clientId: client.id,
        source: report.readingId ? LIVE : DEMO,
      });
    });
  });

  if (status !== "all") {
    rows = rows.filter((report) => report.status === status);
  }

  rows.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));
  return { source: DEMO, reports: rows, total: rows.length };
}

// Export a report via backend PDF or local fallback.
export async function downloadConsultationReport(reportId) {
  const { report, client } = getDemoReport(reportId);
  if (!report || !client) {
    throw new Error("That report is no longer available.");
  }

  if (report.readingId) {
    const { downloadReportPdf } = await import("./reports");
    await downloadReportPdf(report.readingId, `${client.id}-report.pdf`);
    return { source: LIVE };
  }

  const insightLines = (client.aiInsights || []).map(
    (insight, i) => `${i + 1}. [${insight.category}] ${insight.insight} — ${insight.recommendation || "No follow-up recorded."}`
  );
  const tarotLines = (client.tarotHistory || []).map(
    (entry) => `• ${String(entry.date || "").slice(0, 10)} · ${entry.spread} · ${entry.topic} — ${entry.summary}`
  );
  const consultLines = (client.consultations || []).slice(0, 4).map(
    (s) => `• ${String(s.startedAt || "").slice(0, 10)} · ${s.purpose} (${s.status}) — ${s.notes || s.guidance || "Session recorded."}`
  );
  const recLines = (client.recommendations || []).map(
    (r, i) => `${i + 1}. ${r.title} [${r.priority}] — ${r.text}`
  );

  const blob = buildPdfBlob({
    title: `Consultation Report · ${client.name}`,
    subtitle: report.consultation || report.title || "Consultation summary",
    meta: [
      `Generated: ${new Date().toLocaleString()}`,
      `Client: ${client.name} (${client.id}) · ${client.location || ""} · Status: ${report.status}`,
      `Report: ${report.title || report.id} · Date: ${String(report.date || "").slice(0, 10)}`,
      "Source: consultant workspace (demo dataset) — backend PDF is used automatically when a live reading exists",
    ],
    sections: [
      {
        heading: "Client snapshot",
        lines: [
          `Interests: ${(client.interests || []).join(", ") || "—"}.`,
          `Personality: ${client.personality?.archetype || "—"} — ${client.personality?.summary || ""}`,
          `Strengths: ${(client.personality?.strengths || []).join("; ") || "—"}.`,
          `Growth areas: ${(client.personality?.growthAreas || []).join("; ") || "—"}.`,
          client.metrics
            ? `Metrics — alignment ${client.metrics.personalityAlignment} · career ${client.metrics.careerTrend} · growth ${client.metrics.growthPotential} · consistency ${client.metrics.readingConsistency}.`
            : "",
        ],
      },
      {
        heading: "Guidance summary",
        lines:
          insightLines.length > 0
            ? insightLines
            : ["No AI insights were attached to this session."],
      },
      {
        heading: "Recommendations",
        lines: recLines.length > 0 ? recLines : ["No recommendations recorded for this client yet."],
      },
      {
        heading: "Reading context",
        lines: [
          `Latest reading: ${client.latestReading || "—"} · ${client.readingCount || 0} readings · ${client.consultationCount || 0} consultations.`,
          ...(tarotLines.length > 0 ? tarotLines : ["No tarot history recorded."]),
        ],
      },
      {
        heading: "Recent sessions",
        lines: consultLines.length > 0 ? consultLines : ["No past sessions recorded."],
      },
    ],
    footer:
      "Interpretive guidance for self-reflection only. Not medical, financial or legal advice, and not a guaranteed prediction.",
  });

  const safeClient = String(client.id || "client").toLowerCase().replace(/[^\w-]+/g, "-") || "client";
  const datePart = String(report.date || new Date().toISOString()).slice(0, 10);
  downloadBlob(blob, `${safeClient}-consultation-report-${datePart}.pdf`);
  return { source: DEMO };
}

// Palm and tarot detail.
// Demo palm summary; no per-seeker endpoint exists yet.
export async function fetchClientPalmSummary(clientId) {
  const client = getDemoClient(clientId);
  if (!client) return { source: DEMO, palm: null };
  return { source: DEMO, palm: client.palm };
}

export async function fetchClientTarotHistory(clientId) {
  const client = getDemoClient(clientId);
  if (!client) return { source: DEMO, rows: [] };
  return {
    source: DEMO,
    rows: client.tarotHistory.map((entry) => ({ ...entry, readingId: entry.readingId })),
  };
}

// Demo AI insights for a client.
export async function fetchClientAIInsights(clientId) {
  const client = getDemoClient(clientId);
  if (!client) return { source: DEMO, insights: [] };
  return { source: DEMO, insights: client.aiInsights };
}

// Structured reading report for a live reading id.
export async function fetchReadingReport(readingId) {
  if (!readingId) return null;
  try {
    return await getReadingReport(readingId);
  } catch {
    return null;
  }
}

// Status labels.
export const CONSULTANT_STATUS_LABELS = {
  upcoming: "Upcoming",
  in_progress: "In progress",
  completed: "Completed",
  pending: "Pending",
  open: "Open",
  in_review: "In review",
  resolved: "Resolved",
};

export { initialsOf, relativeDays };
