// Spread authoring for the tarot reader (Tarot Reader: create spreads).
import { useEffect, useMemo, useState } from "react";
import {
  Badge,
  Button,
  ConfirmDialog,
  EmptyState,
  ErrorState,
  InlineError,
  Panel,
  SkeletonRow,
  useToast,
} from "@/components/ui";
import { useAsyncData } from "@/hooks/useAsyncData";
import {
  createCustomSpread,
  deleteCustomSpread,
  listReaderSpreads,
  updateCustomSpread,
} from "@/services/reader";
import {
  ArrowUpDownIcon,
  CardsIcon,
  CheckIcon,
  PencilIcon,
  PlusIcon,
  TrashIcon,
} from "@/components/icons";

const EMPTY_POSITION = { name: "", description: "" };
const MAX_POSITIONS = 10;

function emptyDraft(name = "", description = "", positions = []) {
  return {
    name,
    description,
    positions: positions.length
      ? positions
      : [EMPTY_POSITION, EMPTY_POSITION, EMPTY_POSITION],
  };
}

// Move an item inside a list; returns a new array.
function move(list, from, to) {
  if (to < 0 || to >= list.length) return list;
  const copy = [...list];
  const [item] = copy.splice(from, 1);
  copy.splice(to, 0, item);
  return copy;
}

function PositionEditor({ positions, onChange }) {
  function update(index, field, value) {
    onChange(positions.map((p, i) => (i === index ? { ...p, [field]: value } : p)));
  }

  return (
    <ol className="space-y-2.5">
      {positions.map((position, index) => (
        <li
          key={index}
          className="rounded-2xl border border-slate-200 bg-slate-50/50 p-3"
        >
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-bold uppercase tracking-wide text-slate-400">
              Card {index + 1}
            </span>
            <div className="flex items-center gap-1">
              <Button
                size="sm"
                variant="ghost"
                aria-label={`Move position ${index + 1} up`}
                disabled={index === 0}
                onClick={() => onChange(move(positions, index, index - 1))}
              >
                <ArrowUpDownIcon className="h-3.5 w-3.5 rotate-180" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                aria-label={`Move position ${index + 1} down`}
                disabled={index === positions.length - 1}
                onClick={() => onChange(move(positions, index, index + 1))}
              >
                <ArrowUpDownIcon className="h-3.5 w-3.5" />
              </Button>
              <Button
                size="sm"
                variant="dangerGhost"
                aria-label={`Remove position ${index + 1}`}
                disabled={positions.length <= 1}
                onClick={() => onChange(positions.filter((_, i) => i !== index))}
              >
                <TrashIcon className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>

          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            <label className="block">
              <span className="sr-only">Position {index + 1} name</span>
              <input
                type="text"
                value={position.name}
                onChange={(event) => update(index, "name", event.target.value)}
                placeholder="e.g. The Obstacle"
                maxLength={80}
                className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-800 transition placeholder:text-slate-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
              />
            </label>
            <label className="block">
              <span className="sr-only">Position {index + 1} meaning</span>
              <input
                type="text"
                value={position.description || ""}
                onChange={(event) => update(index, "description", event.target.value)}
                placeholder="What this position answers (optional)"
                maxLength={500}
                className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-800 transition placeholder:text-slate-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
              />
            </label>
          </div>
        </li>
      ))}
    </ol>
  );
}

export default function SpreadStudio() {
  const toast = useToast();
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState(null);
  const [visibility, setVisibility] = useState("private");
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState(null);
  const [pendingDelete, setPendingDelete] = useState(null);

  const { data, error, loading, refresh } = useAsyncData(listReaderSpreads);
  const spreads = useMemo(() => data?.custom || [], [data]);

  function startCreate() {
    setEditingId("new");
    setDraft(emptyDraft());
    setVisibility("private");
    setFormError(null);
  }

  function startEdit(spread) {
    setEditingId(spread.id);
    setDraft({
      name: spread.name,
      description: spread.description || "",
      positions: spread.positions.map((p) => ({
        name: p.name,
        description: p.description || "",
      })),
    });
    setVisibility(spread.visibility);
    setFormError(null);
  }

  function cancel() {
    setEditingId(null);
    setDraft(null);
    setFormError(null);
  }

  async function save(event) {
    event.preventDefault();
    if (!draft || busy) return;

    if (!draft.name.trim()) {
      setFormError("Give the spread a name.");
      return;
    }
    if (draft.positions.some((p) => !p.name.trim())) {
      setFormError("Every position needs a name.");
      return;
    }

    setBusy(true);
    setFormError(null);
    try {
      const payload = {
        name: draft.name.trim(),
        description: draft.description.trim() || null,
        positions: draft.positions.map((p) => ({
          name: p.name.trim(),
          description: p.description.trim() || null,
        })),
        visibility,
      };
      if (editingId === "new") {
        await createCustomSpread(payload);
        toast.success("Spread created", `"${payload.name}" is ready to read with.`);
      } else {
        await updateCustomSpread(editingId, payload);
        toast.success("Spread updated", `"${payload.name}" has been saved.`);
      }
      cancel();
      await refresh();
    } catch (err) {
      setFormError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    setBusy(true);
    try {
      await deleteCustomSpread(pendingDelete.id);
      toast.success("Spread retired", `"${pendingDelete.name}" will no longer be offered.`);
      if (editingId === pendingDelete.id) cancel();
      setPendingDelete(null);
      await refresh();
    } catch (err) {
      setFormError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const editingSpread = useMemo(
    () => spreads.find((s) => s.id === editingId) || null,
    [spreads, editingId]
  );

  return (
    <div className="space-y-5">
      <Panel
        title="Your Spreads"
        subtitle="Reader-authored spreads you can run readings with"
        action={
          <Button
            size="sm"
            icon={PlusIcon}
            onClick={startCreate}
            disabled={editingId === "new"}
          >
            New spread
          </Button>
        }
      >
        {loading ? (
          <SkeletonRow lines={4} />
        ) : error ? (
          <ErrorState message={error.message} onRetry={refresh} />
        ) : spreads.length === 0 ? (
          <EmptyState
            icon={CardsIcon}
            title="No spreads yet"
            description="Author a spread to give your readings a personal structure."
            action={
              <Button size="sm" icon={PlusIcon} onClick={startCreate}>
                New spread
              </Button>
            }
          />
        ) : (
          <ul className="divide-y divide-slate-100">
            {spreads.map((spread) => (
              <li key={spread.id} className="-mx-2 rounded-lg px-2 py-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-sm font-semibold text-slate-900">{spread.name}</p>
                      <Badge tone="primary">{spread.card_count} cards</Badge>
                      <Badge tone={spread.visibility === "shared" ? "emerald" : "slate"}>
                        {spread.visibility === "shared" ? "Shared with readers" : "Private"}
                      </Badge>
                      {!spread.is_owner && <Badge tone="blue">Shared by another reader</Badge>}
                    </div>
                    {spread.description && (
                      <p className="mt-0.5 text-xs text-slate-500">{spread.description}</p>
                    )}
                    <p className="mt-1 text-xs text-slate-400">
                      {spread.positions.map((p) => p.name).join(" · ")}
                    </p>
                  </div>
                  {spread.is_owner && (
                    <div className="flex shrink-0 items-center gap-2">
                      <Button
                        size="sm"
                        variant="secondary"
                        icon={PencilIcon}
                        onClick={() => startEdit(spread)}
                      >
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="dangerGhost"
                        icon={TrashIcon}
                        onClick={() => setPendingDelete(spread)}
                      >
                        Retire
                      </Button>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      {editingId && draft && (
        <Panel
          title={editingId === "new" ? "New spread" : `Edit "${editingSpread?.name || "spread"}"`}
          subtitle="Name the spread, then describe each card position in reading order"
        >
          <form onSubmit={save} className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block">
                <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  Spread name
                </span>
                <input
                  type="text"
                  value={draft.name}
                  onChange={(event) => setDraft({ ...draft, name: event.target.value })}
                  placeholder="e.g. Three Doors"
                  maxLength={120}
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-800 transition placeholder:text-slate-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                />
              </label>
              <label className="block">
                <span className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  Description
                </span>
                <input
                  type="text"
                  value={draft.description}
                  onChange={(event) => setDraft({ ...draft, description: event.target.value })}
                  placeholder="When should this spread be used?"
                  maxLength={2000}
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-800 transition placeholder:text-slate-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                />
              </label>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Visibility</p>
                <div className="mt-1 inline-flex items-center rounded-full border border-slate-200 bg-slate-100/80 p-0.5">
                  {[
                    { value: "private", label: "Private" },
                    { value: "shared", label: "Share with readers" },
                  ].map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      aria-pressed={visibility === option.value}
                      onClick={() => setVisibility(option.value)}
                      className={`cursor-pointer rounded-full px-3 py-1 text-xs font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 ${
                        visibility === option.value
                          ? "bg-white text-slate-900 shadow-xs"
                          : "text-slate-500 hover:text-slate-800"
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>
              <Button
                size="sm"
                variant="secondary"
                icon={PlusIcon}
                disabled={draft.positions.length >= MAX_POSITIONS}
                onClick={() =>
                  setDraft({ ...draft, positions: [...draft.positions, EMPTY_POSITION] })
                }
              >
                Add position
              </Button>
            </div>

            <PositionEditor
              positions={draft.positions}
              onChange={(positions) => setDraft({ ...draft, positions })}
            />

            {formError && <InlineError message={formError} />}

            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs text-slate-400">
                {draft.positions.length} of {MAX_POSITIONS} positions · order is the reading order
              </p>
              <div className="flex items-center gap-2">
                <Button type="button" variant="ghost" size="sm" onClick={cancel}>
                  Cancel
                </Button>
                <Button type="submit" size="sm" icon={CheckIcon} loading={busy}>
                  {editingId === "new" ? "Create spread" : "Save changes"}
                </Button>
              </div>
            </div>
          </form>
        </Panel>
      )}

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="Retire this spread?"
        message={`"${pendingDelete?.name}" will no longer be offered for new readings. Readings already taken with it keep their layout.`}
        confirmLabel="Retire spread"
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
      />
    </div>
  );
}
