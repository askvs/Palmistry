import { api } from "./api";

export function getTarotSpreads() {
  return api.get("/api/v1/tarot/spreads");
}

export function getTarotDecks() {
  return api.get("/api/v1/tarot/decks");
}

export function drawTarotSpread({ spreadId, deckId, question, allowReversals }) {
  return api.post("/api/v1/tarot/draw", {
    spread_id: spreadId,
    deck_id: deckId || "rider_waite_smith",
    question: question && question.trim() ? question.trim() : null,
    allow_reversals: Boolean(allowReversals),
  });
}

export function getShuffledDeck({ deckId, seed } = {}) {
  const params = new URLSearchParams();
  if (deckId) params.append("deck_id", deckId);
  if (seed !== undefined && seed !== null) params.append("seed", seed);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return api.get(`/api/v1/tarot/shuffle${qs}`);
}

export function interpretTarotSelection({ spreadId, deckId, cards, question }) {
  return api.post("/api/v1/tarot/interpret", {
    spread_id: spreadId,
    deck_id: deckId || "rider_waite_smith",
    cards: cards.map((c) => ({
      card: c.card || c.card_id || c.name || c.id,
      is_reversed: Boolean(c.is_reversed),
    })),
    question: question && question.trim() ? question.trim() : null,
  });
}

