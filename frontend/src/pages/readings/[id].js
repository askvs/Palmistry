import React, { useEffect, useState } from "react";
import Head from "next/head";
import Image from "next/image";
import { useRouter } from "next/router";
import { useAuth } from "../../hooks/useAuth";
import { getReading, updateReading, deleteReading } from "../../services/readings";
import { interpretPalm, interpretTarot } from "../../services/readings";
import { downloadReportPdf, downloadReportExcel } from "../../services/reports";
import { generateRecommendations } from "../../services/recommendations";
import ChatBot from "../../components/ai/ChatBot";
import AiInsightsPanel from "@/components/ai/AiInsightsPanel";
import RecommendationsSection from "@/components/recommendations/RecommendationsSection";
import ReadingAnalysisPanel from "@/components/tarot/ReadingAnalysisPanel";
import PalmAnalysisDetails, { PalmLinesList } from "@/components/palm/PalmAnalysisDetails";
import {
  Badge,
  Button,
  ConfirmDialog,
  ErrorState,
  InlineError,
  Panel,
  SkeletonCards,
  useToast,
} from "@/components/ui";
import {
  ArrowLeftIcon,
  FileTextIcon,
  PencilIcon,
  TableIcon,
  TrashIcon,
} from "@/components/icons";

const NOTES_MAX_LENGTH = 10000;

export default function ReadingDetailPage() {
  const router = useRouter();
  const queryId = router.query.id;
  const { user, loading: authLoading } = useAuth();
  const toast = useToast();

  const [reading, setReading] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [notes, setNotes] = useState("");
  const [notesError, setNotesError] = useState(null);
  const [savingNotes, setSavingNotes] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(null);

  const loadReading = React.useCallback(async () => {
    if (!queryId) return;
    try {
      const data = await getReading(queryId);
      setReading(data);
      setNotes(data.notes || "");
      setError(null);
    } catch (err) {
      setError(err.message || "Failed to load reading details");
    } finally {
      setLoading(false);
    }
  }, [queryId]);

  useEffect(() => {
    if (!queryId) return undefined;
    if (!authLoading && !user) {
      router.push(`/login?redirect=/readings/${queryId}`);
      return undefined;
    }
    if (!user) {
      return undefined;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await getReading(queryId);
        if (!cancelled) {
          setReading(data);
          setNotes(data.notes || "");
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || "Failed to load reading details");
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
  }, [queryId, user, authLoading, router]);

  const isPalm = reading?.type === "palm";
  const result = reading?.result || {};
  const narrativeBody = Array.isArray(result.narrative?.body) ? result.narrative.body : [];

  // Opt-in only: the AI model is never called on page open. A saved
  // interpretation (persisted by the interpret endpoints) renders directly;
  // otherwise the panel shows a "Generate AI Insight" call-to-action.
  const aiInterpretation = result.ai_interpretation || null;

  async function handleGenerateInsight() {
    if (!reading || aiLoading) return;
    setAiLoading(true);
    setAiError(null);
    try {
      const aiData = isPalm ? await interpretPalm(queryId) : await interpretTarot(queryId);
      if (aiData) {
        setReading((prev) => ({
          ...prev,
          result: { ...(prev?.result || {}), ai_interpretation: aiData },
        }));
      }
    } catch (err) {
      setAiError(err.message || "AI interpretation failed. Please try again.");
    } finally {
      setAiLoading(false);
    }
  }

  async function handleSaveNotes() {
    if (notes.length > NOTES_MAX_LENGTH) {
      setNotesError(
        `Notes are limited to ${NOTES_MAX_LENGTH.toLocaleString()} characters. Please shorten your reflection before saving.`
      );
      return;
    }
    setNotesError(null);
    setSavingNotes(true);
    try {
      await updateReading(queryId, { notes });
      toast.success("Notes saved", "Your reflections have been saved to this reading.");
    } catch (err) {
      setNotesError(err.message || "Could not save notes. Please try again in a moment.");
    } finally {
      setSavingNotes(false);
    }
  }

  async function handleDelete() {
    setActionLoading("delete");
    try {
      await deleteReading(queryId);
      toast.success("Reading deleted", "This reading has been removed from your archive.");
      setDeleteOpen(false);
      router.push("/readings");
    } catch (err) {
      toast.error(
        "Delete failed",
        `${err.message || "The reading could not be removed."} Check your connection and try again.`
      );
      setActionLoading(null);
    }
  }

  async function handleDownloadPdf() {
    setActionLoading("pdf");
    try {
      await downloadReportPdf(queryId, `${reading?.title || "reading"}-dossier.pdf`);
      toast.success("PDF dossier exported", "Your reading dossier has been downloaded.");
    } catch (err) {
      toast.error(
        "Export failed",
        `${err.message || "The PDF report could not be generated."} Check your connection and try again.`
      );
    } finally {
      setActionLoading(null);
    }
  }

  async function handleDownloadExcel() {
    setActionLoading("excel");
    try {
      await downloadReportExcel(queryId, `${reading?.title || "reading"}-data.xlsx`);
      toast.success("Excel workbook exported", "Your reading analysis has been downloaded.");
    } catch (err) {
      toast.error(
        "Export failed",
        `${err.message || "The Excel workbook could not be generated."} Check your connection and try again.`
      );
    } finally {
      setActionLoading(null);
    }
  }

  return (
    <div className="space-y-8">
      <Head>
        <title>{reading ? `${reading.title} | MysticLens` : "Reading Details | MysticLens"}</title>
      </Head>

      {/* Page Header: breadcrumb + export actions */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2 text-sm">
          <Button variant="ghost" size="sm" href="/readings" icon={ArrowLeftIcon}>
            Archives
          </Button>
          <span className="text-slate-300" aria-hidden="true">
            /
          </span>
          <span className="truncate font-display text-sm font-semibold text-slate-800">
            {reading?.title || "Reading"}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            icon={FileTextIcon}
            onClick={handleDownloadPdf}
            loading={actionLoading === "pdf"}
            disabled={Boolean(actionLoading) || !reading}
          >
            Export PDF
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={TableIcon}
            onClick={handleDownloadExcel}
            loading={actionLoading === "excel"}
            disabled={Boolean(actionLoading) || !reading}
          >
            Export Excel
          </Button>
        </div>
      </div>

      <main className="mt-8">
        {/* 1. LOADING STATE */}
        {loading && <SkeletonCards count={3} />}

        {/* 2. ERROR STATE */}
        {!loading && error && (
          <div className="space-y-4">
            <ErrorState
              title="Failed to retrieve reading"
              message={error}
              onRetry={() => {
                setLoading(true);
                loadReading();
              }}
            />
            <div className="flex justify-center">
              <Button variant="secondary" size="sm" href="/readings" icon={ArrowLeftIcon}>
                Return to Archives
              </Button>
            </div>
          </div>
        )}

        {/* 3. SUCCESS STATE */}
        {!loading && reading && (
          <div className="space-y-10">
            {/* Top Overview Hero */}
            <div className="relative overflow-hidden rounded-3xl border border-slate-200/90 bg-white p-8 shadow-xs">
              <div className="pointer-events-none absolute -right-20 -top-20 h-80 w-80 rounded-full bg-primary-100/60 blur-3xl" />

              <div className="relative">
                <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <Badge tone={isPalm ? "accent" : "primary"}>
                      {isPalm ? "Palmistry Biometric Scan" : "Tarot Symbolic Reading"}
                    </Badge>
                    <Badge tone="emerald">{reading.status}</Badge>
                  </div>

                  <div className="text-xs text-slate-400">
                    {reading.created_at ? new Date(reading.created_at).toLocaleString() : ""}
                  </div>
                </div>

                <h1 className="mb-3 font-display text-2xl font-bold text-slate-900 sm:text-3xl">
                  {reading.title}
                </h1>
                <p className="max-w-3xl text-sm leading-relaxed text-slate-600">{reading.summary}</p>
              </div>
            </div>

            {/* Palm reading details. */}
            {isPalm && (
              <div className="space-y-8">
                {/* Palm Shape & Biometrics */}
                {result.palm_shape && (
                  <Panel
                    title="Elemental Hand Morphology"
                    action={<Badge tone="accent">{result.palm_shape.element} Hand</Badge>}
                  >
                    <p className="mb-4 text-xs leading-relaxed text-slate-600">
                      {result.palm_shape.description}
                    </p>
                    {result.hand?.is_palmar === false && (
                      <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-relaxed text-amber-800">
                        Back-of-hand (dorsal) view detected — line creases are naturally less
                        visible from this angle, so lower line confidences are expected.
                      </div>
                    )}
                    <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
                      {[
                        ["Detected Hand", result.hand?.detected_handedness || "—"],
                        [
                          "Handedness Confidence",
                          result.hand?.handedness_confidence != null
                            ? `${Math.round(result.hand.handedness_confidence * 100)}%`
                            : "—",
                        ],
                        ["Landmarks Tracked", result.hand?.landmarks_count ?? "—"],
                        ["Aspect Ratio", result.palm_shape.aspect_ratio ?? "—"],
                        [
                          "Overall Confidence",
                          result.metadata?.overall_confidence != null
                            ? `${Math.round(result.metadata.overall_confidence * 100)}%`
                            : "—",
                        ],
                        ["Palm Width", result.palm_shape.palm_width ?? "—"],
                        ["Palm Height", result.palm_shape.palm_height ?? "—"],
                        [
                          "Finger-to-Palm Ratio",
                          result.palm_shape.finger_to_palm_ratio ?? "—",
                        ],
                      ].map(([label, value]) => (
                        <div key={label} className="rounded-xl border border-slate-200 bg-slate-50/70 p-3">
                          <div className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
                            {label}
                          </div>
                          <div className="mt-0.5 font-bold text-slate-900">{value}</div>
                        </div>
                      ))}
                    </div>
                  </Panel>
                )}

                {/* Primary Lines Breakdown (measured, array-shaped pipeline payload) */}
                {Array.isArray(result.lines) && result.lines.length > 0 && (
                  <div>
                    <h2 className="mb-1 font-display text-xl font-bold text-slate-900">
                      Primary Palm Lines ({result.lines.length})
                    </h2>
                    <p className="mb-4 text-xs text-slate-500">
                      Measured depth, length, and continuity from your photo — lines not clearly
                      detected are shown honestly rather than guessed.
                    </p>
                    <PalmLinesList lines={result.lines} />
                  </div>
                )}

                {/* Finger structure + planetary mount profiles */}
                <PalmAnalysisDetails result={result} />
              </div>
            )}

            {/* Tarot reading details. */}
            {!isPalm && (
              <div className="space-y-8">
                {/* Inquiry context */}
                <div className="rounded-2xl border border-primary-200 bg-primary-50/60 p-6">
                  <div className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-primary-600">
                    Querent Inquiry
                  </div>
                  <div className="font-display text-lg italic text-slate-900">
                    &ldquo;{result.question || "General Spiritual Reflection"}&rdquo;
                  </div>
                  <div className="mt-2 text-xs text-slate-500">
                    Spread: <strong className="text-slate-700">{result.spread_name || "Custom Spread"}</strong>
                  </div>
                </div>

                {/* Spread-level analysis diagnostics (arcana, elements, reversals, numerology) */}
                <ReadingAnalysisPanel analysis={result.analysis} />

                {/* Cards Drawn Grid */}
                {result.cards && (
                  <div>
                    <h2 className="mb-4 font-display text-xl font-bold text-slate-900">
                      Cards Drawn &amp; Position Interpretations
                    </h2>
                    <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                      {result.cards.map((card, idx) => {
                        const isRev = card.is_reversed || card.orientation === "reversed";
                        const posName =
                          card.position_name || card.position?.name || `Position ${card.position || idx + 1}`;
                        const posMeaning =
                          card.position_description ||
                          card.position?.meaning ||
                          "Guiding force";

                        return (
                          <div
                            key={idx}
                            className="flex flex-col justify-between rounded-2xl border border-slate-200/90 bg-white p-5 shadow-xs transition hover:border-primary-300"
                          >
                            <div>
                              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                                <Badge tone="primary">{posName}</Badge>
                                <Badge tone={isRev ? "accent" : "emerald"}>
                                  {isRev ? "Reversed" : "Upright"}
                                </Badge>
                              </div>

                              <div className="mb-3 flex items-start gap-4">
                                {card.image_path && (
                                  <div className="relative h-26 w-16 shrink-0 overflow-hidden rounded-lg border border-slate-200 shadow-sm">
                                    <Image
                                      src={`/${card.image_path.replace(/^\/+/, "")}`}
                                      alt={card.card_name || card.name || "Tarot card"}
                                      fill
                                      className={`object-cover ${isRev ? "rotate-180" : ""}`}
                                      sizes="64px"
                                    />
                                  </div>
                                )}
                                <div className="min-w-0 flex-1">
                                  <h3 className="mb-0.5 font-display text-base font-bold text-slate-900">
                                    {card.card_name || card.name}
                                  </h3>
                                  <div className="mb-1.5 text-[11px] italic text-slate-500">
                                    {card.arcana} {card.suit && card.suit !== "None" ? `• ${card.suit}` : ""}
                                  </div>
                                  <div className="text-xs text-slate-500">
                                    <span className="text-slate-400">Role:</span> {posMeaning}
                                  </div>
                                </div>
                              </div>

                              <p className="mb-4 text-xs leading-relaxed text-slate-600">
                                {card.position_context ||
                                  card.core_meaning ||
                                  card.interpretation ||
                                  card.meaning ||
                                  "Archetypal resonance guiding your path."}
                              </p>
                            </div>

                            {card.keywords && (
                              <div className="flex flex-wrap gap-1 border-t border-slate-100 pt-3">
                                {card.keywords.map((kw, kIdx) => (
                                  <span
                                    key={kIdx}
                                    className="rounded bg-slate-100 px-2 py-0.5 text-[10px] text-slate-600"
                                  >
                                    {kw}
                                  </span>
                                ))}
                              </div>
                            )}

                            {/* Domain-specific guidance (love / career / spiritual) */}
                            {card.domain_guidance?.length > 0 && (
                              <div className="mt-3 space-y-2 border-t border-slate-100 pt-3">
                                {card.domain_guidance.map((g, gIdx) => (
                                  <div key={g.domain || gIdx}>
                                    <div className="text-[9px] font-bold uppercase tracking-wider text-primary-600">
                                      {g.label || g.domain}
                                    </div>
                                    <p className="mt-0.5 text-[11px] leading-relaxed text-slate-600">
                                      {g.text}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            )}

                            {/* Deeper symbolism for the current orientation */}
                            {card.expanded_meanings?.length > 0 && (
                              <div className="mt-3 border-t border-slate-100 pt-3">
                                <div className="text-[9px] font-bold uppercase tracking-wider text-slate-500">
                                  {isRev ? "Shadow Insights" : "Light Insights"}
                                </div>
                                <ul className="mt-1 space-y-1 text-[11px] leading-relaxed text-slate-600">
                                  {card.expanded_meanings.map((m, mIdx) => (
                                    <li key={mIdx} className="flex items-start gap-1.5">
                                      <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-primary-300" />
                                      <span>{m}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Synthesis & Guidance */}
                {result.narrative && (
                  <div className="space-y-4 rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs">
                    <h2 className="font-display text-lg font-bold text-primary-700">
                      Spread Synthesis &amp; Thematic Journey
                    </h2>
                    <p className="text-sm leading-relaxed text-slate-600">
                      {result.narrative.summary || result.narrative.full_text}
                    </p>

                    {narrativeBody.length > 0 && (
                      <ul className="space-y-2">
                        {narrativeBody.map((line, bIdx) => (
                          <li key={bIdx} className="flex items-start gap-2.5 text-xs leading-relaxed text-slate-600">
                            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary-400" />
                            <span>{line}</span>
                          </li>
                        ))}
                      </ul>
                    )}

                    {result.narrative.closing && (
                      <p className="border-t border-primary-100 pt-3 text-xs italic leading-relaxed text-primary-800/80">
                        {result.narrative.closing}
                      </p>
                    )}

                    {result.guidance && result.guidance.length > 0 && (
                      <div className="border-t border-slate-100 pt-4">
                        <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-accent-700">
                          Actionable Reflection Steps
                        </div>
                        <ul className="space-y-1.5 text-xs text-slate-600">
                          {result.guidance.map((step, sIdx) => (
                            <li key={sIdx} className="flex items-start gap-2">
                              <span className="text-accent-500" aria-hidden="true">
                                •
                              </span>
                              <span>{step}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* User reflections and notes. */}
            <Panel
              title="Personal Journal & Integration Notes"
              subtitle="Record how this reading resonates with you and revisit it over time."
            >
              <label
                htmlFor="reading-notes"
                className="mb-2 block text-xs font-semibold uppercase tracking-wider text-slate-500"
              >
                Your reflections
              </label>
              <textarea
                id="reading-notes"
                rows={4}
                placeholder="Write your reflections, synchronicities, or realization notes for this reading..."
                value={notes}
                onChange={(e) => {
                  setNotes(e.target.value);
                  if (notesError) setNotesError(null);
                }}
                className="w-full cursor-text rounded-xl border border-slate-200 bg-slate-50/70 p-3 text-sm text-slate-800 placeholder-slate-400 transition focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100"
              />
              <InlineError message={notesError} className="mt-3" />
              <div className="mt-3 flex justify-end">
                <Button
                  variant="accent"
                  size="sm"
                  icon={PencilIcon}
                  onClick={handleSaveNotes}
                  loading={savingNotes}
                >
                  Save Reflections
                </Button>
              </div>
            </Panel>

            {/* AI interpretation. */}
            <AiInsightsPanel
              readingTypeLabel={isPalm ? "palm reading" : "tarot reading"}
              loading={aiLoading}
              error={aiError}
              interpretation={aiInterpretation}
              onGenerate={handleGenerateInsight}
            />

            {/* Bottom Controls */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-6">
              <Button variant="ghost" size="sm" href="/readings" icon={ArrowLeftIcon}>
                Back to All Readings
              </Button>
              <Button
                variant="dangerGhost"
                size="sm"
                icon={TrashIcon}
                onClick={() => setDeleteOpen(true)}
                disabled={Boolean(actionLoading)}
              >
                Delete Reading
              </Button>
            </div>

            {/* Personalized Recommendations */}
            {reading && reading.status === "completed" && result && (
              <RecommendationsSection
                readingId={reading.id}
                generateFn={async () => {
                  const payload = { max_total: 8, per_type: 2 };
                  if (reading.type === "tarot") {
                    payload.tarot_reading_id = reading.id;
                  } else {
                    payload.reading_id = reading.id;
                  }
                  return generateRecommendations(payload);
                }}
                autoGenerate={false}
              />
            )}

            {/* Safety Disclaimer */}
            <div className="rounded-xl border border-slate-200/70 bg-white/60 p-4 text-center">
              <p className="text-[11px] italic text-slate-400">
                Safety Notice: Interpretations and readings are intended solely for self-reflection,
                mindfulness, and entertainment. They do not constitute formal medical or financial advice.
              </p>
            </div>

            {/* AI ChatBot — fixed bottom-right, same as live reading pages */}
            <ChatBot readingId={queryId} readingType={isPalm ? "palm" : "tarot"} result={result} />
          </div>
        )}
      </main>

      <ConfirmDialog
        open={deleteOpen}
        title="Delete this reading?"
        message="Are you sure you want to delete this reading? Its report, notes, and AI insights will be permanently removed. This cannot be undone."
        confirmLabel="Delete Reading"
        loading={actionLoading === "delete"}
        onConfirm={handleDelete}
        onCancel={() => {
          if (actionLoading !== "delete") setDeleteOpen(false);
        }}
      />
    </div>
  );
}
