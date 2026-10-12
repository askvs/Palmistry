import { Spinner } from "@/components/ui";

// LoadingSpinner – centered, labelled spinner kept as a thin wrapper around the kit Spinner for existing callers (AI.
export default function LoadingSpinner({ label = "Generating AI insight…" }) {
  return (
    <div className="flex animate-fade-in flex-col items-center gap-3 py-6">
      <Spinner className="h-6 w-6" label={label} />
    </div>
  );
}
