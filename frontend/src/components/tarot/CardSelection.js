import React from "react";
import { ArrowRightIcon, CheckCircleIcon, SparkleIcon } from "@/components/icons";
import { Button } from "@/components/ui";

// Pure calculation for card reversal orientation (~20% probability), seeded by the card's position in the arc so the same.
function calculateReversal(card, deckIndex, allowReversals) {
  if (!allowReversals) return false;
  const num = typeof card?.number === "number" ? card.number : 3;
  const seed = (deckIndex * 17 + num * 7 + 11) % 100;
  return seed < 20;
}

export default function CardSelection({
  deck = [], // full shuffled deck from the /shuffle endpoint (78 cards)
  spread,
  allowReversals = true,
  selections = [], // lifted state: [{ position, position_name, card_id, card_name, card, is_reversed }]
  onSelectionsChange,
  onCompleteSelection,
}) {
  const [hoveredIndex, setHoveredIndex] = React.useState(null);

  const totalRequired = spread?.positions?.length || 3;
  const currentPositionIdx = selections.length;
  const currentPosition = spread?.positions?.[currentPositionIdx];
  const isComplete = selections.length >= totalRequired;
  const pickedIds = new Set(selections.map((s) => s.card_id));

  function commit(nextSelections) {
    if (onSelectionsChange) onSelectionsChange(nextSelections);
    // If that was the last required card, auto-advance to interpretation.
    if (nextSelections.length >= totalRequired && onCompleteSelection) {
      setTimeout(() => onCompleteSelection(nextSelections), 700);
    }
  }

  function handlePickCard(card, deckIndex) {
    if (isComplete || pickedIds.has(card.id)) return;

    const posNum = currentPositionIdx + 1;
    commit([
      ...selections,
      {
        position: posNum,
        position_name: currentPosition?.name || `Position ${posNum}`,
        card,
        card_id: card.id,
        card_name: card.name,
        is_reversed: calculateReversal(card, deckIndex, allowReversals),
      },
    ]);
  }

  function handleRemoveCard(cardId) {
    if (isComplete) return;
    const next = selections
      .filter((s) => s.card_id !== cardId)
      .map((s, i) => ({
        ...s,
        position: i + 1,
        position_name: spread?.positions?.[i]?.name || `Position ${i + 1}`,
      }));
    commit(next);
  }

  const handleQuickPickRemaining = () => {
    const pickedIdsNow = new Set(selections.map((s) => s.card_id));
    const available = deck.filter((c) => !pickedIdsNow.has(c.id));
    const remainingCount = totalRequired - selections.length;
    if (remainingCount <= 0 || available.length === 0) return;

    const next = [...selections];
    for (let i = 0; i < remainingCount && i < available.length; i++) {
      const card = available[i];
      const deckIndex = deck.indexOf(card);
      const posIdx = next.length;
      const posDef = spread?.positions?.[posIdx];
      next.push({
        position: posIdx + 1,
        position_name: posDef?.name || `Position ${posIdx + 1}`,
        card,
        card_id: card.id,
        card_name: card.name,
        is_reversed: calculateReversal(card, deckIndex, allowReversals),
      });
    }
    commit(next);
  };

  const deckSize = deck.length;
  const availableCount = Math.max(0, deckSize - selections.length);
  const remainingSlots = totalRequired - selections.length;

  return (
    <div className="w-full flex flex-col items-center px-2 sm:px-4">
      {/* Instruction banner */}
      <div className="my-4 w-full max-w-2xl rounded-2xl border border-primary-200 bg-primary-50/80 p-4 text-center shadow-xs">
        {!isComplete ? (
          <div>
            <div className="mb-1 flex items-center justify-center gap-2 text-xs font-semibold uppercase tracking-wider text-primary-700">
              <SparkleIcon className="h-3.5 w-3.5" aria-hidden="true" />
              <span>
                Select card {currentPositionIdx + 1} of {totalRequired}
              </span>
            </div>
            <p className="font-display text-sm font-semibold text-slate-900">
              For: <span className="text-primary-700">{currentPosition?.name}</span>
            </p>
            <p className="mt-0.5 text-xs text-slate-600">
              &ldquo;{currentPosition?.description}&rdquo;
            </p>
            <p className="mt-1.5 text-[11px] italic text-slate-500">
              The card you pick takes this exact position — tap its numbered slot in the arc below
              to send it back to the deck.
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2.5">
            <span className="flex items-center gap-2 text-sm font-semibold text-emerald-700">
              <CheckCircleIcon className="h-4 w-4 text-emerald-500" />
              All {totalRequired} cards chosen! Revealing divine patterns...
            </span>
            <Button
              size="sm"
              iconRight={ArrowRightIcon}
              onClick={() => onCompleteSelection && onCompleteSelection(selections)}
            >
              Reveal the Reading Now
            </Button>
          </div>
        )}
      </div>

      {/* Card Picking Ribbon: the FULL shuffled deck — every card remains selectable until it is drawn, so the count can never strand the user. */}
      {!isComplete && (
        <div className="my-4 w-full max-w-5xl">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2 px-2">
            <span className="text-xs font-medium text-primary-700">
              Draw from the full {deckSize}-card deck:{" "}
              <strong>{availableCount} still available</strong>
            </span>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={handleQuickPickRemaining}>
                Auto-pick remaining {remainingSlots}
              </Button>
              {selections.length > 0 && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => onSelectionsChange && onSelectionsChange([])}
                >
                  Clear picks
                </Button>
              )}
            </div>
          </div>

          {/* Horizontal scrollable cards */}
          <div className="relative overflow-x-auto rounded-2xl border border-primary-200 bg-primary-50/50 px-4 pb-6 pt-4 shadow-inner">
            <div className="flex items-center justify-start min-w-max py-4 px-2 sm:justify-center">
              {deck.map((card, idx) => {
                const isPicked = pickedIds.has(card.id);
                const isHovered = hoveredIndex === idx;
                const pickedAt = isPicked
                  ? selections.findIndex((s) => s.card_id === card.id) + 1
                  : null;

                if (isPicked) {
                  return (
                    <button
                      key={card.id || idx}
                      type="button"
                      onClick={() => handleRemoveCard(card.id)}
                      title="Send this card back to the deck"
                      className="relative -mr-4 h-28 w-14 flex-shrink-0 cursor-pointer rounded-md border border-slate-200 bg-slate-50 opacity-45 transition-all hover:opacity-80 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 sm:h-32 sm:w-16"
                    >
                      <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-primary-600">
                        {pickedAt}
                      </span>
                    </button>
                  );
                }

                return (
                  <button
                    key={card.id || idx}
                    type="button"
                    onClick={() => handlePickCard(card, idx)}
                    onMouseEnter={() => setHoveredIndex(idx)}
                    onMouseLeave={() => setHoveredIndex(null)}
                    aria-label={`Draw card ${idx + 1}`}
                    className={`tarot-card-back relative -mr-4 flex h-28 w-14 flex-shrink-0 cursor-pointer items-center rounded-md shadow-md transition-all duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500 sm:h-32 sm:w-16 ${
                      isHovered
                        ? "z-30 -translate-y-4 scale-110 border border-accent-300 shadow-xl shadow-primary-300/60"
                        : "z-10 hover:-translate-y-2"
                    }`}
                  >
                    <div className="flex w-full flex-col items-center justify-between p-1.5 opacity-60">
                      <span className="text-[9px] text-accent-300">✦</span>
                      <span className="text-[7px] tracking-widest text-primary-200">TAROT</span>
                      <span className="text-[9px] text-accent-300">✦</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
