// Compact personality insights summary for the user dashboard (FR-035).
import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Badge, EmptyRow, SkeletonRow } from "@/components/dashboards/shared";
import { Button, InlineError } from "@/components/ui";
import { RetryIcon, SparkleIcon } from "@/components/icons";
import { buildPersonalityProfile } from "@/services/personality";

function PersonalityInsightsCard({ palmReadingId, tarotReadingId, readingsLoading }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (readingsLoading || !palmReadingId) {
      return undefined;
    }
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await buildPersonalityProfile({
          reading_id: palmReadingId,
          ...(tarotReadingId ? { tarot_reading_id: tarotReadingId } : {}),
        });
        if (!cancelled) {
          setProfile(result);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err?.message || "Failed to load personality insights");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [palmReadingId, tarotReadingId, readingsLoading]);

  if (readingsLoading) {
    return (
      <div className="p-4">
        <SkeletonRow />
      </div>
    );
  }

  if (!palmReadingId) {
    return (
      <EmptyRow>
        Personality insights are derived from your palm analysis.{" "}
        <Link href="/readings/palm" className="font-semibold text-primary-600 hover:text-primary-700">
          Complete a palm reading
        </Link>{" "}
        to unlock your personality profile.
      </EmptyRow>
    );
  }

  if (loading) {
    return (
      <div className="p-4">
        <SkeletonRow />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-3">
        <InlineError message={error} />
        <Button
          variant="secondary"
          size="sm"
          icon={RetryIcon}
          onClick={() => {
            setProfile(null);
            setError(null);
            setLoading(true);
            buildPersonalityProfile({
              reading_id: palmReadingId,
              ...(tarotReadingId ? { tarot_reading_id: tarotReadingId } : {}),
            })
              .then((result) => setProfile(result))
              .catch((e) => setError(e?.message || "Failed to load personality insights"))
              .finally(() => setLoading(false));
          }}
        >
          Retry
        </Button>
      </div>
    );
  }

  if (!profile) {
    return null;
  }

  const elemental = profile.elemental_profile || {};
  const tarot = profile.tarot_profile || {};
  const strengths = (profile.strengths || []).slice(0, 3);
  const growthAreas = (profile.weaknesses || []).slice(0, 2);
  const insight = (profile.behavioral_insights || [])[0];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="primary">
            <SparkleIcon className="h-3 w-3" /> {elemental.dominant_element || "Unknown"} nature
          </Badge>
          {tarot.personality_type && (
            <span className="text-xs text-slate-500">{tarot.personality_type}</span>
          )}
        </div>
        <span className="text-xs font-semibold text-slate-600">
          Alignment {profile.personality_alignment_score ?? 0}/100 ·{" "}
          {Math.round((profile.confidence || 0) * 100)}% confidence
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-emerald-700">
            Strengths
          </p>
          {strengths.length > 0 ? (
            <ul className="space-y-2">
              {strengths.map((s, i) => (
                <li key={i}>
                  <p className="text-sm font-semibold text-slate-900">{s.trait}</p>
                  <p className="text-xs text-slate-500 line-clamp-2">{s.description}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500 italic">No strengths identified yet.</p>
          )}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-amber-700">
            Growth Areas
          </p>
          {growthAreas.length > 0 ? (
            <ul className="space-y-2">
              {growthAreas.map((w, i) => (
                <li key={i}>
                  <p className="text-sm font-semibold text-slate-900">{w.area}</p>
                  <p className="text-xs text-slate-500 line-clamp-2">{w.description}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500 italic">No growth areas identified.</p>
          )}
        </div>
      </div>

      {insight && (
        <div className="rounded-2xl border border-primary-100 bg-primary-50/60 p-4">
          <Badge tone="primary">{insight.category}</Badge>
          <p className="mt-2 text-sm leading-relaxed text-slate-700">{insight.insight}</p>
        </div>
      )}

      <Link
        href="/personality"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary-600 hover:text-primary-700"
      >
        Open full personality profile →
      </Link>
    </div>
  );
}

export default PersonalityInsightsCard;
