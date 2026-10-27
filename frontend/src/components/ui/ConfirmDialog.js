// Accessible confirmation dialog for destructive/irreversible actions.
import { useEffect, useRef } from "react";
import Button from "@/components/ui/Button";
import { AlertIcon, CloseIcon } from "@/components/icons";

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  tone = "danger",
  loading = false,
  onConfirm,
  onCancel,
}) {
  const cancelRef = useRef(null);
  const dialogRef = useRef(null);
  // Latest onCancel, so the trap effect can depend on [open] only and stay
  // stable across parent re-renders (inline-arrow call sites).
  const onCancelRef = useRef(onCancel);
  useEffect(() => {
    onCancelRef.current = onCancel;
  });

  useEffect(() => {
    if (!open) return undefined;
    const previous = document.activeElement;
    const node = dialogRef.current;
    if (!node) return undefined;
    const focusables = () =>
      node.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    (node.querySelector("[data-autofocus]") || focusables()[0])?.focus();
    const onKeyDown = (event) => {
      if (event.key === "Escape") onCancelRef.current?.();
      if (event.key !== "Tab") return;
      const list = Array.from(focusables()).filter((el) => !el.disabled);
      if (list.length === 0) return;
      const first = list[0];
      const last = list[list.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = "";
      previous?.focus?.();
    };
  }, [open]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
    >
      <div
        className="absolute inset-0 bg-slate-950/40 backdrop-blur-[4px] animate-backdrop-in"
        onClick={onCancel}
        aria-hidden="true"
      />
      <div
        ref={dialogRef}
        className="surface-panel shadow-float relative w-full max-w-md animate-dialog-in p-6"
      >
        <button
          type="button"
          onClick={onCancel}
          aria-label="Close dialog"
          className="absolute right-4 top-4 rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 cursor-pointer"
        >
          <CloseIcon className="h-4 w-4" />
        </button>

        <div className="flex items-start gap-3.5">
          {tone === "danger" && (
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-rose-100 text-rose-600">
              <AlertIcon className="h-5 w-5" />
            </span>
          )}
          <div className="pt-0.5">
            <h2 id="confirm-dialog-title" className="text-base font-semibold text-slate-900">
              {title}
            </h2>
            {message && (
              <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{message}</p>
            )}
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-2.5">
          <Button ref={cancelRef} data-autofocus variant="secondary" onClick={onCancel} disabled={loading}>
            {cancelLabel}
          </Button>
          <Button
            variant={tone === "danger" ? "danger" : "primary"}
            onClick={onConfirm}
            loading={loading}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
