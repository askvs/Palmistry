// A ticking "now" for countdowns and time-window UI.
import { useEffect, useState } from "react";

// Re-renders consumers on the given cadence so join windows and countdowns stay
// live without a page reload. Pass `enabled: false` to park the clock when the
// caller has nothing time-sensitive to show.
export function useNow({ intervalMs = 30 * 1000, enabled = true } = {}) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!enabled) return undefined;
    const handle = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(handle);
  }, [intervalMs, enabled]);

  return now;
}
