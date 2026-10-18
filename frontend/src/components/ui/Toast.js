// App-wide toast notifications.
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { CheckCircleIcon, CloseIcon, AlertIcon, InfoIcon } from "@/components/icons";
import { BellIcon } from "@/components/ui/BellIcon";

const ToastContext = createContext(null);

const TONES = {
  success: {
    ring: "ring-emerald-200",
    iconWrap: "bg-emerald-100 text-emerald-600",
    Icon: CheckCircleIcon,
  },
  error: {
    ring: "ring-rose-200",
    iconWrap: "bg-rose-100 text-rose-600",
    Icon: AlertIcon,
  },
  info: {
    ring: "ring-primary-200",
    iconWrap: "bg-primary-100 text-primary-600",
    Icon: InfoIcon,
  },
};

function ToastItem({ toast, onDismiss }) {
  const tone = TONES[toast.tone] || TONES.info;
  const { Icon } = tone;
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setLeaving(true), toast.duration || 4500);
    return () => clearTimeout(timer);
  }, [toast.duration]);

  useEffect(() => {
    if (!leaving) return undefined;
    const timer = setTimeout(() => onDismiss(toast.id), 200);
    return () => clearTimeout(timer);
  }, [leaving, onDismiss, toast.id]);

  return (
    <div
      className={`pointer-events-auto flex w-full items-start gap-3 rounded-2xl bg-white p-4 ring-1 ${tone.ring} shadow-[inset_0_1px_0_rgba(255,255,255,.85),var(--shadow-lift)] transition-all duration-200 ${
        leaving ? "translate-y-1 opacity-0" : "animate-rise-in"
      }`}
    >
      <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${tone.iconWrap}`}>
        <Icon className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1 pt-0.5">
        {toast.title && <p className="text-sm font-semibold text-slate-900">{toast.title}</p>}
        {toast.message && (
          <p className={`text-sm leading-relaxed text-slate-600 ${toast.title ? "mt-0.5" : ""}`}>
            {toast.message}
          </p>
        )}
      </div>
      <button
        type="button"
        onClick={() => setLeaving(true)}
        aria-label="Dismiss notification"
        className="-mr-1 -mt-1 rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 cursor-pointer"
      >
        <CloseIcon className="h-4 w-4" />
      </button>
    </div>
  );
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const idRef = useRef(0);

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((t) => t.id !== id));
  }, []);

  const push = useCallback((tone, title, message, opts = {}) => {
    const id = ++idRef.current;
    setToasts((current) => [
      ...current.slice(-3),
      { id, tone, title, message, duration: opts.duration },
    ]);
    return id;
  }, []);

  const toast = useMemo(
    () => ({
      success: (title, message, opts) => push("success", title, message, opts),
      error: (title, message, opts) => push("error", title, message, opts),
      info: (title, message, opts) => push("info", title, message, opts),
    }),
    [push]
  );

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div
        aria-live="polite"
        aria-label="Notifications"
        className="pointer-events-none fixed inset-x-4 bottom-4 z-50 flex flex-col items-center gap-2.5 sm:inset-x-auto sm:bottom-6 sm:right-6 sm:items-end"
      >
        {toasts.map((t) => (
          <div key={t.id} className="w-full max-w-sm">
            <ToastItem toast={t} onDismiss={dismiss} />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    // Render-safe fallback so components can be used in isolation/tests.
    const noop = () => undefined;
    return { success: noop, error: noop, info: noop };
  }
  return ctx;
}
