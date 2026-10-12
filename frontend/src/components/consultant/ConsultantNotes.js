// Consultant Notes — the private note-taking surface.
import { Button, Panel } from "@/components/ui";
import { CheckIcon, PencilIcon } from "@/components/icons";
import { SourceBadge } from "@/components/consultant/shared";

export default function ConsultantNotes({
  value = "",
  onChange,
  onSaveDraft,
  onSaveConsultation,
  saving = false,
  saved = false,
  disabled = false,
  contextLabel = "this client",
}) {
  return (
    <Panel
      title="Consultant Notes"
      subtitle={`Private notes for ${contextLabel} — never shown to the client`}
      action={<SourceBadge source="local" />}
    >
      <div className="space-y-4">
        <label className="block">
          <span className="sr-only" id="consultant-notes-label">
            Private consultation notes
          </span>
          <textarea
            value={value}
            onChange={(event) => onChange?.(event.target.value)}
            rows={14}
            disabled={disabled}
            placeholder="Write private consultation notes…"
            aria-labelledby="consultant-notes-label"
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm leading-relaxed text-slate-800 transition placeholder:text-slate-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:opacity-60"
          />
        </label>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-slate-400">
            {saved ? (
              <span className="inline-flex items-center gap-1.5 font-medium text-emerald-600">
                <CheckIcon className="h-3.5 w-3.5" />
                Saved
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5">
                <PencilIcon className="h-3.5 w-3.5" />
                Drafts save to this device until the notes API is available.
              </span>
            )}
          </p>

          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              icon={PencilIcon}
              loading={saving}
              disabled={disabled || saving}
              onClick={() => onSaveDraft?.(value)}
            >
              Save draft
            </Button>
            <Button loading={saving} disabled={disabled || saving} onClick={() => onSaveConsultation?.(value)}>
              Save consultation
            </Button>
          </div>
        </div>
      </div>
    </Panel>
  );
}
