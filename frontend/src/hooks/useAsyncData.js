import { useCallback, useEffect, useState } from "react";

// Async data loader with loading and error state.
export function useAsyncData(loader, { enabled = true } = {}) {
  const [state, setState] = useState({ data: null, error: null, loading: enabled });

  useEffect(() => {
    if (!enabled) {
      return undefined;
    }
    let cancelled = false;
    loader()
      .then((result) => {
        if (!cancelled) {
          setState({ data: result, error: null, loading: false });
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setState({ data: null, error: err, loading: false });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [enabled, loader]);

  const refresh = useCallback(() => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    return loader()
      .then((result) => setState({ data: result, error: null, loading: false }))
      .catch((err) => setState({ data: null, error: err, loading: false }));
  }, [loader]);

  return { ...state, refresh };
}
