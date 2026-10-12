import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import {
  fetchCurrentUser,
  loginUser,
  loginViaPortal,
  logoutUser,
  refreshSession,
  registerUser,
  registerViaPortal,
} from "@/services/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Restore session on mount.
  // OAuth landings already carry the refresh cookie.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const refreshed = await refreshSession();
        if (!cancelled) setUser(refreshed.user);
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (credentials) => {
    const payload = await loginUser(credentials);
    setUser(payload.user);
    return payload.user;
  }, []);

  const loginPortal = useCallback(async (slug, credentials) => {
    const payload = await loginViaPortal(slug, credentials);
    setUser(payload.user);
    return payload.user;
  }, []);

  const register = useCallback(async (details) => {
    const payload = await registerUser(details);
    setUser(payload.user);
    return payload.user;
  }, []);

  const registerPortal = useCallback(async (slug, details) => {
    const payload = await registerViaPortal(slug, details);
    setUser(payload.user);
    return payload.user;
  }, []);

  const refresh = useCallback(async () => {
    const payload = await refreshSession();
    setUser(payload.user);
    return payload.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await logoutUser();
    } finally {
      setUser(null);
    }
  }, []);

  const reloadUser = useCallback(async () => {
    const fresh = await fetchCurrentUser();
    setUser(fresh);
    return fresh;
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      loginPortal,
      register,
      registerPortal,
      refresh,
      logout,
      reloadUser,
    }),
    [user, loading, login, loginPortal, register, registerPortal, refresh, logout, reloadUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }
  return ctx;
}
