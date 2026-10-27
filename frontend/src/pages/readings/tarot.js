import { useCallback, useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import Seo from "@/components/Seo";
import {
  ArrowLeftIcon,
  ArrowRightIcon,
  CardsIcon,
  CheckIcon,
  FileTextIcon,
  RetryIcon,
  ShieldIcon,
  SparkleIcon,
  TableIcon,
} from "@/components/icons";
import { useAuth } from "@/hooks/useAuth";
import { useRoleGuard } from "@/hooks/useRoleGuard";
import {
  drawTarotSpread,
  getTarotDecks,
  getTarotSpreads,
  getShuffledDeck,
  interpretTarotSelection,
} from "@/services/tarot";
import { downloadReportPdf, downloadReportExcel } from "@/services/reports";
import { interpretTarot } from "@/services/readings";
import RecommendationsSection from "@/components/recommendations/RecommendationsSection";
import { generateRecommendations } from "@/services/recommendations";
import AiInsightsPanel from "@/components/ai/AiInsightsPanel";
import ShuffleAnimation from "@/components/tarot/ShuffleAnimation";
import CardSelection from "@/components/tarot/CardSelection";
import CardReveal from "@/components/tarot/CardReveal";
import ReadingAnalysisPanel from "@/components/tarot/ReadingAnalysisPanel";
import ChatBot from "@/components/ai/ChatBot";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  InlineError,
  Panel,
  PageHeader,
  Spinner,
  useToast,
} from "@/components/ui";

const RITUAL_STEPS = [
  { id: "setup", label: "Spread" },
  { id: "shuffling", label: "Shuffle" },
  { id: "selecting", label: "Select" },
  { id: "results", label: "Insight" },
];

// Roman numerals for the ritual progress pills (spec §6.4).
const ROMAN = ["I", "II", "III", "IV"];

function SpreadLayout({ spreadDef, cards }) {
  const coords = useMemo(() => {
    const map = new Map();
    (spreadDef?.positions || []).forEach((pos) => {
      map.set(pos.position, pos.layout_coordinate || { x: 0.5, y: 0.5 });
    });
    return map;
  }, [spreadDef]);

  const seen = new Set();
  const placed = (cards || []).map((card) => {
    const coord = coords.get(card.position) || { x: 0.5, y: 0.5 };
    const key = `${coord.x}-${coord.y}`;
    const crossing = seen.has(key);
    seen.add(key);
    return { card, coord, crossing };
  });

  const count = cards ? cards.length : spreadDef?.card_count || 3;

  return (
    <div className="relative mx-auto aspect-[4/3] w-full max-w-xl overflow-visible rounded-panel border border-primary-200 bg-[radial-gradient(ellipse_at_top,rgba(139,92,246,0.10),rgba(245,243,255,0.7)_50%,white_85%)] p-[7%] shadow-inner">
      {cards
        ? placed.map(({ card, coord, crossing }) => (
            <figure
              key={card.position}
              className={`absolute w-[16%] max-w-[112px] min-w-[46px] ${crossing ? "z-10" : ""}`}
              style={{
                left: `${7 + coord.x * 86}%`,
                top: `${7 + coord.y * 86}%`,
                transform: `translate(-50%, -50%) ${crossing ? "rotate(90deg)" : ""}`,
              }}
            >
              <div
                className={`overflow-hidden rounded-lg border shadow-md transition-transform duration-300 hover:scale-[1.08] ${
                  card.is_reversed ? "border-primary-400 shadow-primary-200" : "border-accent-300 shadow-accent-100"
                } ${crossing ? "rotate-90 shadow-lg" : ""}`}
              >
                {card.image_path ? (
                  <Image
                    src={`/${card.image_path.startsWith("/") ? card.image_path.slice(1) : card.image_path}`}
                    alt={`${card.card_name} (${card.orientation})`}
                    width={280}
                    height={480}
                    sizes="(min-width:640px) 220px, 160px"
                    className={`aspect-[7/12] w-full object-cover ${card.is_reversed ? "rotate-180" : ""}`}
                  />
                ) : (
                  <div className="aspect-[7/12] w-full bg-primary-950 flex items-center justify-center text-[12.5px] text-accent-200 p-1 text-center">
                    {card.card_name}
                  </div>
                )}
              </div>
              <figcaption className="mt-1 truncate text-center text-[12.5px] font-medium text-primary-800">
                {card.position_name}
              </figcaption>
            </figure>
          ))
        : Array.from({ length: count }).map((_, i) => (
            <div
              key={i}
              className="absolute w-[16%] max-w-[112px] min-w-[46px] animate-pulse"
              style={{
                left: `${7 + (coords.get(i + 1)?.x ?? 0.5) * 86}%`,
                top: `${7 + (coords.get(i + 1)?.y ?? 0.5) * 86}%`,
                transform: "translate(-50%, -50%)",
              }}
            >
              {/* Face-down card placeholder (rich card-back art is intentionally dark) */}
              <div className="flex aspect-[7/12] w-full items-center justify-center rounded-lg border border-accent-300/50 bg-gradient-to-br from-primary-700 via-indigo-900 to-slate-950 shadow-md shadow-primary-300/40">
                <CardsIcon className="h-5 w-5 text-accent-200/80" />
              </div>
            </div>
          ))}
    </div>
  );
}

function CardThumb({ card, reversed }) {
  return (
    <div
      className={`relative h-26 w-16 overflow-hidden rounded-lg border shadow-sm sm:h-28 sm:w-[72px] ${
        reversed ? "border-primary-400" : "border-accent-300"
      }`}
    >
      {card.image_path ? (
        <Image
          src={`/${card.image_path.startsWith("/") ? card.image_path.slice(1) : card.image_path}`}
          alt={card.name || "Tarot card"}
          fill
          className={`object-cover ${reversed ? "rotate-180" : ""}`}
          sizes="72px"
        />
      ) : (
        <div className="flex h-full w-full items-center justify-center bg-primary-950 p-1 text-center text-[12.5px] leading-tight text-accent-200">
          {card.name}
        </div>
      )}
      <span className="absolute inset-x-0 bottom-0 truncate bg-slate-950/75 px-1 py-0.5 text-center text-[12.5px] font-medium text-white">
        {card.name}
      </span>
    </div>
  );
}

function SelectionBoard({ spread, selections = [] }) {
  if (!spread?.positions?.length) return null;
  const selectionIds = new Set(selections.map((s) => s.card_id));
  const positionDefs = spread.positions;

  return (
    <div className="mb-6">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-display text-base font-bold text-slate-900">{spread.name}</h3>
        <Badge tone="primary">
          {selections.length} / {positionDefs.length} placed
          {selectionIds.size > selections.length ? ` (${selectionIds.size} unique drawn)` : ""}
        </Badge>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {positionDefs.map((pos, idx) => {
          const sel = selections[idx];
          const isNext = idx === selections.length;

          return (
            <div
              key={pos.position || idx}
              className={`flex items-start gap-4 rounded-2xl border p-4 transition-all ${
                sel
                  ? "border-primary-200 bg-primary-50/50 shadow-xs"
                  : isNext
                    ? "animate-pulse border-accent-300/70 border-dashed bg-accent-50/40"
                    : "border-slate-200 border-dashed bg-slate-50/50"
              }`}
            >
              {sel ? (
                <CardThumb card={sel.card} reversed={sel.is_reversed} />
              ) : (
                <div className="flex h-26 w-16 shrink-0 flex-col items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-300 sm:h-28 sm:w-[72px]">
                  {isNext ? (
                    <SparkleIcon className="h-4 w-4 text-accent-400" />
                  ) : (
                    <span className="text-lg">+</span>
                  )}
                </div>
              )}
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[12.5px] font-semibold uppercase tracking-wider text-primary-600">
                    {pos.position || idx + 1}. {pos.name}
                  </span>
                  {sel?.is_reversed && (
                    <Badge tone="accent" className="px-1.5 py-0 font-bold uppercase">
                      Rev
                    </Badge>
                  )}
                </div>
                <p className="mt-1 text-sm leading-relaxed text-slate-500">{pos.description}</p>
                <p className="mt-2 text-xs">
                  {sel ? (
                    <span className="font-semibold text-slate-800">
                      {sel.card.name}
                      {sel.is_reversed ? " (Reversed)" : ""}
                    </span>
                  ) : isNext ? (
                    <span className="font-medium text-accent-700">
                      This is the next slot you&rsquo;ll draw from the arc below.
                    </span>
                  ) : (
                    <span className="italic text-slate-500">Awaiting card</span>
                  )}
                </p>
                {sel?.core_meaning ? (
                  <p className="mt-1.5 line-clamp-2 text-sm italic leading-relaxed text-slate-500">
                    {sel.core_meaning}
                  </p>
                ) : sel && (sel.card.arcana || sel.card.suit) ? (
                  <p className="mt-1.5 text-sm italic leading-relaxed text-slate-500">
                    {String(sel.card.arcana || "").toUpperCase()}
                    {sel.card.suit ? ` Arcana • ${sel.card.suit}` : ""}
                    {typeof sel.card.number === "number" ? ` • No. ${sel.card.number}` : ""}
                  </p>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function TarotReadingPage() {
  const blocked = useRoleGuard();
  const { user } = useAuth();
  const toast = useToast();

  const [spreads, setSpreads] = useState(null);
  const [deck, setDeck] = useState(null);
  const [catalogError, setCatalogError] = useState(null);

  const [spreadId, setSpreadId] = useState("three_card");
  const [question, setQuestion] = useState("");
  const [allowReversals, setAllowReversals] = useState(true);

  // Ritual phase state machine: 'setup' -> 'shuffling' -> 'selecting' -> 'interpreting' -> 'results'
  const [phase, setPhase] = useState("setup");
  const [shuffledCards, setShuffledCards] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [exporting, setExporting] = useState(null);

  // AI interpretation states (non-blocking)
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(null);

  // Selected arcana positions during the card-selection phase.
  const [liveSelections, setLiveSelections] = useState([]);

  const loadCatalog = useCallback(() => {
    Promise.all([getTarotSpreads(), getTarotDecks()])
      .then(([spreadList, deckList]) => {
        setSpreads(spreadList);
        setDeck(deckList[0] || null);
        setCatalogError(null);
        if (spreadList.length > 0) setSpreadId(spreadList[0].id);
      })
      .catch((err) => {
        setCatalogError(err.message || "Could not load the tarot catalog.");
      });
  }, []);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  const selectedSpread = useMemo(
    () => spreads?.find((s) => s.id === spreadId) || null,
    [spreads, spreadId]
  );

  if (blocked) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner label="Returning to your dashboard…" />
      </div>
    );
  }

  function resetRitual() {
    setPhase("setup");
    setShuffledCards([]);
    setLiveSelections([]);
    setResult(null);
    setError(null);
  }

  // Phase 1 -> 2: fetch the shuffled deck first, then begin the ritual animation.
  async function handleStartRitual(e) {
    if (e) e.preventDefault();
    if (!selectedSpread) return;
    setError(null);
    setLiveSelections([]);

    try {
      const resp = await getShuffledDeck({ deckId: deck?.deck_id });
      const cards = resp.cards || [];
      if (cards.length === 0) {
        throw new Error("The deck came back empty. Please try again.");
      }
      setShuffledCards(cards);
      setPhase("shuffling");
    } catch (err) {
      setError(
        `Could not shuffle the deck: ${err.message || err}. Check that the backend is running, then try again.`
      );
      setPhase("setup");
    }
  }

  // Cmd/Ctrl+Enter from the question field starts the ritual — the existing
  // setup-phase continue handler (spec §7.5 keyboard hint).
  function handleQuestionKeyDown(event) {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      handleStartRitual();
    }
  }

  // Phase 2 -> 3: User cuts the deck and moves to card selection
  function handleShuffleComplete() {
    setLiveSelections([]);
    setPhase("selecting");
  }

  // Phase 3 -> 4 & 5: User finishes selecting cards from arc
  async function handleCompleteSelection(userSelections) {
    if (!userSelections || userSelections.length === 0) {
      setError("No cards were drawn for this spread. Please pick cards from the deck.");
      return;
    }
    setPhase("interpreting");
    setError(null);
    try {
      const data = await interpretTarotSelection({
        spreadId: selectedSpread.id,
        deckId: deck?.deck_id,
        cards: userSelections.map((sel) => ({
          card: sel.card_id || sel.card?.id || sel.card_name,
          is_reversed: sel.is_reversed,
        })),
        question,
      });
      setResult(data);
      setPhase("results");
    } catch (err) {
      setError(err.message || "Failed to interpret selection. Please try again.");
      setPhase("selecting");
    }
  }

  // Power user bypass: instant draw without manual picking
  async function handleInstantDraw() {
    if (!selectedSpread) return;
    setPhase("interpreting");
    setError(null);
    try {
      const data = await drawTarotSpread({
        spreadId: selectedSpread.id,
        deckId: deck?.deck_id,
        question,
        allowReversals,
      });
      setResult(data);
      setPhase("results");
    } catch (err) {
      setError(err.message || "The draw failed. Please try again.");
      setPhase("setup");
    }
  }

  // Opt-in AI interpretation: only runs when the user clicks
  // "Generate AI Insight" (also the retry path when a previous attempt failed).
  async function handleGenerateAi() {
    if (!result || aiLoading) return;
    setAiLoading(true);
    setAiError(null);
    try {
      const aiRes = await interpretTarot(
        result.reading_id,
        question,
        !result.reading_id ? result.result || result : undefined
      );
      if (aiRes) {
        setResult((prev) => ({ ...prev, ai_interpretation: aiRes }));
      }
    } catch (aiErr) {
      setAiError(aiErr.message || "AI interpretation failed. Please try again.");
    } finally {
      setAiLoading(false);
    }
  }

  async function handleExport(format) {
    if (!result?.reading_id || exporting) return;
    setExporting(format);
    try {
      if (format === "pdf") {
        await downloadReportPdf(result.reading_id, `${result.spread_name || "tarot"}-dossier.pdf`);
        toast.success("PDF dossier exported", "Your reading dossier has been downloaded.");
      } else {
        await downloadReportExcel(
          result.reading_id,
          `${result.spread_name || "tarot"}-analysis.xlsx`
        );
        toast.success("Excel workbook exported", "Your reading analysis has been downloaded.");
      }
    } catch (err) {
      toast.error(
        "Export failed",
        err?.message || `Could not export the ${format === "pdf" ? "PDF dossier" : "Excel workbook"}.`
      );
    } finally {
      setExporting(null);
    }
  }

  const showLoading = !spreads && !catalogError;

  // The step list carries four pills; "interpreting" belongs to the Insight
  // stage, so it keeps IV active while the reading synthesizes.
  const ritualPhase = phase === "interpreting" ? "results" : phase;
  const activeIndex = RITUAL_STEPS.findIndex((step) => step.id === ritualPhase);

  // The shared panel normalizes the tarot payload
  // ({deep_narrative, wisdom_points, action_plan}) into its display shape.
  const aiInterpretation = result?.ai_interpretation || null;

  return (
    <div className="space-y-8">
      <Seo title="Tarot reading" description="Shuffle, draw, and reveal a guided tarot spread with structured, personal interpretation." />
      <div>
        <Link
          href="/readings"
          className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg text-xs font-medium text-primary-600 transition-colors hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
        >
          <ArrowLeftIcon className="h-3.5 w-3.5" />
          Back to Readings Archive
        </Link>
        <PageHeader
          icon={CardsIcon}
          tileTone="primary"
          title="Tarot Sanctuary"
          description="Experience the authentic ritual of shuffling, cutting the deck, and drawing cards with sacred Fisher-Yates randomness."
          className="mt-3"
          actions={
            <div className="flex flex-wrap items-center gap-1.5" aria-label="Ritual progress">
              {RITUAL_STEPS.map((step, i) => (
                <div key={step.id} className="flex items-center gap-1.5">
                  {i > 0 && (
                    <span
                      aria-hidden="true"
                      className={`h-px w-4 sm:w-6 ${
                        i <= activeIndex
                          ? "bg-gradient-to-r from-primary-400 to-accent-400"
                          : "bg-slate-200"
                      }`}
                    />
                  )}
                  <span
                    aria-current={i === activeIndex ? "step" : undefined}
                    className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${
                      i === activeIndex
                        ? "border-primary-200 bg-primary-50 text-primary-700"
                        : i < activeIndex
                          ? "border-accent-200 bg-accent-50 text-accent-700"
                          : "border-slate-200 bg-white text-slate-500"
                    }`}
                  >
                    <span className="font-display">{ROMAN[i]}</span>
                    {step.label}
                  </span>
                </div>
              ))}
            </div>
          }
        />
      </div>

      {/* Global Error Banner */}
      {error && (
        <div className="flex items-start justify-between gap-3">
          <InlineError message={error} className="flex-1" />
          <Button variant="ghost" size="sm" onClick={() => setError(null)}>
            Dismiss
          </Button>
        </div>
      )}

      {/* PHASE 0: CATALOG ERROR */}
      {catalogError && phase === "setup" && (
        <ErrorState
          title="The tarot archives could not be reached"
          message={`${catalogError} — make sure the backend server is running on port 8000.`}
          onRetry={loadCatalog}
        />
      )}

      {/* PHASE 1: SETUP */}
      {phase === "setup" && !catalogError && (
        <div className="grid grid-cols-1 items-start gap-8 lg:grid-cols-2">
          {/* Controls Column */}
          <Panel
            title="Select Your Divination Spread"
            subtitle="Choose the architectural pattern that mirrors your question."
          >
            {showLoading ? (
              <div className="flex justify-center py-12">
                <Spinner label="Gathering arcane archives..." />
              </div>
            ) : (
              <div className="space-y-5">
                <div>
                  <label
                    htmlFor="tarot-spread-select"
                    className="mb-2 block text-[12.5px] font-semibold uppercase tracking-wider text-primary-700"
                  >
                    Spread Format
                  </label>
                  <select
                    id="tarot-spread-select"
                    value={spreadId}
                    onChange={(e) => setSpreadId(e.target.value)}
                    className="w-full cursor-pointer rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-sm text-slate-800 transition focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  >
                    {(spreads || []).map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name} ({s.card_count} {s.card_count === 1 ? "card" : "cards"})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <label
                      htmlFor="tarot-question-input"
                      className="text-[12.5px] font-semibold uppercase tracking-wider text-primary-700"
                    >
                      Your Sacred Question / Focus (Optional)
                    </label>
                    <kbd className="rounded-md border border-slate-200 bg-slate-100 px-1.5 py-0.5 font-sans text-[10px] font-semibold text-slate-500">⌘↵</kbd>
                  </div>
                  <textarea
                    id="tarot-question-input"
                    rows={3}
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={handleQuestionKeyDown}
                    placeholder="e.g., What underlying energies are shaping my career path?"
                    className="w-full rounded-[10px] border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 shadow-xs transition placeholder:text-slate-500 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                  />
                </div>

                <div className="flex items-center justify-between pt-1">
                  <label className="flex cursor-pointer items-center gap-2.5 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      checked={allowReversals}
                      onChange={(e) => setAllowReversals(e.target.checked)}
                      className="h-4 w-4 cursor-pointer rounded border-slate-300 text-primary-600 accent-primary-600 focus:ring-primary-300"
                    />
                    <span>Allow Reversed Cards (Shadow Meanings)</span>
                  </label>
                </div>

                <div className="flex flex-col gap-3 pt-2">
                  <Button fullWidth size="lg" icon={SparkleIcon} onClick={handleStartRitual}>
                    Begin Shuffling Ritual &amp; Draw Cards
                  </Button>
                  <Button variant="ghost" size="sm" fullWidth onClick={handleInstantDraw}>
                    Skip Ritual (Instant Auto-Draw)
                  </Button>
                </div>
              </div>
            )}
          </Panel>

          {/* Spread Preview Column */}
          <Panel
            title={`Spread Preview: ${selectedSpread?.name || "…"}`}
            subtitle={selectedSpread?.description || "Geometrical placement of drawn archetypes."}
          >
            <SpreadLayout spreadDef={selectedSpread} cards={null} />

            <div className="mt-6 space-y-2">
              <span className="block text-[12.5px] font-semibold uppercase tracking-wider text-primary-600">
                Position Meanings:
              </span>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {(selectedSpread?.positions || []).map((pos, idx) => (
                  <div
                    key={pos.position || idx}
                    className="rounded-lg border border-slate-200 bg-slate-50/70 p-2 text-xs"
                  >
                    <span className="font-semibold text-accent-700">
                      #{pos.position}: {pos.name}
                    </span>
                    <p className="mt-0.5 text-sm text-slate-500">{pos.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </Panel>
        </div>
      )}

      {/* PHASE 2: SHUFFLING */}
      {phase === "shuffling" && (
        <Panel padded={false}>
          <ShuffleAnimation
            deckName={deck?.name || "Rider-Waite Smith Tarot"}
            question={question}
            onComplete={handleShuffleComplete}
          />
        </Panel>
      )}

      {/* PHASE 3: SELECTING CARDS */}
      {phase === "selecting" && (
        <Panel>
          {shuffledCards.length === 0 ? (
            // The deck failed to arrive — recoverable state instead of a dead empty arc.
            <EmptyState
              icon={CardsIcon}
              title="The deck could not be prepared"
              description="The shuffled deck did not arrive from the oracle server. You can retry the ritual or use the instant auto-draw instead."
              action={
                <div className="flex flex-wrap items-center justify-center gap-3">
                  <Button size="sm" icon={RetryIcon} onClick={handleStartRitual}>
                    Retry Shuffling Ritual
                  </Button>
                  <Button variant="secondary" size="sm" onClick={handleInstantDraw}>
                    Instant Auto-Draw
                  </Button>
                </div>
              }
            />
          ) : (
            <>
              {/* Selected cards mapped onto the spread geometry with meanings */}
              <SelectionBoard spread={selectedSpread} selections={liveSelections} />

              <CardSelection
                deck={shuffledCards}
                spread={selectedSpread}
                allowReversals={allowReversals}
                selections={liveSelections}
                onSelectionsChange={setLiveSelections}
                onCompleteSelection={handleCompleteSelection}
              />
            </>
          )}
        </Panel>
      )}

      {/* PHASE 4: INTERPRETING LOADING */}
      {phase === "interpreting" && (
        <div className="flex flex-col items-center justify-center gap-5 py-20 text-center">
          <Spinner className="h-10 w-10" />
          <div>
            <h3 className="font-display text-xl font-bold text-slate-900">
              Interpreting Arcane Alignments
            </h3>
            <p className="mx-auto mt-1 max-w-sm text-xs text-slate-500">
              Synthesizing elemental dynamics, numerology, reversals, and position contexts...
            </p>
          </div>
        </div>
      )}

      {/* PHASE 5: DIVINATION RESULTS */}
      {phase === "results" && result && (
        <div className="space-y-8">
          {/* Results Summary */}
          <Panel>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <Badge tone="accent">Divination Complete</Badge>
                <h2 className="mt-2 font-display text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                  {result.spread_name}
                </h2>
                {result.question && (
                  <p className="mt-2 text-sm italic text-primary-800">
                    Inquiry: &ldquo;{result.question}&rdquo;
                  </p>
                )}
              </div>

              <Button variant="secondary" size="sm" icon={RetryIcon} onClick={resetRitual}>
                Perform Another Reading
              </Button>
            </div>

            {/* Narrative Opening & Summary */}
            {(result.narrative?.summary || result.narrative?.opening) && (
              <div className="mt-6 border-t border-slate-100 pt-6">
                <p className="font-display text-base leading-relaxed text-slate-800">
                  {result.narrative?.summary || result.narrative?.opening}
                </p>
              </div>
            )}
          </Panel>

          {/* Interactive Card Reveal & Inspection Carousel */}
          <div>
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <h3 className="font-display text-lg font-bold text-slate-900">
                Cards in Spread ({result.cards?.length})
              </h3>
              <span className="text-xs text-slate-500">Click any card to inspect its guidance</span>
            </div>
            <CardReveal cards={result.cards} />
          </div>

          {/* Spread Geometry Board */}
          <Panel title="Altar Placement Geometry">
            <SpreadLayout spreadDef={selectedSpread} cards={result.cards} />
          </Panel>

          {/* Elemental, Arcana, Reversal & Numerology Analytics */}
          <ReadingAnalysisPanel analysis={result.analysis} />

          {/* Full Narrative Breakdown */}
          {result.narrative?.body && result.narrative.body.length > 0 && (
            <Panel title="Synthesis & Deeper Meaning">
              <ul className="space-y-2.5">
                {result.narrative.body.map((line, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-3 text-sm leading-relaxed text-slate-700"
                  >
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-500" />
                    <span>{line}</span>
                  </li>
                ))}
              </ul>
              {result.narrative.closing && (
                <p className="mt-4 border-t border-slate-100 pt-3 text-sm italic leading-relaxed text-primary-900/70">
                  {result.narrative.closing}
                </p>
              )}
            </Panel>
          )}

          {/* Guidance Points */}
          {result.guidance && result.guidance.length > 0 && (
            <Panel title="Actionable Advice & Divinatory Counsel">
              <ul className="space-y-2.5">
                {result.guidance.map((item, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700">
                    <SparkleIcon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent-500" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </Panel>
          )}

          {/* Export Dossier & Persistence Actions */}
          <Panel
            title="Export & Archive"
            subtitle="Download your dossier or revisit the reading in your archives."
          >
            {result.reading_id ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm text-emerald-700">
                  <CheckIcon className="h-4 w-4" />
                  <span>Reading preserved to your account history archives.</span>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={FileTextIcon}
                    loading={exporting === "pdf"}
                    disabled={exporting !== null}
                    onClick={() => handleExport("pdf")}
                  >
                    {exporting === "pdf" ? "Exporting Dossier..." : "Export PDF Dossier"}
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={TableIcon}
                    loading={exporting === "excel"}
                    disabled={exporting !== null}
                    onClick={() => handleExport("excel")}
                  >
                    {exporting === "excel" ? "Exporting Data..." : "Export Excel Workbook"}
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    href={`/readings/${result.reading_id}`}
                    iconRight={ArrowRightIcon}
                  >
                    View in Archives
                  </Button>
                </div>
              </div>
            ) : (
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs leading-relaxed text-slate-600">
                {user
                  ? "This reading was not saved to your timeline. Make sure you are signed in, then draw again."
                  : "You performed this reading as a guest. "}
                {!user && (
                  <>
                    <Link
                      href="/login"
                      className="font-medium text-primary-600 underline transition-colors hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                    >
                      Sign in or register
                    </Link>{" "}
                    to save readings permanently to your personal timeline.
                  </>
                )}
              </div>
            )}

            {result.disclaimer && (
              <p className="mt-4 flex items-start gap-2 rounded-xl border border-primary-200 bg-primary-50/70 px-4 py-3 text-xs leading-relaxed text-primary-900/70">
                <ShieldIcon className="mt-0.5 h-4 w-4 shrink-0 text-accent-500" />
                {result.disclaimer}
              </p>
            )}

            <p className="mt-4 text-center text-[12.5px] text-slate-500">
              {result.metadata?.engine} • relevance{" "}
              {Math.round((result.metadata?.overall_relevance || 0.95) * 100)}% • Fisher-Yates PRNG
            </p>
          </Panel>

          {/* AI INTERPRETATION SECTION (opt-in) */}
          <AiInsightsPanel
            readingTypeLabel="tarot reading"
            loading={aiLoading}
            error={aiError}
            interpretation={aiInterpretation}
            onGenerate={handleGenerateAi}
          />
        </div>
      )}
      {result && result.reading_id && (
        <RecommendationsSection
          readingId={result.reading_id}
          generateFn={async () => generateRecommendations({
            tarot_reading_id: result.reading_id,
            max_total: 8,
            per_type: 2,
          })}
          autoGenerate={false}
        />
      )}
      {result && (
        <ChatBot
          readingId={result.reading_id}
          readingType="tarot"
          result={result}
          position="fixed"
        />
      )}
    </div>
  );
}
