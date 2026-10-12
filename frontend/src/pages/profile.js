import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import { useAuth } from "@/hooks/useAuth";
import { getReadingAnalytics, listReadings } from "@/services/readings";
import {
  AGE_GROUP_OPTIONS,
  DECK_OPTIONS,
  INTEREST_OPTIONS,
  SPREAD_OPTIONS,
  TONE_OPTIONS,
  createGoal,
  deleteGoal,
  fetchAvatarBlobUrl,
  fetchProfile,
  removeAvatar,
  replaceInterests,
  updateGoal,
  updateProfile,
  uploadAvatar,
} from "@/services/profile";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  InlineError,
  PageHeader,
  Panel,
  SkeletonCards,
  SkeletonRow,
  Spinner,
  useToast,
} from "@/components/ui";
import {
  ArrowRightIcon,
  CalendarIcon,
  CameraIcon,
  CardsIcon,
  CheckIcon,
  FileTextIcon,
  HandIcon,
  ImageIcon,
  PencilIcon,
  SparkleIcon,
  TrashIcon,
  UserIcon,
} from "@/components/icons";
import { roleMeta } from "@/lib/roles";

const MAX_INTERESTS = 10;
const AVATAR_ACCEPT = ["image/jpeg", "image/png", "image/webp"];
const AVATAR_MAX_BYTES = 5 * 1024 * 1024;

// Unified input class — every field on this page uses this exact string.
const INPUT_CLASS =
  "w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 shadow-xs transition focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-500/20 disabled:cursor-not-allowed disabled:opacity-60";

const QUICK_ACTIONS = [
  { href: "/readings/palm", Icon: HandIcon, title: "New Palm Scan", hint: "Upload a palm photo for CV analysis" },
  { href: "/readings/tarot", Icon: CardsIcon, title: "New Tarot Draw", hint: "Shuffle and draw a symbolic spread" },
  { href: "/readings", Icon: FileTextIcon, title: "Readings Archive", hint: "Browse, export or delete past sessions" },
];

function formatAgeGroup(value) {
  if (!value) return null;
  return value.replace("-", "–");
}

function formatDate(value) {
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function fieldErrorsFrom(err) {
  const map = {};
  if (Array.isArray(err?.fields)) {
    for (const f of err.fields) {
      map[f.loc?.[f.loc.length - 1]] = f.msg;
    }
  }
  return map;
}

// Saved confirmation pill shown briefly after each save.
function SavedFlash() {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-700">
      <CheckIcon className="h-3 w-3" />
      Saved
    </span>
  );
}

export default function ProfilePage() {
  const router = useRouter();
  const { user, loading: authLoading, reloadUser } = useAuth();
  const toast = useToast();
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileError, setProfileError] = useState(null);
  const [busy, setBusy] = useState(null);

  const [editingIdentity, setEditingIdentity] = useState(false);
  const [identityForm, setIdentityForm] = useState({ fullName: "", ageGroup: "" });
  const [identityErrors, setIdentityErrors] = useState({});

  const [goalDraft, setGoalDraft] = useState("");
  const [editingGoal, setEditingGoal] = useState(null);
  const [recentReadings, setRecentReadings] = useState([]);
  const [analytics, setAnalytics] = useState(null);

  // Which section currently flashes the "Saved" indicator.
  const [sectionFlash, setSectionFlash] = useState(null);
  const flashTimer = useRef(null);

  const [avatarState, setAvatarState] = useState({ key: null, url: null });
  const fileInputRef = useRef(null);

  function flashSaved(section) {
    if (flashTimer.current) clearTimeout(flashTimer.current);
    setSectionFlash(section);
    flashTimer.current = setTimeout(() => setSectionFlash(null), 2400);
  }

  useEffect(() => () => flashTimer.current && clearTimeout(flashTimer.current), []);

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/login");
    }
  }, [authLoading, user, router]);

  const loadProfileData = useCallback(() => {
    (async () => {
      try {
        setProfile(await fetchProfile());
        setProfileError(null);
      } catch (err) {
        setProfileError(err.message || "We couldn't load your profile.");
      } finally {
        setProfileLoading(false);
      }
    })();
    listReadings({ limit: 5 })
      .then((rData) => setRecentReadings(rData.items || []))
      .catch(() => {
        /* reading history optional on profile load */
      });
    getReadingAnalytics()
      .then((a) => setAnalytics(a))
      .catch(() => {
        /* stats optional */
      });
  }, []);

  useEffect(() => {
    if (authLoading || !user) {
      return;
    }
    loadProfileData();
  }, [authLoading, user, loadProfileData]);

  const avatarKey = profile?.avatar_key ?? null;

  useEffect(() => {
    if (!avatarKey) {
      return undefined;
    }
    let cancelled = false;
    let objectUrl = null;
    fetchAvatarBlobUrl(profile.updated_at)
      .then((url) => {
        if (cancelled) {
          URL.revokeObjectURL(url);
          return;
        }
        objectUrl = url;
        setAvatarState({ key: avatarKey, url });
      })
      .catch(() => setAvatarState({ key: avatarKey, url: null }));
    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [avatarKey, profile?.updated_at]);

  const avatarUrl = avatarKey && avatarState.key === avatarKey ? avatarState.url : null;

  const typeCounts = useMemo(() => {
    const counts = { palm: 0, tarot: 0 };
    for (const row of analytics?.by_type || []) {
      if (row.type in counts) counts[row.type] = row.count;
    }
    return counts;
  }, [analytics]);

  function startEditing() {
    setIdentityForm({
      fullName: user?.full_name ?? "",
      ageGroup: profile?.age_group ?? "",
    });
    setIdentityErrors({});
    setEditingIdentity(true);
  }

  async function saveIdentity(event) {
    event.preventDefault();
    setBusy("identity");
    setIdentityErrors({});
    try {
      const updated = await updateProfile({
        full_name: identityForm.fullName,
        age_group: identityForm.ageGroup || null,
      });
      setProfile(updated);
      setEditingIdentity(false);
      await reloadUser();
      flashSaved("identity");
      toast.success("Profile saved", "Your identity details are up to date.");
    } catch (err) {
      const fieldErrors = fieldErrorsFrom(err);
      if (Object.keys(fieldErrors).length > 0) {
        setIdentityErrors(fieldErrors);
        toast.error("Please fix the highlighted fields.");
      } else {
        toast.error("Saving failed. Please try again.", err.message);
      }
    } finally {
      setBusy(null);
    }
  }

  async function toggleInterest(interest) {
    if (!profile) return;
    const selected = profile.interests.includes(interest);
    if (!selected && profile.interests.length >= MAX_INTERESTS) {
      toast.error(`You can pick up to ${MAX_INTERESTS} interests.`);
      return;
    }
    const next = selected
      ? profile.interests.filter((item) => item !== interest)
      : [...profile.interests, interest];
    setBusy("interests");
    try {
      setProfile(await replaceInterests(next));
      flashSaved("interests");
    } catch (err) {
      toast.error("Couldn't update interests.", err.message);
    } finally {
      setBusy(null);
    }
  }

  async function patchPreference(patch, section = "preferences") {
    setBusy("preferences");
    try {
      setProfile(await updateProfile(patch));
      flashSaved(section);
    } catch (err) {
      toast.error("Couldn't save your preferences.", err.message);
    } finally {
      setBusy(null);
    }
  }

  async function addGoal(event) {
    event.preventDefault();
    const text = goalDraft.trim();
    if (!text) return;
    setBusy("goal-add");
    try {
      setProfile(await createGoal(text));
      setGoalDraft("");
      flashSaved("goals");
    } catch (err) {
      toast.error("Couldn't add that goal.", err.message);
    } finally {
      setBusy(null);
    }
  }

  async function saveGoalEdit(event) {
    event.preventDefault();
    if (!editingGoal) return;
    setBusy(`goal-${editingGoal.id}`);
    try {
      setProfile(await updateGoal(editingGoal.id, editingGoal.text));
      setEditingGoal(null);
      flashSaved("goals");
    } catch (err) {
      toast.error("Couldn't update that goal.", err.message);
    } finally {
      setBusy(null);
    }
  }

  async function removeGoal(goalId) {
    setBusy(`goal-${goalId}`);
    try {
      await deleteGoal(goalId);
      setProfile((prev) =>
        prev ? { ...prev, goals: prev.goals.filter((g) => g.id !== goalId) } : prev
      );
    } catch (err) {
      toast.error("Couldn't remove that goal.", err.message);
    } finally {
      setBusy(null);
    }
  }

  async function handleAvatarChange(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (!AVATAR_ACCEPT.includes(file.type)) {
      toast.error("Avatars must be a JPG, PNG, or WEBP image.");
      return;
    }
    if (file.size > AVATAR_MAX_BYTES) {
      toast.error("Avatars must be 5 MB or smaller.");
      return;
    }
    setBusy("avatar");
    try {
      setProfile(await uploadAvatar(file));
      flashSaved("account");
    } catch (err) {
      toast.error("Couldn't upload that image.", err.message);
    } finally {
      setBusy(null);
    }
  }

  async function handleRemoveAvatar() {
    setBusy("avatar");
    try {
      setProfile(await removeAvatar());
      flashSaved("account");
    } catch (err) {
      toast.error("Couldn't remove your avatar.", err.message);
    } finally {
      setBusy(null);
    }
  }

  if (authLoading || profileLoading) {
    return (
      <div className="animate-fade-in space-y-6" aria-busy="true" aria-live="polite">
        <SkeletonRow lines={2} />
        <SkeletonCards count={3} />
        <SkeletonRow lines={3} />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner label="Redirecting to sign-in…" />
      </div>
    );
  }

  if (profileError || !profile) {
    return (
      <div className="animate-fade-in py-10">
        <ErrorState
          title="Unable to load your profile"
          message={profileError || "The profile could not be retrieved."}
          onRetry={() => {
            setProfileLoading(true);
            loadProfileData();
          }}
        />
      </div>
    );
  }

  const saving = busy !== null;
  const displayName = user.full_name || user.email?.split("@")[0] || "Seeker";
  const meta = roleMeta(user.role);

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        icon={UserIcon}
        tileTone="primary"
        eyebrow={meta.label}
        title={displayName}
        description={`Member since ${formatDate(user.created_at)}. Manage your identity, spiritual interests, goals and reading preferences.`}
        actions={
          <Button
            variant="secondary"
            icon={PencilIcon}
            onClick={() => (editingIdentity ? setEditingIdentity(false) : startEditing())}
          >
            {editingIdentity ? "Close editor" : "Edit profile"}
          </Button>
        }
      />

      {/* Identity section. */}
      <Panel
        title="Identity"
        subtitle="Your public name, contact details and avatar."
        action={(sectionFlash === "identity" || sectionFlash === "account") && <SavedFlash />}
      >
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
          {/* Avatar with camera overlay */}
          <div className="relative shrink-0 self-center sm:self-start">
            <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-full bg-gradient-to-br from-primary-600 to-fuchsia-500 text-3xl font-semibold text-white shadow-lg shadow-primary-500/30 ring-4 ring-white">
              {avatarUrl ? (
                // eslint-disable-next-line @next/next/no-img-element -- blob object URL, not optimizable by next/image
                <img src={avatarUrl} alt={`${displayName} avatar`} className="h-full w-full object-cover" />
              ) : (
                displayName.charAt(0).toUpperCase()
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept={AVATAR_ACCEPT.join(",")}
              className="hidden"
              onChange={handleAvatarChange}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={saving}
              aria-label="Change avatar"
              title="Change avatar"
              className="absolute -right-1 -bottom-1 flex h-9 w-9 cursor-pointer items-center justify-center rounded-full border-2 border-white bg-primary-600 text-white shadow-md transition hover:bg-primary-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {busy === "avatar" ? <Spinner className="h-4 w-4" /> : <CameraIcon className="h-4 w-4" />}
            </button>
          </div>

          {/* Identity details */}
          <div className="min-w-0 flex-1 space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone={meta.badgeTone}>
                {meta.icon && <meta.icon className="h-3 w-3" />}
                {meta.label}
              </Badge>
              {profile.age_group && (
                <Badge tone="primary">Age {formatAgeGroup(profile.age_group)}</Badge>
              )}
              <Badge tone="accent">{profile.tone} tone</Badge>
              <Badge tone={profile.avatar_key ? "emerald" : "slate"}>
                {profile.avatar_key ? "Avatar uploaded" : "No avatar"}
              </Badge>
            </div>
            <p className="break-all text-sm text-slate-600">{user.email}</p>
            <p className="flex items-center gap-1.5 text-xs text-slate-500">
              <CalendarIcon className="h-3.5 w-3.5 shrink-0" />
              Member since {formatDate(user.created_at)}
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              <Button
                variant="secondary"
                size="sm"
                icon={ImageIcon}
                loading={busy === "avatar"}
                disabled={saving}
                onClick={() => fileInputRef.current?.click()}
              >
                Change photo
              </Button>
              {profile.avatar_key && (
                <Button
                  variant="dangerGhost"
                  size="sm"
                  icon={TrashIcon}
                  disabled={saving}
                  onClick={handleRemoveAvatar}
                >
                  Remove photo
                </Button>
              )}
            </div>
            <p className="text-[11px] text-slate-400">
              JPG, PNG or WEBP up to {Math.round(AVATAR_MAX_BYTES / (1024 * 1024))} MB.
            </p>
          </div>
        </div>

        {/* Identity edit form */}
        {editingIdentity && (
          <form
            onSubmit={saveIdentity}
            className="mt-6 grid gap-4 border-t border-slate-100 pt-6 sm:grid-cols-2"
            noValidate
          >
            <div>
              <label htmlFor="fullName" className="mb-1.5 block text-sm font-medium text-slate-700">
                Name
              </label>
              <input
                id="fullName"
                type="text"
                value={identityForm.fullName}
                onChange={(e) =>
                  setIdentityForm((prev) => ({ ...prev, fullName: e.target.value }))
                }
                disabled={saving}
                className={INPUT_CLASS}
              />
              {identityErrors.full_name && (
                <InlineError className="mt-1.5" message={identityErrors.full_name} />
              )}
            </div>
            <div>
              <label htmlFor="ageGroup" className="mb-1.5 block text-sm font-medium text-slate-700">
                Age group
              </label>
              <select
                id="ageGroup"
                value={identityForm.ageGroup}
                onChange={(e) =>
                  setIdentityForm((prev) => ({ ...prev, ageGroup: e.target.value }))
                }
                disabled={saving}
                className={`${INPUT_CLASS} cursor-pointer`}
              >
                <option value="">Prefer not to say</option>
                {AGE_GROUP_OPTIONS.map((group) => (
                  <option key={group} value={group}>
                    {formatAgeGroup(group)}
                  </option>
                ))}
              </select>
              {identityErrors.age_group && (
                <InlineError className="mt-1.5" message={identityErrors.age_group} />
              )}
            </div>
            <div className="flex flex-wrap gap-2 sm:col-span-2">
              <Button type="submit" loading={busy === "identity"} disabled={saving}>
                Save changes
              </Button>
              <Button variant="ghost" disabled={saving} onClick={() => setEditingIdentity(false)}>
                Cancel
              </Button>
            </div>
          </form>
        )}
      </Panel>

      <div className="grid items-start gap-6 lg:grid-cols-3">
        {/* Main column. */}
        <div className="space-y-6 lg:col-span-2">
          {/* Spiritual interests */}
          <Panel
            title="Spiritual Interests"
            subtitle="Tap a topic to add or remove it — this shapes your readings and guidance."
            action={
              <div className="flex items-center gap-2">
                {sectionFlash === "interests" && <SavedFlash />}
                <Badge tone="primary">
                  {profile.interests.length}/{MAX_INTERESTS} chosen
                </Badge>
              </div>
            }
          >
            <div className="flex flex-wrap gap-2">
              {INTEREST_OPTIONS.map((interest) => {
                const selected = profile.interests.includes(interest);
                return (
                  <button
                    key={interest}
                    type="button"
                    aria-pressed={selected}
                    onClick={() => toggleInterest(interest)}
                    disabled={saving}
                    className={`inline-flex cursor-pointer items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-sm font-medium transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:cursor-not-allowed disabled:opacity-60 ${
                      selected
                        ? "border-primary-600 bg-primary-600 text-white shadow-sm shadow-primary-500/30"
                        : "border-slate-200 bg-white text-slate-600 hover:border-primary-200 hover:bg-primary-50 hover:text-primary-700"
                    }`}
                  >
                    {selected && <CheckIcon className="h-3.5 w-3.5" />}
                    {interest}
                  </button>
                );
              })}
            </div>
          </Panel>

          {/* Spiritual goals */}
          <Panel
            title="Spiritual Goals"
            subtitle="Intentions you are actively working through your practice."
            action={sectionFlash === "goals" && <SavedFlash />}
          >
            <ul className="space-y-2.5">
              {profile.goals.length === 0 && (
                <li>
                  <EmptyState
                    icon={SparkleIcon}
                    title="No goals yet"
                    description="Set your first intention below."
                  />
                </li>
              )}
              {profile.goals.map((goal) => (
                <li
                  key={goal.id}
                  className="group flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50/60 px-4 py-3 transition hover:border-primary-200 hover:bg-primary-50/40"
                >
                  {editingGoal?.id === goal.id ? (
                    <form
                      onSubmit={saveGoalEdit}
                      className="flex flex-1 flex-col gap-2 sm:flex-row sm:items-end"
                    >
                      <div className="min-w-0 flex-1">
                        <label
                          htmlFor={`goal-edit-${goal.id}`}
                          className="mb-1.5 block text-xs font-medium text-slate-600"
                        >
                          Edit goal
                        </label>
                        <input
                          id={`goal-edit-${goal.id}`}
                          type="text"
                          value={editingGoal.text}
                          onChange={(e) =>
                            setEditingGoal((prev) => ({ ...prev, text: e.target.value }))
                          }
                          maxLength={500}
                          autoFocus
                          className={INPUT_CLASS}
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button
                          type="submit"
                          variant="secondary"
                          size="sm"
                          loading={busy === `goal-${goal.id}`}
                          disabled={saving}
                        >
                          Save
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={saving}
                          onClick={() => setEditingGoal(null)}
                        >
                          Cancel
                        </Button>
                      </div>
                    </form>
                  ) : (
                    <>
                      <SparkleIcon className="h-4 w-4 shrink-0 text-accent-500" />
                      <span className="min-w-0 flex-1 text-sm text-slate-700">{goal.text}</span>
                      <span className="flex shrink-0 items-center gap-1">
                        <button
                          type="button"
                          onClick={() => setEditingGoal({ id: goal.id, text: goal.text })}
                          disabled={saving}
                          aria-label={`Edit goal: ${goal.text}`}
                          title="Edit"
                          className="cursor-pointer rounded-full p-2 text-slate-400 transition hover:bg-white hover:text-primary-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => removeGoal(goal.id)}
                          disabled={saving}
                          aria-label={`Remove goal: ${goal.text}`}
                          title="Remove"
                          className="cursor-pointer rounded-full p-2 text-slate-400 transition hover:bg-white hover:text-rose-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rose-500 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </span>
                    </>
                  )}
                </li>
              ))}
            </ul>

            <form
              onSubmit={addGoal}
              className="mt-5 flex flex-col gap-2 border-t border-slate-100 pt-5 sm:flex-row sm:items-end"
            >
              <div className="min-w-0 flex-1">
                <label htmlFor="new-goal" className="mb-1.5 block text-xs font-medium text-slate-600">
                  Add a goal
                </label>
                <input
                  id="new-goal"
                  type="text"
                  value={goalDraft}
                  onChange={(e) => setGoalDraft(e.target.value)}
                  placeholder="e.g. Build a daily reflection habit"
                  maxLength={500}
                  className={INPUT_CLASS}
                />
              </div>
              <Button
                type="submit"
                variant="secondary"
                icon={SparkleIcon}
                loading={busy === "goal-add"}
                disabled={saving || !goalDraft.trim()}
              >
                Add goal
              </Button>
            </form>
          </Panel>

          {/* Reading preferences */}
          <Panel
            title="Reading Preferences"
            subtitle="Changes save automatically."
            action={sectionFlash === "preferences" && <SavedFlash />}
          >
            <div className="grid gap-5 sm:grid-cols-2">
              <div>
                <label htmlFor="deck" className="mb-1.5 block text-sm font-medium text-slate-700">
                  Default deck
                </label>
                <select
                  id="deck"
                  value={profile.default_deck}
                  onChange={(e) => patchPreference({ default_deck: e.target.value })}
                  disabled={saving}
                  className={`${INPUT_CLASS} cursor-pointer`}
                >
                  {DECK_OPTIONS.map((deck) => (
                    <option key={deck} value={deck}>
                      {deck}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="spread" className="mb-1.5 block text-sm font-medium text-slate-700">
                  Favorite spread
                </label>
                <select
                  id="spread"
                  value={profile.favorite_spread}
                  onChange={(e) => patchPreference({ favorite_spread: e.target.value })}
                  disabled={saving}
                  className={`${INPUT_CLASS} cursor-pointer`}
                >
                  {SPREAD_OPTIONS.map((spread) => (
                    <option key={spread} value={spread}>
                      {spread}
                    </option>
                  ))}
                </select>
              </div>
              <fieldset className="sm:col-span-2">
                <legend className="mb-2 text-sm font-medium text-slate-700">
                  Interpretation tone
                </legend>
                <div className="grid grid-cols-3 gap-2">
                  {TONE_OPTIONS.map((tone) => {
                    const active = profile.tone === tone;
                    return (
                      <button
                        key={tone}
                        type="button"
                        onClick={() => patchPreference({ tone })}
                        disabled={saving}
                        aria-pressed={active}
                        className={`cursor-pointer rounded-2xl border px-3 py-2.5 text-sm font-medium capitalize transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:cursor-not-allowed disabled:opacity-60 ${
                          active
                            ? "border-accent-400 bg-accent-50 text-accent-800 shadow-xs"
                            : "border-slate-200 bg-white text-slate-600 hover:border-accent-200 hover:bg-accent-50/50"
                        }`}
                      >
                        {tone}
                      </button>
                    );
                  })}
                </div>
              </fieldset>
              <fieldset className="sm:col-span-2">
                <legend className="mb-2 text-sm font-medium text-slate-700">Notifications</legend>
                <div className="grid gap-2 sm:grid-cols-3">
                  {[
                    ["Daily guidance", "notify_daily_guidance"],
                    ["Reading reminders", "notify_reminders"],
                    ["SMS alerts", "notify_sms"],
                  ].map(([label, key]) => (
                    <label
                      key={key}
                      className={`flex cursor-pointer items-center justify-between gap-2 rounded-2xl border px-3.5 py-2.5 text-sm transition ${
                        profile[key]
                          ? "border-primary-200 bg-primary-50 text-primary-800"
                          : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      <span className="font-medium">{label}</span>
                      <input
                        type="checkbox"
                        checked={profile[key]}
                        onChange={(e) => patchPreference({ [key]: e.target.checked })}
                        disabled={saving}
                        className="h-4 w-4 cursor-pointer rounded border-slate-300 text-primary-600 focus:ring-primary-400"
                      />
                    </label>
                  ))}
                </div>
              </fieldset>
            </div>
          </Panel>

          {/* Session history */}
          <Panel
            title="Recent Sessions"
            subtitle="Your latest readings across palm and tarot."
            action={
              <Button href="/readings" variant="ghost" size="sm" iconRight={ArrowRightIcon}>
                View all archives
              </Button>
            }
          >
            <ul className="divide-y divide-slate-100">
              {recentReadings.length === 0 && (
                <li>
                  <EmptyState
                    icon={CalendarIcon}
                    title="No readings yet"
                    description="Your first session will appear here."
                  />
                </li>
              )}
              {recentReadings.map((r) => {
                const isPalm = r.type === "palm";
                return (
                  <li key={r.id}>
                    <Link
                      href={`/readings/${r.id}`}
                      className="group flex items-center gap-4 rounded-2xl px-2 py-3 transition hover:bg-primary-50/50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                    >
                      <span
                        className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border ${
                          isPalm
                            ? "border-accent-200 bg-accent-50 text-accent-600"
                            : "border-primary-200 bg-primary-50 text-primary-600"
                        }`}
                        aria-hidden="true"
                      >
                        {isPalm ? <HandIcon className="h-5 w-5" /> : <CardsIcon className="h-5 w-5" />}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-medium text-slate-800 group-hover:text-primary-700">
                          {r.title}
                        </span>
                        <span className="block text-xs text-slate-500">
                          {new Date(r.created_at).toLocaleDateString(undefined, {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}{" "}
                          · <span className="capitalize">{r.type}</span>
                        </span>
                      </span>
                      <Badge tone="emerald">{r.status}</Badge>
                      <ArrowRightIcon className="h-4 w-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-primary-500" />
                    </Link>
                  </li>
                );
              })}
            </ul>
          </Panel>
        </div>

        {/* Sidebar. */}
        <aside className="space-y-6 lg:sticky lg:top-24">
          {/* Journey stats */}
          <Panel title="Your Journey" subtitle="A snapshot of your reading practice.">
            <div className="grid grid-cols-3 gap-3 text-center">
              {[
                { label: "Total", value: analytics?.total ?? recentReadings.length, tint: "text-primary-700" },
                { label: "Palm", value: typeCounts.palm, tint: "text-accent-700" },
                { label: "Tarot", value: typeCounts.tarot, tint: "text-indigo-700" },
              ].map((stat) => (
                <div key={stat.label} className="rounded-2xl border border-slate-200 bg-slate-50/70 p-3">
                  <div className={`font-display text-2xl font-bold ${stat.tint}`}>
                    {analytics ? stat.value : "·"}
                  </div>
                  <div className="mt-0.5 text-[11px] font-medium uppercase tracking-wider text-slate-500">
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 rounded-2xl border border-primary-100 bg-primary-50/60 p-4">
              <p className="text-xs leading-relaxed text-primary-900/80">
                <span className="font-semibold">Favorite spread:</span>{" "}
                {profile.favorite_spread || "None yet"} — open the Tarot Sanctuary to draw it.
              </p>
              <Button
                href="/readings/tarot"
                variant="ghost"
                size="sm"
                className="mt-2"
                iconRight={ArrowRightIcon}
              >
                Draw a spread
              </Button>
            </div>
          </Panel>

          {/* Quick actions */}
          <Panel title="Quick actions" subtitle="Jump straight into your next ritual.">
            <div className="space-y-1.5">
              {QUICK_ACTIONS.map(({ href, Icon, title, hint }) => (
                <Link
                  key={href}
                  href={href}
                  className="group flex items-center gap-3 rounded-2xl p-2.5 transition hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                >
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-primary-100 bg-primary-50 text-primary-600">
                    <Icon className="h-5 w-5" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-semibold text-slate-800 group-hover:text-primary-700">
                      {title}
                    </span>
                    <span className="block truncate text-xs text-slate-500">{hint}</span>
                  </span>
                  <ArrowRightIcon className="h-4 w-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-primary-500" />
                </Link>
              ))}
            </div>
          </Panel>
        </aside>
      </div>
    </div>
  );
}
