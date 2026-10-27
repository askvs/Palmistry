import { useCallback, useEffect, useRef, useState } from "react";
import Seo from "@/components/Seo";
import { useRouter } from "next/router";
import { useAuth } from "@/hooks/useAuth";
import { useRoleGuard } from "@/hooks/useRoleGuard";
import { buildPersonalityProfile } from "@/services/personality";
import { listReadings } from "@/services/readings";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  InlineError,
  PageHeader,
  Panel,
  SkeletonCards,
  SkeletonRow,
  Spinner,
} from "@/components/ui";
import { StatCard } from "@/components/dashboards/shared";
import {
  ArrowLeftIcon,
  BrainIcon,
  CompassIcon,
  HandIcon,
  InfoIcon,
  ScanIcon,
  SparkleIcon,
  StarIcon,
  TargetIcon,
} from "@/components/icons";

// Data-viz colors for the elemental bars (accent = gold, no raw hex).
const ELEMENT_STYLES = {
  Fire: { bar: "bg-accent-500", text: "text-accent-700" },
  Water: { bar: "bg-blue-500", text: "text-blue-700" },
  Air: { bar: "bg-slate-400", text: "text-slate-600" },
  Earth: { bar: "bg-emerald-600", text: "text-emerald-700" },
  Unknown: { bar: "bg-slate-300", text: "text-slate-500" },
};

const ELEMENT_TONES = { Fire: "accent", Water: "blue", Air: "slate", Earth: "emerald" };

// Unified input class — every field on this page uses this exact string.
const INPUT_CLASS =
  "w-full rounded-[10px] border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-500 shadow-xs transition focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-500/20 disabled:cursor-not-allowed disabled:opacity-60";

const READING_DATE_FORMAT = {
  month: "short",
  day: "numeric",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
};

export default function PersonalityPage() {
  const blocked = useRoleGuard();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [readings, setReadings] = useState(null);
  const [readingsLoading, setReadingsLoading] = useState(true);
  const [readingsError, setReadingsError] = useState(null);

  const [palmReadingId, setPalmReadingId] = useState("");
  const [tarotReadingId, setTarotReadingId] = useState("");
  const [question, setQuestion] = useState("");

  const [profile, setProfile] = useState(null);
  const [building, setBuilding] = useState(false);
  const [buildError, setBuildError] = useState(null);

  // Monotonic request id so stale listReadings responses (or retries) never
  // clobber fresher state.
  const readingsRequestRef = useRef(0);

  const loadReadings = useCallback(async () => {
    const requestId = ++readingsRequestRef.current;
    setReadingsLoading(true);
    setReadingsError(null);
    try {
      const data = await listReadings({ limit: 20 });
      if (readingsRequestRef.current === requestId) setReadings(data);
    } catch (err) {
      if (readingsRequestRef.current === requestId) {
        setReadingsError(err.message || "Failed to load readings");
      }
    } finally {
      if (readingsRequestRef.current === requestId) setReadingsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/login?redirect=/personality");
    }
  }, [authLoading, user, router]);

  useEffect(() => {
    if (!user) return undefined;
    const requestId = ++readingsRequestRef.current;
    let cancelled = false;
    listReadings({ limit: 20 })
      .then((data) => {
        if (!cancelled && readingsRequestRef.current === requestId) setReadings(data);
      })
      .catch((err) => {
        if (!cancelled && readingsRequestRef.current === requestId) {
          setReadingsError(err.message || "Failed to load readings");
        }
      })
      .finally(() => {
        if (!cancelled && readingsRequestRef.current === requestId) setReadingsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  const palmReadings = (readings?.items?.filter((r) => r.type === "palm") || []).sort(
    (a, b) => new Date(b.created_at) - new Date(a.created_at)
  );
  const tarotReadings = (readings?.items?.filter((r) => r.type === "tarot") || []).sort(
    (a, b) => new Date(b.created_at) - new Date(a.created_at)
  );

  async function handleBuild() {
    setBuilding(true);
    setBuildError(null);
    setProfile(null);

    if (!palmReadingId) {
      setBuildError("Please select a palm reading");
      setBuilding(false);
      return;
    }

    const payload = { question: question.trim() || null, reading_id: palmReadingId };
    if (tarotReadingId) payload.tarot_reading_id = tarotReadingId;

    try {
      const data = await buildPersonalityProfile(payload);
      setProfile(data);
    } catch (err) {
      setBuildError(err.message || "Failed to build personality profile");
    } finally {
      setBuilding(false);
    }
  }

  if (blocked) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner label="Returning to your dashboard…" />
      </div>
    );
  }

  if (authLoading || !user) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner label="Loading your sanctuary…" />
      </div>
    );
  }

  function renderProfile() {
    if (!profile) return null;

    const elemental = profile.elemental_profile || {};
    const scores = elemental.element_scores || {};
    const dominant = elemental.dominant_element || "Unknown";
    const secondary = elemental.secondary_element;

    const sortedScores = Object.entries(scores).sort((a, b) => (b[1] || 0) - (a[1] || 0));

    return (
      <div className="animate-rise-in space-y-6">
        {/* Header: Dominant Element + Alignment + Confidence */}
        <div className="grid gap-5 sm:grid-cols-3">
          <StatCard
            label="Dominant Element"
            value={dominant}
            tone={ELEMENT_TONES[dominant] || "slate"}
            icon={SparkleIcon}
            hint={secondary ? `Secondary: ${secondary}` : "Single-element dominant profile"}
          />
          <StatCard
            label="Personality Alignment"
            value={`${profile.personality_alignment_score ?? 0}/100`}
            tone="primary"
            icon={TargetIcon}
            hint="Elemental balance × tarot harmony"
          />
          <StatCard
            label="Confidence"
            value={`${Math.round((profile.confidence || 0) * 100)}%`}
            tone="accent"
            icon={InfoIcon}
            hint={profile.provider || "rule-based"}
          />
        </div>

        {/* Elemental Balance Bars */}
        <Panel
          title="Elemental Personality Balance"
          subtitle="Fire • Water • Air • Earth — your symbolic energetic signature"
        >
          {sortedScores.length === 0 ? (
            <EmptyState
              icon={CompassIcon}
              title="No elemental data"
              description="Element scores were not part of this profile."
            />
          ) : (
            <div className="space-y-4">
              {sortedScores.map(([el, score]) => {
                const style = ELEMENT_STYLES[el] || ELEMENT_STYLES.Unknown;
                const pct = Math.max(0, Math.min(100, Number(score) || 0));
                return (
                  <div key={el} className="space-y-1.5">
                    <div className="flex items-center justify-between text-sm">
                      <span className={`font-semibold ${style.text}`}>{el}</span>
                      <span className="text-xs font-medium tabular-nums text-slate-500">
                        {pct.toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
                      <div
                        className={`h-full ${style.bar} rounded-full transition-[width] duration-[240ms]`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Panel>

        {/* Strengths */}
        <Panel title="Personality Strengths" subtitle="Natural talents and positive tendencies identified">
          {profile.strengths && profile.strengths.length > 0 ? (
            <div className="grid gap-3 sm:grid-cols-2">
              {profile.strengths.map((s, i) => (
                <div key={i} className="surface-card p-4">
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <span className="font-semibold text-slate-900">{s.trait}</span>
                    <Badge tone="emerald">{Math.round(s.confidence || 0)}%</Badge>
                  </div>
                  <p className="text-sm leading-relaxed text-slate-600">{s.description}</p>
                  <span className="mt-1 block text-[12.5px] text-slate-500">via {s.source}</span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={StarIcon}
              title="No strengths identified yet"
              description="Build another profile once you have more readings to draw from."
            />
          )}
        </Panel>

        {/* Weaknesses / Growth Areas */}
        <Panel title="Growth Areas" subtitle="Opportunities for personal development and self-awareness">
          {profile.weaknesses && profile.weaknesses.length > 0 ? (
            <div className="space-y-3">
              {profile.weaknesses.map((w, i) => (
                <div key={i} className="surface-card p-4">
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <span className="font-semibold text-slate-900">{w.area}</span>
                    <Badge tone={w.severity === "growth" || w.severity === "insight" ? "accent" : "slate"}>
                      {w.severity}
                    </Badge>
                  </div>
                  <p className="text-sm leading-relaxed text-slate-600">{w.description}</p>
                  <span className="mt-1 block text-[12.5px] text-slate-500">via {w.source}</span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={TargetIcon}
              title="No growth areas identified"
              description="Nothing was flagged for development in this profile."
            />
          )}
        </Panel>

        {/* Behavioral Insights */}
        <Panel title="Behavioral Insights" subtitle="Pattern observations derived from your readings">
          {profile.behavioral_insights && profile.behavioral_insights.length > 0 ? (
            <div className="space-y-3">
              {profile.behavioral_insights.map((insight, i) => (
                <div key={i} className="surface-card p-4">
                  <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                    <Badge tone="primary">{insight.category}</Badge>
                    <span className="text-xs font-medium text-slate-500">
                      {Math.round(insight.confidence || 0)}% confidence
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed text-slate-700">{insight.insight}</p>
                  <p className="mt-1 text-xs text-slate-500">{insight.context}</p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={InfoIcon}
              title="No behavioral insights available"
              description="Insights appear as more of your readings are analyzed."
            />
          )}
        </Panel>

        {/* Recommendations */}
        <Panel title="Personal Development Recommendations" subtitle="Guided practices for self-reflection and growth">
          {profile.recommendations && profile.recommendations.length > 0 ? (
            <div className="space-y-3">
              {profile.recommendations.map((rec, i) => (
                <div key={i} className="surface-card p-4">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <Badge tone={rec.priority === "high" ? "rose" : rec.priority === "medium" ? "accent" : "slate"}>
                      {rec.priority} priority
                    </Badge>
                    <Badge tone="slate">{rec.type}</Badge>
                  </div>
                  <p className="text-sm leading-relaxed text-slate-700">{rec.recommendation}</p>
                  <span className="mt-1 block text-[12.5px] text-slate-500">
                    category: {rec.category} — via {rec.source}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={SparkleIcon}
              title="No recommendations generated"
              description="Try building a profile with more readings included."
            />
          )}
        </Panel>

        {/* Safety Disclaimer */}
        {profile.disclaimer && (
          <p className="rounded-2xl border border-slate-200/70 bg-slate-50/60 p-4 text-center text-xs italic leading-relaxed text-slate-500">
            {profile.disclaimer}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="animate-fade-in space-y-6">
      <Seo
        title="Personality profile"
        description="Your elemental balance, strengths, growth areas, and behavioral insights — derived from your palm and tarot readings."
      />

      <PageHeader
        icon={BrainIcon}
        tileTone="primary"
        eyebrow="Inner blueprint"
        title="Personality Intelligence"
        description="Derive your personality profile from your palm analysis and tarot readings. Insights are interpretive guidance for self-reflection — not psychological diagnosis."
        actions={
          <Button href="/readings" variant="secondary" icon={ArrowLeftIcon}>
            Back to Archives
          </Button>
        }
      />

      {/* Build form */}
      <Panel
        title="Build Your Profile"
        subtitle="Pick a palm reading, optionally add a tarot draw, then generate your profile."
      >
        <div className="space-y-5">
          {readingsError ? (
            <ErrorState
              title="Couldn't load your readings"
              message={readingsError}
              onRetry={loadReadings}
            />
          ) : (
            <>
              <div>
                <label htmlFor="palm-reading" className="mb-1.5 block text-sm font-medium text-slate-700">
                  Palm reading
                </label>
                {readingsLoading ? (
                  <SkeletonRow lines={2} />
                ) : palmReadings.length === 0 ? (
                  <EmptyState
                    icon={HandIcon}
                    title="No palm readings found"
                    description="You need at least one palm scan to build a profile."
                    action={
                      <Button href="/readings/palm" variant="secondary" size="sm" icon={ScanIcon}>
                        Perform a palm scan first
                      </Button>
                    }
                  />
                ) : (
                  <select
                    id="palm-reading"
                    value={palmReadingId}
                    onChange={(e) => setPalmReadingId(e.target.value)}
                    disabled={building}
                    className={`${INPUT_CLASS} cursor-pointer`}
                  >
                    <option value="">Select a palm reading…</option>
                    {palmReadings.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.title} — {new Date(r.created_at).toLocaleString("en-US", READING_DATE_FORMAT)}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label htmlFor="tarot-reading" className="mb-1.5 block text-sm font-medium text-slate-700">
                  Tarot reading{" "}
                  <span className="font-normal text-slate-500">(optional — for a combined profile)</span>
                </label>
                {readingsLoading ? (
                  <SkeletonRow lines={2} />
                ) : tarotReadings.length === 0 ? (
                  <p className="text-sm text-slate-500">
                    No tarot readings found. You can still build a palm-only profile.
                  </p>
                ) : (
                  <select
                    id="tarot-reading"
                    value={tarotReadingId}
                    onChange={(e) => setTarotReadingId(e.target.value)}
                    disabled={building}
                    className={`${INPUT_CLASS} cursor-pointer`}
                  >
                    <option value="">No tarot reading (palm-only profile)</option>
                    {tarotReadings.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.title} — {new Date(r.created_at).toLocaleString("en-US", READING_DATE_FORMAT)}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </>
          )}

          <div>
            <label htmlFor="focus-question" className="mb-1.5 block text-sm font-medium text-slate-700">
              Focus question <span className="font-normal text-slate-500">(optional)</span>
            </label>
            <input
              id="focus-question"
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="What would you like guidance on?"
              maxLength={500}
              disabled={building}
              className={INPUT_CLASS}
            />
          </div>

          {buildError && <InlineError message={buildError} />}

          <Button onClick={handleBuild} loading={building} icon={SparkleIcon}>
            {building ? "Generating…" : "Generate Personality Profile"}
          </Button>
        </div>
      </Panel>

      {/* Results */}
      {building && <SkeletonCards count={3} />}

      {!building && !buildError && profile && renderProfile()}
    </div>
  );
}
