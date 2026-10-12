// Shared "AI Insights" section used by palm, tarot and reading-detail pages.
import Button from "@/components/ui/Button";
import { Spinner } from "@/components/ui/States";
import { AlertIcon, BrainIcon, ClockIcon, RetryIcon, SparkleIcon } from "@/components/icons";

// Map any known AI interpretation payload onto the panel's display shape.
export function normalizeAiInterpretation(ai) {
  if (!ai || typeof ai !== "object") return null;
  const domainInsights =
    ai.domain_insights && Object.keys(ai.domain_insights).length > 0
      ? ai.domain_insights
      : ai.action_plan?.length > 0
        ? { "Action plan": ai.action_plan.map((step, i) => `${i + 1}. ${step}`).join(" ") }
        : null;
  return {
    ...ai,
    summary: ai.summary || ai.deep_narrative || "",
    body: ai.body || ai.contextual_insight || "",
    guidance: ai.guidance?.length ? ai.guidance : ai.wisdom_points || [],
    domain_insights: domainInsights || undefined,
  };
}

function Section({ label, children }) {
  return (
    <div className="rounded-2xl border border-primary-100 bg-primary-50/50 p-4 sm:p-5">
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-primary-700">
        {label}
      </p>
      {children}
    </div>
  );
}

export default function AiInsightsPanel({
  readingTypeLabel = "reading",
  loading = false,
  error = null,
  interpretation = null,
  onGenerate,
  footer,
}) {
  const ai = normalizeAiInterpretation(interpretation);
  const hasContent =
    ai &&
    (ai.summary ||
      ai.body ||
      ai.guidance?.length ||
      (ai.domain_insights && Object.keys(ai.domain_insights).length > 0));

  return (
    <section
      className="animate-rise-in space-y-5 rounded-3xl border border-primary-200/70 bg-gradient-to-br from-primary-50/80 via-white to-accent-50/50 p-6 shadow-sm sm:p-8"
      aria-label="AI insights"
    >
      <div className="flex items-start gap-4">
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-600 to-fuchsia-500 text-white shadow-lg shadow-primary-500/30">
          <SparkleIcon className="h-5 w-5" />
        </span>
        <div>
          <h2 className="font-display text-xl tracking-tight text-slate-900 sm:text-2xl">
            AI Insights
          </h2>
          <p className="mt-0.5 text-sm text-slate-600">
            An optional AI interpretation layered on top of your {readingTypeLabel} — generated
            only when you ask for it.
          </p>
        </div>
      </div>

      {loading && (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-primary-100 bg-white/80 px-4 py-10">
          <Spinner label="Generating your AI interpretation…" />
          <p className="text-xs text-slate-400">
            The model is reading your {readingTypeLabel} — this usually takes a few seconds.
          </p>
        </div>
      )}

      {!loading && error && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50/70 p-5">
          <div className="flex items-start gap-3">
            <AlertIcon className="mt-0.5 h-5 w-5 shrink-0 text-rose-500" />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-rose-700">AI interpretation failed</p>
              <p className="mt-1 break-words text-sm leading-relaxed text-rose-600">{error}</p>
            </div>
          </div>
          {onGenerate && (
            <div className="mt-4 flex justify-end">
              <Button variant="secondary" size="sm" icon={RetryIcon} onClick={onGenerate}>
                Try again
              </Button>
            </div>
          )}
        </div>
      )}

      {!loading && !error && hasContent && (
        <div className="space-y-4 rounded-2xl border border-primary-100 bg-white p-5 shadow-xs sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="flex items-center gap-1.5 text-sm font-semibold text-primary-700">
              <BrainIcon className="h-4 w-4" />
              Interpretation
            </h3>
            {(ai.engine || ai.provider) && (
              <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-[11px] font-medium text-slate-500">
                {ai.engine || ai.provider}
              </span>
            )}
          </div>

          {ai.summary && (
            <p className="text-sm font-medium leading-relaxed text-slate-800">{ai.summary}</p>
          )}

          {ai.body && (
            <Section label="Detailed reading">
              <p className="text-sm leading-relaxed text-slate-700">{ai.body}</p>
            </Section>
          )}

          {ai.guidance?.length > 0 && (
            <Section label="Guidance">
              <ul className="space-y-2.5">
                {ai.guidance.map((step, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm leading-relaxed text-slate-700">
                    <SparkleIcon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent-500" />
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {ai.domain_insights && Object.keys(ai.domain_insights).length > 0 && (
            <Section label="Domain insights">
              <dl className="space-y-3.5">
                {Object.entries(ai.domain_insights).map(([domain, insight]) => (
                  <div key={domain}>
                    <dt className="text-xs font-semibold uppercase tracking-wide text-primary-700">
                      {domain}
                    </dt>
                    <dd className="mt-0.5 text-sm leading-relaxed text-slate-700">{insight}</dd>
                  </div>
                ))}
              </dl>
            </Section>
          )}

          {ai.disclaimer && (
            <p className="border-t border-slate-100 pt-3 text-[11px] italic leading-relaxed text-slate-400">
              {ai.disclaimer}
            </p>
          )}
        </div>
      )}

      {!loading && !error && !hasContent && onGenerate && (
        <div className="relative overflow-hidden rounded-2xl border border-dashed border-primary-300 bg-white/70 px-6 py-10 text-center">
          <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-accent-100/50 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-16 -left-16 h-48 w-48 rounded-full bg-primary-100/60 blur-3xl" />
          <div className="relative mx-auto flex max-w-md flex-col items-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-600 to-fuchsia-500 text-white shadow-lg shadow-primary-500/30">
              <SparkleIcon className="h-5 w-5" />
            </span>
            <h3 className="mt-4 font-display text-lg font-semibold text-slate-900">
              Generate your AI insight
            </h3>
            <p className="mt-1.5 text-sm leading-relaxed text-slate-500">
              No interpretation exists for this {readingTypeLabel} yet. Run the AI model to weave
              your results into a personalized narrative, step-by-step guidance, and domain
              insights — entirely on your terms.
            </p>
            <Button variant="accent" className="mt-5" icon={SparkleIcon} onClick={onGenerate}>
              Generate AI Insight
            </Button>
            <p className="mt-3 flex items-center gap-1.5 text-[11px] text-slate-400">
              <ClockIcon className="h-3.5 w-3.5" />
              Takes a few seconds · saved to this reading once generated
            </p>
          </div>
        </div>
      )}

      {!loading && !error && !hasContent && !onGenerate && (
        <div className="rounded-2xl border border-dashed border-primary-200 bg-white/60 px-6 py-8 text-center text-sm text-slate-500">
          No AI interpretation was generated for this reading yet.
        </div>
      )}

      {footer && <div className="pt-1">{footer}</div>}
    </section>
  );
}
