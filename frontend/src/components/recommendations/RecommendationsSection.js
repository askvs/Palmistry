import { useEffect, useState } from "react";
import RecommendationCard from "./RecommendationCard";
import { Badge, Button, EmptyState, ErrorState, Panel, Spinner } from "@/components/ui";
import { SparkleIcon } from "@/components/icons";

export default function RecommendationsSection({
  readingId,
  generateFn, // Function: async () => recommendations
  onGenerated,
  autoGenerate = false,
}) {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(autoGenerate);
  const [hasGenerated, setHasGenerated] = useState(false);
  const [error, setError] = useState(null);
  const [activeCategory, setActiveCategory] = useState(null);

  useEffect(() => {
    if (autoGenerate && readingId && !hasGenerated) {
      loadRecommendations();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [readingId, autoGenerate, hasGenerated]);

  async function loadRecommendations() {
    setLoading(true);
    setError(null);
    setHasGenerated(true);
    try {
      const result = await generateFn();
      const items = Array.isArray(result?.recommendations) ? result.recommendations : [];
      // Bind items to persisted ids for feedback.
      const recordIds = new Map(
        (result?.persisted || []).map((p) => [p.item_id, p.record_id])
      );
      const bound = items.map((item, idx) => ({
        ...item,
        id: recordIds.get(item.id) || `${item.id || "item"}-${idx}`,
      }));
      setRecommendations(bound);
      onGenerated?.(result);
    } catch (err) {
      setError(err.message || "Failed to generate recommendations");
    } finally {
      setLoading(false);
    }
  }

  // Filter by active category
  const recType = (r) => r.type || r.rec_type || "recommendation";
  const filteredRecs = activeCategory
    ? recommendations.filter((r) => recType(r) === activeCategory)
    : recommendations;

  const categories = [...new Set(recommendations.map(recType))];
  const categoryLabel = (category) => category.replace(/_/g, " ");

  if (!hasGenerated) {
    return (
      <Panel
        title="Personalized Recommendations"
        subtitle="Based on your reading and profile"
        action={
          <Badge tone="primary">
            <SparkleIcon className="h-3 w-3" />
            AI guided
          </Badge>
        }
      >
        <EmptyState
          icon={SparkleIcon}
          title="Guidance tailored to this reading"
          description="Generate personalized recommendations from your reading results and profile."
          action={
            <Button size="sm" onClick={loadRecommendations} loading={loading}>
              Show
            </Button>
          }
        />
      </Panel>
    );
  }

  return (
    <Panel
      title="Personalized Recommendations"
      subtitle="Based on your reading and profile"
      action={
        <Badge tone="primary">
          <SparkleIcon className="h-3 w-3" />
          AI guided
        </Badge>
      }
    >
      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner label="Generating personalized guidance..." />
        </div>
      ) : error ? (
        <ErrorState
          title="Couldn't generate recommendations"
          message={error}
          onRetry={loadRecommendations}
        />
      ) : recommendations.length === 0 ? (
        <EmptyState
          icon={SparkleIcon}
          title="No recommendations yet"
          description="No recommendations were generated for this reading. Generate again to try another pass."
          action={
            <Button size="sm" variant="secondary" onClick={loadRecommendations}>
              Generate
            </Button>
          }
        />
      ) : (
        <div>
          <div className="mb-4 inline-flex flex-wrap items-center gap-1 rounded-full border border-slate-200 bg-slate-100 p-1">
            <button
              type="button"
              onClick={() => setActiveCategory(null)}
              aria-pressed={!activeCategory}
              className={`inline-flex cursor-pointer items-center rounded-full px-3 py-1.5 text-[12.5px] font-medium transition duration-[120ms] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 ${
                !activeCategory
                  ? "bg-white text-primary-700 shadow-[0_1px_3px_rgba(30,24,54,0.12)]"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              All
            </button>
            {categories.map((category) => (
              <button
                type="button"
                key={category}
                onClick={() => setActiveCategory(category)}
                aria-pressed={activeCategory === category}
                className={`inline-flex cursor-pointer items-center rounded-full px-3 py-1.5 text-[12.5px] font-medium transition duration-[120ms] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 ${
                  activeCategory === category
                    ? "bg-white text-primary-700 shadow-[0_1px_3px_rgba(30,24,54,0.12)]"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {categoryLabel(category)}
              </button>
            ))}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {filteredRecs.map((rec) => (
              <RecommendationCard
                key={rec.id}
                recommendation={rec}
                onFeedback={(updated) => {
                  // Update local state with feedback result
                  setRecommendations((prev) =>
                    prev.map((r) => (r.id === updated.id ? updated : r))
                  );
                }}
              />
            ))}
          </div>
        </div>
      )}
    </Panel>
  );
}
