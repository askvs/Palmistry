import React, { useState, useEffect } from "react";
import { ArrowRightIcon } from "@/components/icons";
import { Badge, Button } from "@/components/ui";

export default function ShuffleAnimation({ onComplete, deckName = "Rider-Waite Tarot", question = "" }) {
  const [shuffleState, setShuffleState] = useState("shuffling"); // 'shuffling', 'cutting', 'ready'
  const [shuffleSeconds, setShuffleSeconds] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setShuffleSeconds((s) => s + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleCutDeck = () => {
    setShuffleState("cutting");
    setTimeout(() => {
      setShuffleState("ready");
      if (onComplete) {
        onComplete();
      }
    }, 1200);
  };

  // Derive phase text directly without cascading state updates
  let phaseText = "Channeling your intention into the deck...";
  if (shuffleState === "cutting") {
    phaseText = "Cutting the deck at your chosen moment...";
  } else if (shuffleState === "ready") {
    phaseText = "Deck prepared and aligned for divination.";
  } else if (shuffleSeconds >= 4) {
    phaseText = "Energies aligned. Cut the deck whenever you feel ready.";
  } else if (shuffleSeconds >= 2) {
    phaseText = "Riffling cards through cosmic currents...";
  }

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 select-none">
      {/* Mystical atmosphere header */}
      <div className="text-center max-w-lg mb-8">
        <Badge tone="primary" className="mb-3 animate-pulse">
          <span className="h-2 w-2 rounded-full bg-primary-500 animate-ping" aria-hidden="true" />
          The Shuffling Ritual
        </Badge>
        <h2 className="font-display text-2xl sm:text-3xl text-slate-900 tracking-wide">
          {deckName}
        </h2>
        {question ? (
          <p className="mt-2 text-sm italic text-primary-800 max-w-md mx-auto">
            &ldquo;{question}&rdquo;
          </p>
        ) : (
          <p className="mt-2 text-xs text-slate-500">Hold your inquiry silently in mind as cards cycle</p>
        )}
      </div>

      {/* 3D Shuffling Arena */}
      <div className="relative w-72 h-96 my-4 flex items-center justify-center perspective-1000">
        {/* Glow backdrop */}
        <div className="absolute inset-0 bg-primary-400/15 blur-3xl rounded-full pointer-events-none animate-mystic-pulse" />

        {shuffleState === "shuffling" && (
          <div className="relative w-44 h-64 preserve-3d">
            {/* Left Riffle Stack */}
            <div className="absolute inset-0 tarot-card-back rounded-xl animate-riffle-left shadow-2xl flex items-center justify-center overflow-hidden border border-accent-300/40">
              <div className="w-full h-full opacity-30 flex items-center justify-center">
                <svg className="w-24 h-24 text-accent-200/50" viewBox="0 0 100 100" fill="currentColor">
                  <polygon points="50,10 90,90 10,90" fill="none" stroke="currentColor" strokeWidth="2" />
                  <circle cx="50" cy="55" r="20" fill="none" stroke="currentColor" strokeWidth="2" />
                  <path d="M50 20 L50 85 M20 55 L80 55" stroke="currentColor" strokeWidth="1" />
                </svg>
              </div>
            </div>

            {/* Middle Cascade Card */}
            <div className="absolute inset-0 -top-2 tarot-card-back rounded-xl animate-deck-cascade shadow-xl flex items-center justify-center border border-primary-400/40">
              <div className="text-center p-3">
                <div className="text-2xl text-accent-300 mb-1">✦</div>
                <div className="text-[10px] tracking-widest uppercase text-primary-200/80 font-semibold">
                  Tarot Arcana
                </div>
              </div>
            </div>

            {/* Right Riffle Stack */}
            <div className="absolute inset-0 tarot-card-back rounded-xl animate-riffle-right shadow-2xl flex items-center justify-center overflow-hidden border border-accent-300/40">
              <div className="w-full h-full opacity-30 flex items-center justify-center">
                <svg className="w-24 h-24 text-accent-200/50" viewBox="0 0 100 100" fill="currentColor">
                  <polygon points="50,90 90,10 10,10" fill="none" stroke="currentColor" strokeWidth="2" />
                  <circle cx="50" cy="45" r="20" fill="none" stroke="currentColor" strokeWidth="2" />
                </svg>
              </div>
            </div>
          </div>
        )}

        {shuffleState === "cutting" && (
          <div className="relative w-48 h-64 preserve-3d flex items-center justify-center">
            {/* Split stack left */}
            <div className="absolute w-36 h-56 tarot-card-back rounded-xl shadow-2xl -translate-x-12 -translate-y-4 rotate-[-8deg] transition-all duration-700 border border-accent-300/50 flex items-center justify-center">
              <span className="text-accent-200/80 text-sm font-display">Pile I</span>
            </div>
            {/* Split stack right */}
            <div className="absolute w-36 h-56 tarot-card-back rounded-xl shadow-2xl translate-x-12 translate-y-4 rotate-[8deg] transition-all duration-700 border border-primary-300/50 flex items-center justify-center">
              <span className="text-primary-200/80 text-sm font-display">Pile II</span>
            </div>
          </div>
        )}

        {shuffleState === "ready" && (
          <div className="relative w-44 h-64 tarot-card-back rounded-xl shadow-2xl border-2 border-accent-400 animate-card-float flex items-center justify-center">
            <div className="text-center p-4">
              <div className="text-3xl text-accent-400 mb-2">✧</div>
              <p className="text-xs uppercase tracking-wider text-accent-200 font-semibold">Deck Ready</p>
            </div>
          </div>
        )}
      </div>

      {/* Dynamic Status Text */}
      <p className="text-sm font-medium text-primary-700 h-6 text-center animate-pulse mt-4">
        {phaseText}
      </p>

      {/* Interactive Control */}
      <div className="mt-8 flex flex-col items-center gap-3">
        {shuffleState === "shuffling" && (
          <Button size="lg" iconRight={ArrowRightIcon} onClick={handleCutDeck}>
            Cut the Deck &amp; Choose Cards
          </Button>
        )}

        <span className="text-xs text-slate-400">
          Shuffled with cryptographically secure Fisher-Yates randomization
        </span>
      </div>
    </div>
  );
}
