// Start Consultation — the guided workflow described in the consultant requirements: 1.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button, SkeletonRow } from "@/components/ui";
import {
  CheckCircleIcon,
  CloseIcon,
  HandIcon,
  CardsIcon,
  SparklesIcon,
} from "@/components/icons";
import {
  AIInsightIcon,
  ClientAvatar,
  ConsultantSelect,
  FieldLabel,
  SectionError,
} from "@/components/consultant/shared";
import { CONSULTATION_PURPOSES, startConsultationSession } from "@/services/consultant";
import { READING_TYPE_LABELS } from "@/services/consultantDemoData";
import { formatDate } from "@/lib/format";

const STEPS = ["Client & purpose", "Reading context", "AI insights", "Guidance & save"];

// Flatten a client's reading history into selectable context rows.
function contextRowsFor(client) {
  if (!client) return [];
  const rows = [];
  client.tarotHistory.forEach((entry) => {
    rows.push({
      id: `tarot-${entry.id}`,
      kind: "tarot",
      label: `${entry.spread} · ${entry.topic}`,
      detail: entry.summary,
      date: entry.date,
      icon: CardsIcon,
    });
  });
  client.palm?.features
    ?.filter((feature) => feature.status === "analyzed")
    .slice(0, 3)
    .forEach((feature) => {
      rows.push({
        id: `palm-${feature.key}`,
        kind: "palm",
        label: `${feature.label} analysis`,
        detail: feature.insight,
        date: client.palm.analyzedAt,
        icon: HandIcon,
      });
    });
  return rows;
}

export default function StartConsultationDialog({
  open,
  clients = [],
  preselectedClientId = "",
  onClose,
  onCreated,
}) {
  const [step, setStep] = useState(preselectedClientId ? 1 : 0);
  const [clientId, setClientId] = useState(preselectedClientId || "");
  const [purpose, setPurpose] = useState(CONSULTATION_PURPOSES[0].value);
  const [selectedContext, setSelectedContext] = useState(null);
  const [insights, setInsights] = useState(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [insightsError, setInsightsError] = useState(null);
  const [reviewed, setReviewed] = useState(false);
  const [notes, setNotes] = useState("");
  const [guidance, setGuidance] = useState("");
  const [followUpDate, setFollowUpDate] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [saved, setSaved] = useState(false);
  const dialogRef = useRef(null);

  const clientOptions = useMemo(
    () => [
      { value: "", label: "Select a client…" },
      ...clients.map((client) => ({
        value: client.id,
        label: client.profilePending ? `${client.name} (profile pending)` : client.name,
      })),
    ],
    [clients]
  );

  const selectedClient = useMemo(
    () => clients.find((client) => client.id === clientId) || null,
    [clients, clientId]
  );

  const contextRows = useMemo(() => contextRowsFor(selectedClient), [selectedClient]);

  // null means "all available context"; the first toggle materialises the list.
  const selectedContextIds =
    selectedContext === null ? contextRows.map((row) => row.id) : selectedContext;

  const loadInsights = useCallback(async (id) => {
    setInsightsLoading(true);
    setInsightsError(null);
    try {
      const { fetchClientAIInsights } = await import("@/services/consultant");
      const payload = await fetchClientAIInsights(id);
      setInsights(payload.insights || []);
    } catch (err) {
      setInsightsError(err?.message || "Could not generate insights right now.");
    } finally {
      setInsightsLoading(false);
    }
  }, []);

  // Focus the dialog on open, lock background scroll, restore focus on close.
  useEffect(() => {
    if (!open) return undefined;
    const previous = document.activeElement;
    dialogRef.current?.focus();
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
      previous?.focus?.();
    };
  }, [open]);

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (event) => {
      if (event.key === "Escape") onClose?.();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const canLeaveStep1 = Boolean(clientId);
  const canGenerate = selectedContextIds.length > 0;
  const canSave = reviewed && guidance.trim().length > 0 && Boolean(clientId);

  async function handleGenerate() {
    await loadInsights(clientId);
  }

  function toggleContext(id) {
    setSelectedContext((prev) => {
      const current = prev === null ? contextRows.map((row) => row.id) : prev;
      return current.includes(id) ? current.filter((item) => item !== id) : [...current, id];
    });
  }

  async function handleSave() {
    setSaving(true);
    setSaveError(null);
    try {
      const result = await startConsultationSession({ clientId, purpose });
      await saveConsultationNotesForSession(result.session.id);
      setSaved(true);
      onCreated?.(result.session);
    } catch (err) {
      setSaveError(err?.message || "Could not save this consultation.");
    } finally {
      setSaving(false);
    }
  }

  // Notes persist via the service until the API replaces it.
  async function saveConsultationNotesForSession(sessionId) {
    const { saveConsultationNotes } = await import("@/services/consultant");
    await saveConsultationNotes(sessionId, { notes, guidance, followUpDate, status: "completed" });
  }

  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center overflow-y-auto p-4 sm:items-center">
      <div
        className="absolute inset-0 animate-backdrop-in bg-slate-950/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        ref={dialogRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="start-consultation-title"
        className="surface-panel shadow-float relative my-auto w-full max-w-2xl animate-dialog-in focus:outline-none"
      >
        <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-5">
          <div>
            <h2 id="start-consultation-title" className="text-base font-semibold text-slate-900">
              Start Consultation
            </h2>
            <p className="mt-0.5 text-xs text-slate-500">
              Step {step + 1} of {STEPS.length} · {STEPS[step]}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="cursor-pointer rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
          >
            <CloseIcon />
          </button>
        </div>

        {/* Step rail */}
        <ol className="flex flex-wrap gap-2 border-b border-slate-100 px-6 py-3">
          {STEPS.map((label, index) => (
            <li key={label}>
              <span
                className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
                  index === step
                    ? "bg-primary-50 text-primary-700 ring-1 ring-primary-100"
                    : index < step
                      ? "bg-emerald-50 text-emerald-700"
                      : "bg-slate-100 text-slate-500"
                }`}
              >
                {index < step ? <CheckCircleIcon className="h-3 w-3" /> : <span>{index + 1}</span>}
                {label}
              </span>
            </li>
          ))}
        </ol>

        <div className="max-h-[60vh] overflow-y-auto px-6 py-5">
          <div key={step} className="animate-tab-in space-y-5">
          {step === 0 && (
            <div className="space-y-5">
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-1.5 block">
                    <FieldLabel>Client</FieldLabel>
                  </span>
                  <ConsultantSelect
                    label="Client"
                    value={clientId}
                    onChange={setClientId}
                    options={clientOptions}
                    className="w-full"
                  />
                </label>
                <label className="block">
                  <span className="mb-1.5 block">
                    <FieldLabel>Consultation purpose</FieldLabel>
                  </span>
                  <ConsultantSelect
                    label="Consultation purpose"
                    value={purpose}
                    onChange={setPurpose}
                    options={CONSULTATION_PURPOSES}
                    className="w-full"
                  />
                </label>
              </div>

              {selectedClient && (
                <div className="flex items-center gap-3 rounded-card border border-slate-100 bg-slate-50/60 p-4">
                  <ClientAvatar name={selectedClient.name} size="md" />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-900">
                      {selectedClient.name}
                    </p>
                    <p className="truncate text-xs text-slate-500">
                      {selectedClient.ageGroup || "Age group not shared"} ·{" "}
                      {selectedClient.interests.join(", ") || "No interests recorded"} ·{" "}
                      {selectedClient.consultationCount} previous session
                      {selectedClient.consultationCount === 1 ? "" : "s"}
                    </p>
                  </div>
                </div>
              )}

              {selectedClient?.profilePending && (
                <p className="rounded-card border border-accent-200 bg-accent-50 px-4 py-3 text-xs leading-relaxed text-accent-900">
                  This seeker has an open thread but their profile and readings are not exposed to
                  consultants by the API yet. You can still conduct the session and record your own
                  notes.
                </p>
              )}
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <p className="text-sm leading-relaxed text-slate-600">
                Previous readings for {selectedClient?.name || "this client"}. Select the material
                that is relevant to this session — only the selected items inform the generated
                insights.
              </p>

              {contextRows.length === 0 ? (
                <p className="rounded-card border border-dashed border-slate-300 bg-slate-50/60 px-4 py-8 text-center text-sm text-slate-500">
                  No readings are available for this client yet.
                </p>
              ) : (
                <ul className="space-y-2.5">
                  {contextRows.map((row) => {
                    const checked = selectedContextIds.includes(row.id);
                    return (
                      <li key={row.id}>
                        <label
                          className={`flex cursor-pointer items-start gap-3 rounded-card border p-3.5 transition ${
                            checked
                              ? "border-primary-200 bg-primary-50/60"
                              : "border-slate-100 bg-white hover:bg-slate-50"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => toggleContext(row.id)}
                            className="mt-0.5 h-4 w-4 shrink-0 cursor-pointer rounded border-slate-300 text-primary-600 focus:ring-primary-400"
                          />
                          <row.icon className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
                          <span className="min-w-0 flex-1">
                            <span className="flex flex-wrap items-center gap-2">
                              <span className="text-sm font-semibold text-slate-900">
                                {row.label}
                              </span>
                              <span className="text-xs text-slate-500 tabular-nums">
                                {formatDate(row.date)}
                              </span>
                            </span>
                            <span className="mt-0.5 block text-xs leading-relaxed text-slate-600">
                              {row.detail}
                            </span>
                          </span>
                        </label>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-card border border-primary-100 bg-primary-50/50 p-4">
                <div className="flex items-start gap-3">
                  <AIInsightIcon />
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900">AI consultation insights</h3>
                    <p className="mt-0.5 text-xs leading-relaxed text-slate-600">
                      Generated from the reading context you selected. Reflection points, not
                      predictions.
                    </p>
                  </div>
                </div>
                <Button
                  size="sm"
                  icon={SparklesIcon}
                  loading={insightsLoading}
                  disabled={!canGenerate || insightsLoading}
                  onClick={handleGenerate}
                >
                  {insights ? "Regenerate" : "Generate insights"}
                </Button>
              </div>

              {insightsError && (
                <SectionError
                  title="Unable to generate insights."
                  onRetry={handleGenerate}
                />
              )}

              {insightsLoading && (
                <div className="space-y-3">
                  <SkeletonRow lines={3} />
                  <SkeletonRow lines={3} />
                </div>
              )}

              {!insightsLoading && insights && insights.length === 0 && (
                <p className="rounded-card border border-dashed border-slate-300 bg-slate-50/60 px-4 py-8 text-center text-sm text-slate-500">
                  No insights could be generated from the selected context. Try selecting more
                  readings, or continue and write your own guidance.
                </p>
              )}

              {!insightsLoading && insights && insights.length > 0 && (
                <>
                  <ul className="space-y-2.5">
                    {insights.map((insight) => (
                      <li
                        key={insight.id}
                        className="rounded-card border border-slate-100 bg-white p-4 shadow-xs"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="text-xs font-bold uppercase tracking-wide text-primary-700">
                            {insight.category}
                          </span>
                          <span className="text-xs text-slate-500 tabular-nums">
                            Relevance {insight.relevance}% · {formatDate(insight.createdAt)}
                          </span>
                        </div>
                        <p className="mt-1.5 text-sm leading-relaxed text-slate-800">
                          {insight.insight}
                        </p>
                        {insight.recommendation && (
                          <p className="mt-2 rounded-control bg-slate-50 px-3 py-2 text-xs leading-relaxed text-slate-600">
                            <span className="font-semibold text-slate-700">Suggested focus: </span>
                            {insight.recommendation}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>

                  <label className="flex cursor-pointer items-start gap-3 rounded-card border border-emerald-200 bg-emerald-50/70 p-4">
                    <input
                      type="checkbox"
                      checked={reviewed}
                      onChange={(event) => setReviewed(event.target.checked)}
                      className="mt-0.5 h-4 w-4 shrink-0 cursor-pointer rounded border-slate-300 text-emerald-600 focus:ring-emerald-400"
                    />
                    <span className="text-xs leading-relaxed text-emerald-900">
                      I have reviewed these insights and will decide myself what guidance to give.
                      AI output is never sent to a client without this step.
                    </span>
                  </label>
                </>
              )}
            </div>
          )}

          {step === 3 && (
            <div className="space-y-5">
              <label className="block">
                <span className="mb-1.5 block">
                  <FieldLabel hint="Private to you. Not shared with the client.">
                    Consultant notes
                  </FieldLabel>
                </span>
                <textarea
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  rows={6}
                  placeholder="Write private consultation notes…"
                  className="w-full rounded-control border border-slate-200 bg-white px-3.5 py-2.5 text-sm leading-relaxed text-slate-800 shadow-xs transition placeholder:text-slate-500 focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                />
              </label>

              <label className="block">
                <span className="mb-1.5 block">
                  <FieldLabel hint="What you are telling this client, in your own words.">
                    Guidance to the client
                  </FieldLabel>
                </span>
                <textarea
                  value={guidance}
                  onChange={(event) => setGuidance(event.target.value)}
                  rows={4}
                  placeholder="Write the guidance you will share with this client…"
                  className="w-full rounded-control border border-slate-200 bg-white px-3.5 py-2.5 text-sm leading-relaxed text-slate-800 shadow-xs transition placeholder:text-slate-500 focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                />
              </label>

              <label className="block sm:w-64">
                <span className="mb-1.5 block">
                  <FieldLabel hint="Optional">Follow-up date</FieldLabel>
                </span>
                <input
                  type="date"
                  value={followUpDate}
                  onChange={(event) => setFollowUpDate(event.target.value)}
                  className="h-10 w-full cursor-pointer rounded-control border border-slate-200 bg-white px-3 text-sm text-slate-800 shadow-xs transition focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                />
              </label>

              <p className="rounded-card border border-slate-100 bg-slate-50/60 px-4 py-3 text-xs leading-relaxed text-slate-500">
                Guidance is written by you. Nothing in this session is sent to the client
                automatically, and no AI text is presented as a prediction or a professional
                (medical, financial or legal) opinion.
              </p>

              {saveError && <SectionError title={saveError} />}

              {saved && (
                <div className="rounded-card border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
                  Consultation saved. You can generate the report from the workspace.
                </div>
              )}
            </div>
          )}
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-6 py-4">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              disabled={step === 0}
              onClick={() => setStep((current) => Math.max(0, current - 1))}
            >
              Back
            </Button>
            {step < STEPS.length - 1 ? (
              <Button
                size="sm"
                disabled={(step === 0 && !canLeaveStep1) || (step === 1 && !canGenerate)}
                onClick={() => setStep((current) => Math.min(STEPS.length - 1, current + 1))}
              >
                Continue
              </Button>
            ) : (
              <Button size="sm" loading={saving} disabled={!canSave || saving} onClick={handleSave}>
                Save consultation
              </Button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">
              {step === 2 && !reviewed && insights?.length
                ? "Review the insights to continue"
                : step === 3 && !canSave
                  ? "Add your guidance to save"
                  : "Ready"}
            </span>
            <Button variant="secondary" size="sm" onClick={onClose}>
              {saved ? "Close" : "Cancel"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
