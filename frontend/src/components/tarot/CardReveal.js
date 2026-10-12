import React, { useState } from "react";
import Image from "next/image";
import { Badge, Panel } from "@/components/ui";

export default function CardReveal({ cards = [], onCardSelect, activeIndex = 0 }) {
  const [selectedIdx, setSelectedIdx] = useState(activeIndex);

  if (!cards || cards.length === 0) return null;

  const currentCard = cards[selectedIdx] || cards[0];

  return (
    <div className="my-6 w-full">
      {/* Cards Ribbon / Selector */}
      <div className="flex items-center justify-center gap-3 overflow-x-auto px-2 py-4 sm:gap-4">
        {cards.map((c, idx) => {
          const isSelected = selectedIdx === idx;
          return (
            <button
              key={c.position || idx}
              type="button"
              onClick={() => {
                setSelectedIdx(idx);
                if (onCardSelect) onCardSelect(c, idx);
              }}
              className={`flex cursor-pointer flex-col items-center rounded-xl p-2 transition-all duration-300 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500 ${
                isSelected
                  ? "-translate-y-2 border-2 border-accent-400 bg-white shadow-lg shadow-primary-200"
                  : "border border-primary-200 bg-white/70 opacity-80 hover:-translate-y-1 hover:border-primary-300 hover:opacity-100"
              }`}
            >
              <div className="mb-1 font-mono text-[10px] font-semibold text-primary-700">
                {c.position_name || `Pos ${c.position || idx + 1}`}
              </div>
              <div className="relative h-32 w-20 overflow-hidden rounded-md bg-primary-950 shadow-md ring-1 ring-slate-200 sm:h-36 sm:w-24">
                <div
                  className={`relative h-full w-full transition-transform duration-500 ${
                    c.is_reversed ? "rotate-180" : ""
                  }`}
                >
                  {c.image_path ? (
                    <Image
                      src={`/${c.image_path.replace(/^\/+/, "")}`}
                      alt={c.card_name}
                      fill
                      className="object-cover"
                      sizes="(max-width: 640px) 80px, 96px"
                    />
                  ) : (
                    <div className="tarot-card-back flex h-full w-full items-center justify-center p-1 text-center text-xs text-accent-300">
                      {c.card_name}
                    </div>
                  )}
                </div>
              </div>
              <span className="mt-2 max-w-[90px] truncate text-center text-[11px] font-medium text-slate-800">
                {c.card_name}
              </span>
              {c.is_reversed && (
                <Badge tone="accent" className="mt-1 text-[9px] uppercase">
                  Reversed
                </Badge>
              )}
            </button>
          );
        })}
      </div>

      {/* Deep-Dive Inspection Card of Selected Card */}
      {currentCard && (
        <Panel className="mt-8">
          <div className="flex flex-col items-center gap-6 sm:gap-8 md:flex-row md:items-start">
            {/* Card Visual Spotlight */}
            <div className="flex flex-shrink-0 flex-col items-center">
              <div
                className={`relative h-64 w-40 overflow-hidden rounded-xl border-2 border-accent-400/70 shadow-xl transition-transform duration-500 sm:h-72 sm:w-48 ${
                  currentCard.is_reversed ? "rotate-180" : ""
                }`}
              >
                {currentCard.image_path ? (
                  <Image
                    src={`/${currentCard.image_path.replace(/^\/+/, "")}`}
                    alt={currentCard.card_name}
                    fill
                    className="object-cover"
                    sizes="(max-width: 640px) 160px, 192px"
                    priority
                  />
                ) : (
                  <div className="tarot-card-back flex h-full w-full items-center justify-center text-accent-300">
                    {currentCard.card_name}
                  </div>
                )}
              </div>
              <div className="mt-3 text-center">
                <Badge tone="primary">
                  {currentCard.orientation || (currentCard.is_reversed ? "Reversed" : "Upright")}
                </Badge>
              </div>
            </div>

            {/* Interpretation Details */}
            <div className="flex-1 space-y-4 text-left">
              <div>
                <div className="flex flex-wrap items-center gap-2 font-mono text-xs uppercase tracking-widest text-accent-600">
                  <span>Position {currentCard.position}:</span>
                  <span className="font-bold text-primary-700">{currentCard.position_name}</span>
                </div>
                <h3 className="mt-1 font-display text-2xl font-bold text-slate-900 sm:text-3xl">
                  {currentCard.card_name}
                </h3>
                {currentCard.position_description && (
                  <p className="mt-0.5 text-xs italic text-slate-500">
                    &ldquo;{currentCard.position_description}&rdquo;
                  </p>
                )}
              </div>

              {/* Badges / Keywords */}
              {(currentCard.keywords?.length > 0 ||
                currentCard.element ||
                currentCard.arcana ||
                currentCard.suit ||
                typeof currentCard.number === "number") && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {currentCard.keywords?.map((kw, i) => (
                    <Badge key={i} tone="primary">
                      {kw}
                    </Badge>
                  ))}
                  {typeof currentCard.number === "number" && (
                    <Badge tone="slate">No. {currentCard.number}</Badge>
                  )}
                  {currentCard.suit && (
                    <Badge tone="emerald">
                      Suit: {currentCard.suit.charAt(0).toUpperCase() + currentCard.suit.slice(1)}
                    </Badge>
                  )}
                  {currentCard.element && (
                    <Badge tone="indigo">Element: {currentCard.element}</Badge>
                  )}
                  {currentCard.arcana && (
                    <Badge tone="accent" className="uppercase">
                      {currentCard.arcana} Arcana
                    </Badge>
                  )}
                </div>
              )}

              {/* Core Meaning */}
              <div className="pt-2">
                <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-primary-700">
                  Essence &amp; Meaning
                </h4>
                <p className="text-sm leading-relaxed text-slate-700">
                  {currentCard.core_meaning || currentCard.meaning}
                </p>
              </div>

              {/* Position Context */}
              {currentCard.position_context && (
                <div className="border-t border-primary-100 pt-2">
                  <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-accent-700">
                    Guidance For This Position
                  </h4>
                  <p className="text-sm leading-relaxed text-primary-900/80">
                    {currentCard.position_context}
                  </p>
                </div>
              )}

              {/* Fortune telling hints if any */}
              {currentCard.fortune_telling && currentCard.fortune_telling.length > 0 && (
                <div className="border-t border-slate-100 pt-2">
                  <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Divinatory Omens
                  </h4>
                  <ul className="list-inside list-disc space-y-1 text-xs text-slate-600">
                    {currentCard.fortune_telling.slice(0, 3).map((omen, i) => (
                      <li key={i}>{omen}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Domain-specific guidance (love / career / spiritual) */}
              {currentCard.domain_guidance && currentCard.domain_guidance.length > 0 && (
                <div className="border-t border-slate-100 pt-2">
                  <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Domain Guidance
                  </h4>
                  <div className="space-y-2">
                    {currentCard.domain_guidance.map((g, i) => (
                      <div
                        key={g.domain || i}
                        className="rounded-xl border border-primary-100 bg-primary-50/50 p-3"
                      >
                        <p className="text-[10px] font-bold uppercase tracking-wider text-primary-700">
                          {g.label || g.domain}
                        </p>
                        <p className="mt-1 text-xs leading-relaxed text-slate-700">{g.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Expanded light/shadow symbolism for the current orientation */}
              {currentCard.expanded_meanings && currentCard.expanded_meanings.length > 0 && (
                <div className="border-t border-slate-100 pt-2">
                  <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    {currentCard.is_reversed ? "Shadow Insights" : "Light Insights"}
                    <span className="ml-1 font-normal normal-case text-slate-400">
                      — deeper symbolism for this orientation
                    </span>
                  </h4>
                  <ul className="list-inside list-disc space-y-1 text-xs leading-relaxed text-slate-600">
                    {currentCard.expanded_meanings.map((m, i) => (
                      <li key={i}>{m}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </Panel>
      )}
    </div>
  );
}
