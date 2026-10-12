// Deterministic demo dataset for the consultant workspace.
// Taxonomy.
export const TREND_CATEGORIES = [
  { value: "overall", label: "Overall" },
  { value: "career", label: "Career" },
  { value: "relationships", label: "Relationships" },
  { value: "personal_growth", label: "Personal Growth" },
  { value: "opportunities", label: "Opportunities" },
  { value: "challenges", label: "Challenges" },
];

export const TREND_WINDOWS = [
  { value: "7d", label: "Last 7 Days", points: 7, stepDays: 1 },
  { value: "30d", label: "Last 30 Days", points: 10, stepDays: 3 },
  { value: "6m", label: "Last 6 Months", points: 6, stepDays: 30 },
  { value: "1y", label: "1 Year", points: 12, stepDays: 30 },
];

export const CONSULTATION_PURPOSES = [
  { value: "general_guidance", label: "General Guidance" },
  { value: "career", label: "Career" },
  { value: "relationship", label: "Relationship" },
  { value: "personal_growth", label: "Personal Growth" },
  { value: "life_direction", label: "Life Direction" },
  { value: "spiritual_development", label: "Spiritual Development" },
];

export const CLIENT_STATUS_LABELS = {
  active: "Active",
  follow_up: "Follow-up required",
  recent: "Recently consulted",
};

export const CLIENT_TREND_LABELS = {
  positive: "Positive",
  stable: "Stable",
  growth: "Growth",
  attention: "Needs attention",
};

export const PALM_FEATURES = [
  { key: "life_line", label: "Life Line" },
  { key: "head_line", label: "Head Line" },
  { key: "heart_line", label: "Heart Line" },
  { key: "fate_line", label: "Fate Line" },
  { key: "sun_line", label: "Sun Line" },
  { key: "palm_shape", label: "Palm Shape" },
  { key: "finger_structure", label: "Finger Structure" },
];

// Reading-type labels for the clients table.
export const READING_TYPE_LABELS = {
  palm: "Palm",
  tarot: "Tarot",
  "palm+tarot": "Palm + Tarot",
};

// Seeded generator.
function mulberry32(seed) {
  let a = seed >>> 0;
  return function next() {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function hashString(value) {
  let hash = 2166136261;
  for (let i = 0; i < value.length; i += 1) {
    hash ^= value.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

const DAY_MS = 24 * 60 * 60 * 1000;

function isoDaysAgo(days) {
  return new Date(Date.now() - days * DAY_MS).toISOString();
}

function pick(rand, list) {
  return list[Math.floor(rand() * list.length)];
}

function round(value, step = 1) {
  return Math.round(value / step) * step;
}

// Phrasing pools.
const PALM_INSIGHTS = {
  life_line: [
    "Strong and continuous pattern detected — vitality reads as steady across the archive.",
    "Clear arc with a noticeable break; may indicate a period of reassessment rather than loss.",
    "Deep, well-defined line; the analysis reports a consistent life-force signal.",
  ],
  head_line: [
    "Long, straight segment — suggests a methodical, evidence-first thinking style.",
    "Sloped toward the mount; could suggest an intuitive, associative reasoning pattern.",
    "Balanced curve and depth; reflective thinking reads as a stable trait.",
  ],
  heart_line: [
    "Curved line ending under the index finger — warmth and expressiveness surface as themes.",
    "Long and straight; emotional steadiness reads as a recurring reflection point.",
    "Feint but unbroken; may indicate reserved emotional expression.",
  ],
  fate_line: [
    "Present and deepening with age — a sense of direction is a recurring theme.",
    "Faint or broken; may indicate a self-directed path rather than an imposed one.",
    "Multiple influencing marks; could suggest overlapping priorities.",
  ],
  sun_line: [
    " Visible arc — recognition and creative confidence are recurring themes.",
    "Short but distinct; may indicate quiet satisfaction over public recognition.",
    "Not prominent; creative confidence reads as an area still developing.",
  ],
  palm_shape: [
    "Earth-shaped palm — grounded, practical orientation toward tangible results.",
    "Air-shaped palm — analytical and communicative orientation.",
    "Water-shaped palm — adaptive, feeling-led orientation.",
    "Fire-shaped palm — energetic, initiative-led orientation.",
  ],
  finger_structure: [
    "Balanced finger ratios with a flexible thumb — adaptability and persuasion both read as assets.",
    "Smooth joints with a firm thumb; may indicate idealism paired with determination.",
    "Knotted joints; detail-orientation reads as a dominant trait.",
  ],
};

const AI_INSIGHT_SEEDS = [
  {
    category: "Career",
    insight: "Career growth appears to be the current dominant theme across recent readings.",
    recommendation: "Anchor the next session on one concrete next step rather than a full plan.",
  },
  {
    category: "Personal Growth",
    insight: "Recent readings indicate a positive personal-development trend.",
    recommendation: "Revisit the reflection prompts the seeker responded to most strongly.",
  },
  {
    category: "Relationships",
    insight: "Relationship themes are recurring but less dominant than career in the last two readings.",
    recommendation: "Give relationships one deliberate segment so the theme does not stay implicit.",
  },
  {
    category: "Follow-up",
    insight: "A follow-up consultation may be useful after two weeks.",
    recommendation: "Offer a short follow-up slot before closing the current thread.",
  },
  {
    category: "Opportunities",
    insight: "Signals point toward a collaborative opening rather than a solo push.",
    recommendation: "Ask who the seeker could bring alongside the current goal.",
  },
  {
    category: "Challenges",
    insight: "The same friction point appears in both the palm notes and the last tarot spread.",
    recommendation: "Name the friction explicitly and check how the seeker frames it.",
  },
];

const TAROT_SUMMARIES = [
  "Positive growth indicators",
  "Mixed insights — opportunity alongside hesitation",
  "A clear turning-point pattern",
  "Reflective, inward-oriented guidance",
  "Encouraging momentum on the chosen question",
  "Caution advised around timing, not direction",
];

const TAROT_SPREADS = ["Career Spread", "Relationship Spread", "Three Card", "Celtic Cross", "Life Path"];

const TAROT_TOPICS = ["Career", "Relationships", "Personal Growth", "Life Direction", "Spiritual Development"];

const PERSONALITY_ARCHETYPES = [
  "The Builder",
  "The Seeker",
  "The Nurturer",
  "The Catalyst",
  "The Steward",
  "The Explorer",
];

const STRENGTHS = [
  "Sustained focus once a direction is chosen",
  "Comfort with ambiguity and open questions",
  "Willingness to act on small reflections",
  "Strong pattern recognition in their own behaviour",
];

const GROWTH_AREAS = [
  "Following through on the second half of a plan",
  "Asking for support earlier than feels natural",
  "Separating urgency from importance",
  "Naming a feeling before analysing it",
];

// Demo clients.
const CLIENT_SEEDS = [
  {
    id: "rahul-sharma",
    name: "Rahul Sharma",
    ageGroup: "21-25",
    location: "Pune, IN",
    interests: ["Career", "Personal Growth"],
    status: "active",
    trend: "positive",
    latestReading: "tarot",
    lastConsultationDays: 2,
    consultationCount: 6,
    readingCount: 14,
  },
  {
    id: "priya-singh",
    name: "Priya Singh",
    ageGroup: "25-34",
    location: "Bengaluru, IN",
    interests: ["Relationships", "Spiritual Development"],
    status: "follow_up",
    trend: "stable",
    latestReading: "palm",
    lastConsultationDays: 5,
    consultationCount: 9,
    readingCount: 21,
  },
  {
    id: "amit-kumar",
    name: "Amit Kumar",
    ageGroup: "21-25",
    location: "Delhi, IN",
    interests: ["Career", "Life Direction"],
    status: "recent",
    trend: "growth",
    latestReading: "palm+tarot",
    lastConsultationDays: 7,
    consultationCount: 4,
    readingCount: 11,
  },
  {
    id: "neha-iyer",
    name: "Neha Iyer",
    ageGroup: "35-44",
    location: "Chennai, IN",
    interests: ["Personal Growth", "Spiritual Development"],
    status: "active",
    trend: "positive",
    latestReading: "tarot",
    lastConsultationDays: 1,
    consultationCount: 12,
    readingCount: 27,
  },
  {
    id: "arjun-menon",
    name: "Arjun Menon",
    ageGroup: "18-24",
    location: "Kochi, IN",
    interests: ["Personal Growth"],
    status: "recent",
    trend: "attention",
    latestReading: "palm",
    lastConsultationDays: 12,
    consultationCount: 2,
    readingCount: 5,
  },
  {
    id: "kavya-desai",
    name: "Kavya Desai",
    ageGroup: "25-34",
    location: "Ahmedabad, IN",
    interests: ["Career", "Relationships"],
    status: "active",
    trend: "growth",
    latestReading: "palm+tarot",
    lastConsultationDays: 3,
    consultationCount: 7,
    readingCount: 18,
  },
];

function buildClient(seed) {
  const rand = mulberry32(hashString(seed.id));
  const metrics = {
    personalityAlignment: round(62 + rand() * 34),
    careerTrend: round(48 + rand() * 48),
    growthPotential: round(64 + rand() * 34),
    readingConsistency: round(58 + rand() * 40),
  };

  const palm = {
    analyzedAt: isoDaysAgo(round(2 + rand() * 26)),
    features: PALM_FEATURES.map((feature) => {
      const roll = rand();
      const status = roll > 0.28 ? "analyzed" : roll > 0.12 ? "partial" : "pending";
      const phrasings = PALM_INSIGHTS[feature.key] || [];
      const insight =
        status === "pending"
          ? "Not yet captured — a palm scan is required before this feature can be read."
          : pick(rand, phrasings);
      return {
        key: feature.key,
        label: feature.label,
        status,
        confidence: round((0.55 + rand() * 0.42) * 100),
        insight,
      };
    }),
  };

  const tarotHistory = Array.from({ length: 3 }).map((_, index) => {
    const daysAgo = 6 + index * 9 + Math.floor(rand() * 4);
    return {
      id: `${seed.id}-tarot-${index + 1}`,
      date: isoDaysAgo(daysAgo),
      spread: pick(rand, TAROT_SPREADS),
      topic: pick(rand, TAROT_TOPICS),
      summary: pick(rand, TAROT_SUMMARIES),
      cards: ["The Star", "Knight of Cups", "Eight of Pentacles"].slice(0, 2 + Math.floor(rand() * 2)),
      readingId: null,
    };
  });

  const aiInsights = AI_INSIGHT_SEEDS.slice(0, 4).map((item, index) => ({
    id: `${seed.id}-insight-${index + 1}`,
    category: item.category,
    insight: item.insight,
    recommendation: item.recommendation,
    relevance: round((0.62 + rand() * 0.36) * 100),
    createdAt: isoDaysAgo(index),
    reviewed: index === 0 ? rand() > 0.5 : false,
  }));

  const personality = {
    archetype: PERSONALITY_ARCHETYPES[hashString(seed.id) % PERSONALITY_ARCHETYPES.length],
    summary:
      "Blended palm and tarot signals read as consistent, with one recurring theme and no strong contradictions between the two sources.",
    alignment: metrics.personalityAlignment,
    strengths: STRENGTHS.slice(0, 2 + Math.floor(rand() * 2)),
    growthAreas: GROWTH_AREAS.slice(0, 2),
  };

  const recommendations = [
    {
      id: `${seed.id}-rec-1`,
      type: "personal_growth",
      title: "One-week reflection practice",
      text: "A short evening reflection on the theme surfaced by the last two readings.",
      priority: "high",
    },
    {
      id: `${seed.id}-rec-2`,
      type: "career",
      title: "Define the next concrete step",
      text: "Name one action that can be completed inside two weeks and review it next session.",
      priority: "medium",
    },
    {
      id: `${seed.id}-rec-3`,
      type: "spiritual_development",
      title: "Return to the practice that already works",
      text: "Reinforce an existing routine rather than adding a new one this cycle.",
      priority: "low",
    },
  ];

  const consultations = [
    {
      id: `${seed.id}-consultation-open`,
      consultationId: null,
      type: "open_thread",
      purpose: CONSULTATION_PURPOSES[hashString(seed.id) % CONSULTATION_PURPOSES.length].label,
      status: "open",
      startedAt: isoDaysAgo(1),
      durationMinutes: null,
      notes: "",
      guidance: "",
      followUpDate: null,
    },
    ...Array.from({ length: 3 }).map((_, index) => ({
      id: `${seed.id}-consultation-${index + 1}`,
      consultationId: null,
      type: "past",
      purpose: pick(rand, CONSULTATION_PURPOSES).label,
      status: "completed",
      startedAt: isoDaysAgo(14 + index * 12),
      durationMinutes: 35 + Math.floor(rand() * 40),
      notes: `Session ${index + 1}: reviewed the two most recent readings, agreed on one reflection focus for the fortnight.`,
      guidance: "Guided reflection on the dominant theme; no predictions were offered.",
      followUpDate: index === 0 ? isoDaysAgo(2) : null,
    })),
  ];

  const reports = Array.from({ length: 2 }).map((_, index) => ({
    id: `${seed.id}-report-${index + 1}`,
    clientId: seed.id,
    consultation: `${consultations[index]?.purpose || "General Guidance"} · ${new Date(
      consultations[index]?.startedAt || Date.now()
    ).toLocaleDateString()}`,
    date: consultations[index]?.startedAt || isoDaysAgo(10),
    status: index === 0 ? "ready" : "generating",
    readingId: null,
    title: `Consultation report · ${seed.name}`,
  }));

  return {
    ...seed,
    metrics,
    palm,
    tarotHistory,
    aiInsights,
    personality,
    recommendations,
    consultations,
    reports,
    lastConsultationAt: isoDaysAgo(seed.lastConsultationDays),
    latestReadingAt: isoDaysAgo(seed.lastConsultationDays + 1),
  };
}

export const DEMO_CLIENTS = CLIENT_SEEDS.map(buildClient);

// Scheduled demo sessions.
export const DEMO_UPCOMING_CONSULTATIONS = [
  {
    id: "upcoming-1",
    clientId: "rahul-sharma",
    time: "10:30",
    type: "Career Consultation",
    status: "upcoming",
    date: isoDaysAgo(0),
  },
  {
    id: "upcoming-2",
    clientId: "priya-singh",
    time: "12:00",
    type: "Relationship Consultation",
    status: "upcoming",
    date: isoDaysAgo(0),
  },
  {
    id: "upcoming-3",
    clientId: "amit-kumar",
    time: "15:30",
    type: "Personal Growth",
    status: "in_progress",
    date: isoDaysAgo(0),
  },
  {
    id: "upcoming-4",
    clientId: "neha-iyer",
    time: "09:00",
    type: "Spiritual Development",
    status: "pending",
    date: isoDaysAgo(-1),
  },
];

// Trend series.
// Deterministic trend points for one client and category.
export function demoClientTrendSeries(clientId, category, windowValue = "30d") {
  const client = getDemoClient(clientId);
  if (!client) return [];
  const win = TREND_WINDOWS.find((w) => w.value === windowValue) || TREND_WINDOWS[1];
  const rand = mulberry32(hashString(`${clientId}:${category}:${windowValue}`));

  // Baseline per category.
  const baseByCategory = {
    overall: (client.metrics.growthPotential + client.metrics.careerTrend) / 200,
    career: client.metrics.careerTrend / 100,
    relationships: 0.55 + rand() * 0.2,
    personal_growth: client.metrics.growthPotential / 100,
    opportunities: 0.5 + rand() * 0.25,
    challenges: 0.32 + rand() * 0.2,
  };
  const base = baseByCategory[category] ?? 0.6;
  const drift = (rand() - 0.35) * 0.22;

  return Array.from({ length: win.points }).map((_, index) => {
    const progress = win.points === 1 ? 1 : index / (win.points - 1);
    const value = Math.min(0.97, Math.max(0.12, base + drift * progress + (rand() - 0.5) * 0.09));
    return {
      date: isoDaysAgo(round((win.points - 1 - index) * win.stepDays)),
      value: round(value * 100) / 100,
    };
  });
}

// Roster trend series for the all-clients view.
export function demoRosterTrendSeries(category, windowValue = "30d") {
  const series = DEMO_CLIENTS.map((client) => demoClientTrendSeries(client.id, category, windowValue));
  if (series.length === 0) return [];
  const length = series[0].length;
  return Array.from({ length }).map((_, index) => {
    const values = series.map((points) => points[index]?.value ?? 0);
    const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
    return {
      date: series[0][index].date,
      value: round(mean * 100) / 100,
    };
  });
}

// Analytics payloads.
export const DEMO_GUIDANCE_BREAKDOWN = [
  { area: "Career", value: 0.89, sessions: 12 },
  { area: "Relationship", value: 0.82, sessions: 9 },
  { area: "Personal Growth", value: 0.91, sessions: 15 },
  { area: "Spiritual", value: 0.85, sessions: 7 },
];

export const DEMO_EFFECTIVENESS_OVER_TIME = [
  { period: "May", value: 0.74 },
  { period: "Jun", value: 0.78 },
  { period: "Jul", value: 0.81 },
  { period: "Aug", value: 0.8 },
  { period: "Sep", value: 0.84 },
  { period: "Oct", value: 0.86 },
];

export const DEMO_GUIDANCE_AREAS = [
  { area: "Career", count: 14 },
  { area: "Relationships", count: 11 },
  { area: "Personal Growth", count: 18 },
  { area: "Spiritual Development", count: 8 },
  { area: "Life Direction", count: 9 },
];

export const DEMO_CONSULTATION_INSIGHTS = [
  {
    id: "insight-1",
    title: "Career consultations increased by 18%",
    explanation:
      "Career is the fastest-growing theme across your consultation threads over the last two months.",
    category: "Trend",
    date: isoDaysAgo(1),
    icon: "trend",
  },
  {
    id: "insight-2",
    title: "Personal-growth readings are the most common consultation type",
    explanation:
      "Personal-growth themes appear in the largest share of the readings behind your sessions.",
    category: "Pattern",
    date: isoDaysAgo(2),
    icon: "pattern",
  },
  {
    id: "insight-3",
    title: "5 clients currently require follow-up",
    explanation:
      "Threads that received guidance but have not had a closing session yet are flagged for follow-up.",
    category: "Attention",
    date: isoDaysAgo(3),
    icon: "alert",
  },
  {
    id: "insight-4",
    title: "Most recent consultations show positive growth trends",
    explanation:
      "The last five closed sessions report an upward signal against the same clients' earlier readings.",
    category: "Outcome",
    date: isoDaysAgo(4),
    icon: "trend",
  },
];

// Demo lookups.
export function getDemoClient(clientId) {
  return DEMO_CLIENTS.find((client) => client.id === clientId) || null;
}

export function getDemoUpcoming(consultationId) {
  return DEMO_UPCOMING_CONSULTATIONS.find((item) => item.id === consultationId) || null;
}

export function getDemoReport(reportId) {
  for (const client of DEMO_CLIENTS) {
    const report = client.reports.find((item) => item.id === reportId);
    if (report) return { report, client };
  }
  return { report: null, client: null };
}
