// Porcelain tooltip — 150ms show delay, focus-triggered (touch-safe), Esc dismisses (spec §5.12).
import { useEffect, useId, useRef, useState } from "react";

export default function Tooltip({ label, children, side = "top" }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const timer = useRef(null);
  const show = () => { timer.current = setTimeout(() => setOpen(true), 150); };
  const hide = () => { clearTimeout(timer.current); setOpen(false); };
  useEffect(() => () => clearTimeout(timer.current), []);
  const position = side === "top"
    ? "bottom-full left-1/2 mb-1.5 -translate-x-1/2"
    : "top-full left-1/2 mt-1.5 -translate-x-1/2";
  return (
    <span
      className="relative inline-flex"
      onMouseEnter={show} onMouseLeave={hide}
      onFocus={show} onBlur={hide}
      onKeyDown={(e) => { if (e.key === "Escape") hide(); }}
    >
      <span aria-describedby={open ? id : undefined}>{children}</span>
      {open && (
        <span
          id={id} role="tooltip"
          className={`pointer-events-none absolute z-30 w-max max-w-[240px] rounded-[10px] bg-white px-2.5 py-1.5 text-[11px] leading-relaxed text-slate-600 shadow-lift ring-1 ring-slate-200 animate-rise-in ${position}`}
        >
          {label}
        </span>
      )}
    </span>
  );
}
