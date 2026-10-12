import { useState } from "react";
import { Badge, InlineError } from "@/components/ui";
import { CheckIcon, StarIcon, TargetIcon } from "@/components/icons";
import { submitRecommendationFeedback } from "@/services/recommendations";

// Badge tone per type (matches catalog categories; kit tones)
const TYPE_TONES = {
  personal_growth: "primary",
  relationship: "rose",
  career: "blue",
  goal_alignment: "emerald",
  spiritual_development: "accent",
};

const PRIORITY_TONES = {
  high: "rose",
  medium: "accent",
  low: "slate",
};

export default function RecommendationCard({
  recommendation,
  onFeedback,
  hideActions = false,
}) {
  const [feedbackLoading, setFeedbackLoading] = useState(null);
  const [feedbackError, setFeedbackError] = useState(null);
  const [ratingHover, setRatingHover] = useState(0);

  const recType = recommendation.type || recommendation.rec_type;
  const typeTone = TYPE_TONES[recType] || TYPE_TONES.personal_growth;

  async function handleFeedback(action, rating = null) {
    setFeedbackLoading(action);
    setFeedbackError(null);
    try {
      const result = await submitRecommendationFeedback(recommendation.id, action, rating);
      onFeedback?.(result);
    } catch (err) {
      setFeedbackError(err.message || "Failed to save feedback");
    } finally {
      setFeedbackLoading(null);
    }
  }

  const status = recommendation.status || "new";
  const isCompleted = status === "completed";
  const isDismissed = status === "dismissed";

  return (
    <div
      className={`rounded-3xl border border-slate-200/90 bg-white p-5 shadow-xs transition ${
        isDismissed ? "opacity-60" : ""
      }`}
    >
      {/* Header: category + priority + confidence */}
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div className="flex flex-wrap gap-2">
          <Badge tone={typeTone}>{(recType || "recommendation").replace(/_/g, " ")}</Badge>
          {recommendation.priority && (
            <Badge tone={PRIORITY_TONES[recommendation.priority] || "slate"}>
              {recommendation.priority} priority
            </Badge>
          )}
        </div>
        <div className="text-right">
          <div className="text-sm font-semibold text-slate-700">
            {Math.round((recommendation.confidence || recommendation.score || 0) * 100)}%
          </div>
          <div className="text-xs text-slate-500">relevance</div>
        </div>
      </div>

      <h3 className="mb-2 text-sm font-semibold text-slate-900">{recommendation.title}</h3>

      <p className="mb-3 text-sm leading-relaxed text-slate-700">{recommendation.text}</p>

      {/* Element affinity tag */}
      {recommendation.element_affinity && (
        <div className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-primary-50 px-2.5 py-0.5 text-[11px] font-medium text-primary-700 ring-1 ring-primary-100">
          <TargetIcon className="h-3 w-3" />
          Matches your {recommendation.element_affinity} element
        </div>
      )}

      {/* Reasoning (if available) */}
      {recommendation.reasoning && recommendation.reasoning.length > 0 && (
        <div className="mb-3 rounded-2xl bg-slate-50 p-3 text-xs text-slate-600">
          <div className="mb-1.5 font-medium text-slate-700">Why this recommendation:</div>
          <ul className="space-y-1">
            {recommendation.reasoning.map((reason, i) => (
              <li key={i} className="flex items-start gap-1.5">
                <CheckIcon className="mt-0.5 h-3 w-3 shrink-0 text-emerald-600" />
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Score breakdown (if available) */}
      {recommendation.scores && (
        <div className="mb-3 grid grid-cols-3 gap-2 text-xs">
          {recommendation.scores.context_relevance != null && (
            <div className="rounded-xl bg-slate-50 p-2">
              <div className="text-slate-500">Context</div>
              <div className="font-semibold text-slate-900">
                {Math.round(recommendation.scores.context_relevance * 100)}%
              </div>
            </div>
          )}
          {recommendation.scores.personalization != null && (
            <div className="rounded-xl bg-slate-50 p-2">
              <div className="text-slate-500">Personal</div>
              <div className="font-semibold text-slate-900">
                {Math.round(recommendation.scores.personalization * 100)}%
              </div>
            </div>
          )}
          {recommendation.scores.goal_alignment != null && (
            <div className="rounded-xl bg-slate-50 p-2">
              <div className="text-slate-500">Goal Match</div>
              <div className="font-semibold text-slate-900">
                {Math.round(recommendation.scores.goal_alignment * 100)}%
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error message */}
      {feedbackError && <InlineError message={feedbackError} className="mb-3" />}

      {/* Status indicator */}
      {status !== "new" && (
        <div className="mb-3">
          <Badge tone={isCompleted ? "emerald" : status === "accepted" ? "primary" : "slate"}>
            {isCompleted ? (
              <>
                <CheckIcon className="h-3 w-3" />
                Completed
              </>
            ) : status === "accepted" ? (
              "Accepted"
            ) : (
              "Dismissed"
            )}
          </Badge>
        </div>
      )}

      {/* Action buttons */}
      {!hideActions && status === "new" && (
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => handleFeedback("accepted")}
            disabled={feedbackLoading !== null}
            className="flex-1 cursor-pointer rounded-full border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-700 transition hover:bg-emerald-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {feedbackLoading === "accepted" ? "Saving..." : "Accept"}
          </button>
          <button
            type="button"
            onClick={() => handleFeedback("dismissed", 0)}
            disabled={feedbackLoading !== null}
            className="flex-1 cursor-pointer rounded-full border border-slate-300 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-700 transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {feedbackLoading === "dismissed" ? "Saving..." : "Dismiss"}
          </button>
        </div>
      )}

      {status === "accepted" && (
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => handleFeedback("completed")}
            disabled={feedbackLoading !== null}
            className="flex-1 cursor-pointer rounded-full border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-700 transition hover:bg-emerald-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {feedbackLoading === "completed" ? "Saving..." : "Mark completed"}
          </button>
          <div className="flex shrink-0 items-center gap-0.5" role="group" aria-label="Rate this recommendation">
            {[1, 2, 3, 4, 5].map((star) => {
              const filled = ratingHover >= star || recommendation.feedback_rating >= star;
              return (
                <button
                  key={star}
                  type="button"
                  onClick={() => handleFeedback("rated", star)}
                  onMouseEnter={() => setRatingHover(star)}
                  onMouseLeave={() => setRatingHover(0)}
                  className={`cursor-pointer rounded-full p-1 transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-600 disabled:cursor-not-allowed disabled:opacity-50 ${
                    filled ? "text-accent-500" : "text-slate-300 hover:text-accent-400"
                  }`}
                  title={`Rate ${star} star${star === 1 ? "" : "s"}`}
                  aria-label={`Rate ${star} star${star === 1 ? "" : "s"}`}
                  disabled={feedbackLoading !== null}
                >
                  <StarIcon className="h-4 w-4" />
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
