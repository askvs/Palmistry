// Consultant detail + booking page.
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import {
  Button,
  EmptyState,
  ErrorState,
  InlineError,
  Panel,
  SkeletonRow,
  useToast,
} from "@/components/ui";
import { Badge } from "@/components/ui";
import {
  CalendarIcon,
  CheckCircleIcon,
  ClockIcon,
  StarIcon,
  VideoIcon,
} from "@/components/icons";
import { ConsultantAvatar, EmptyRow, SlotPicker } from "@/components/booking/shared";
import TimeProposalForm from "@/components/booking/TimeProposalForm";
import Seo from "@/components/Seo";
import { useAsyncData } from "@/hooks/useAsyncData";
import {
  createBooking,
  fetchConsultant,
  fetchConsultantAvailability,
  fetchConsultantDaySlots,
  fetchConsultantReviews,
  proposeBooking,
} from "@/services/booking";
import {
  addDays,
  decorateAvailabilityDays,
  formatDateTime,
  formatDuration,
  todayKey,
  weekdayShort,
} from "@/lib/datetime";
import Link from "next/link";

const CALENDAR_WINDOW_DAYS = 21;

export default function ConsultantDetailPage() {
  const router = useRouter();
  const toast = useToast();
  const consultantId = router.query.consultantId;

  const fromKey = useMemo(() => todayKey(), []);
  const toKey = useMemo(() => addDays(todayKey(), CALENDAR_WINDOW_DAYS - 1), []);

  const {
    data: consultantData,
    error: consultantError,
    loading: consultantLoading,
  } = useAsyncData(
    useCallback(() => (consultantId ? fetchConsultant(consultantId) : Promise.resolve(null)), [consultantId]),
    { enabled: Boolean(consultantId) },
  );

  const {
    data: availabilityData,
    error: availabilityError,
    loading: availabilityLoading,
    refresh: refreshAvailability,
  } = useAsyncData(
    useCallback(
      () =>
        consultantId
          ? fetchConsultantAvailability(consultantId, { from: fromKey, to: toKey })
          : Promise.resolve(null),
      [consultantId, fromKey, toKey],
    ),
    { enabled: Boolean(consultantId) },
  );

  const days = useMemo(
    () => decorateAvailabilityDays(availabilityData?.days || []),
    [availabilityData],
  );

  // Derived, not synced: the first day that actually has open slots becomes the
  // selection unless the seeker already picked another one.
  const firstOpenDay = useMemo(
    () => days.find((day) => day.available_slots > 0)?.date ?? null,
    [days],
  );

  const [pickedDate, setPickedDate] = useState(null);
  const [pickedSlot, setPickedSlot] = useState(null);
  const [subject, setSubject] = useState("");
  const [notes, setNotes] = useState("");
  // Pasted by the seeker for this particular request only — no default value.
  const [meetingLink, setMeetingLink] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const selectedDate = pickedDate ?? firstOpenDay;

  const {
    data: daySlotsData,
    loading: slotsLoading,
    refresh: refreshSlots,
  } = useAsyncData(
    useCallback(
      () =>
        consultantId && selectedDate
          ? fetchConsultantDaySlots(consultantId, selectedDate)
          : Promise.resolve(null),
      [consultantId, selectedDate],
    ),
    { enabled: Boolean(consultantId && selectedDate) },
  );

  const daySlots = useMemo(() => daySlotsData?.slots || [], [daySlotsData]);

  // A slot can disappear between render and submit (someone else books it), so
  // the effective selection is derived rather than cleared from an effect.
  const selectedSlot =
    pickedSlot && daySlots.some((slot) => slot.id === pickedSlot.id)
      ? pickedSlot
      : null;

  const reviewsLoader = useCallback(
    () =>
      consultantId ? fetchConsultantReviews(consultantId, { limit: 5 }) : Promise.resolve({ items: [] }),
    [consultantId],
  );
  const { data: reviewsData } = useAsyncData(reviewsLoader, {
    enabled: Boolean(consultantId),
  });

  if (consultantLoading) {
    return (
      <div className="animate-fade-in space-y-6">
        <Seo title="Consultant profile" description="See availability, reviews and book a live palm or tarot session." />
        <SkeletonRow lines={4} />
        <SkeletonRow lines={6} />
      </div>
    );
  }

  if (consultantError || !consultantData) {
    return (
      <div className="animate-fade-in space-y-6">
        <Seo title="Consultant profile" description="See availability, reviews and book a live palm or tarot session." />
        <ErrorState
          title="Consultant not found"
          message={consultantError?.message || "This consultant profile is no longer available."}
          onRetry={() => router.reload()}
        />
        <Button href="/consultants" variant="secondary">
          Back to the directory
        </Button>
      </div>
    );
  }

  async function submitBooking(event) {
    event.preventDefault();
    if (!selectedSlot || busy) return;
    if (subject.trim().length < 3) {
      setError("Give your session a short focus (at least 3 characters).");
      return;
    }
    const pastedLink = meetingLink.trim();
    if (pastedLink) {
      try {
        void new URL(pastedLink);
      } catch {
        setError("That meeting link doesn't look valid. Paste the full URL or leave it empty.");
        return;
      }
    }
    setBusy(true);
    setError(null);
    try {
      const booking = await createBooking(consultantId, {
        slotId: selectedSlot.id,
        subject: subject.trim(),
        notes: notes.trim() || undefined,
        meetingLink: pastedLink || undefined,
      });
      toast.success(
        "Request sent",
        `${consultantData.full_name} will confirm your session shortly.`,
      );
      router.push(`/sessions?booked=${booking.id}`);
    } catch (err) {
      setError(err?.message || "Could not book this session");
      refreshSlots();
    } finally {
      setBusy(false);
    }
  }

  const profile = consultantData;

  async function handlePropose({ startTime, durationMinutes, subject: subj, notes: note, meetingLink: link }) {
    const booking = await proposeBooking(consultantId, {
      startTime,
      durationMinutes,
      subject: subj,
      notes: note,
      meetingLink: link?.trim() || undefined,
    });
    toast.success(
      "Time proposed",
      `${consultantData.full_name} will confirm or suggest another time.`,
    );
    router.push(`/sessions?booked=${booking.id}`);
  }

  return (
    <div className="animate-fade-in space-y-8">
      <Seo title="Consultant profile" description="See availability, reviews and book a live palm or tarot session." />

      {/* Nocturne header band */}
      <header className="rounded-[20px] bg-gradient-to-br from-[#1e1836] to-[#241b3f] p-6 sm:p-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 items-start gap-4">
            <ConsultantAvatar
              name={profile.full_name || "Consultant"}
              className="h-14 w-14 text-lg ring-1 ring-white/15"
            />
            <div className="min-w-0">
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#a79fc6]">
                Consultant profile
              </p>
              <h1 className="mt-1.5 font-display text-2xl font-semibold tracking-[-0.02em] text-[#ede9fe] sm:text-3xl">
                {profile.full_name || "Consultant"}
              </h1>
              {profile.headline && (
                <p className="mt-1.5 text-sm leading-relaxed text-[#c4b5fd]">
                  {profile.headline}
                </p>
              )}
              <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1.5">
                {profile.avg_rating != null && (
                  <span className="flex items-center gap-1.5">
                    <StarIcon className="h-4 w-4 text-[#e9b44c]" />
                    <span className="text-sm font-semibold tabular-nums text-[#e9b44c]">
                      {Number(profile.avg_rating).toFixed(1)}
                    </span>
                    {(profile.review_count || 0) > 0 && (
                      <span className="text-xs text-[#a79fc6]">({profile.review_count})</span>
                    )}
                  </span>
                )}
                {(profile.specializations || []).length > 0 && (
                  <span className="flex flex-wrap gap-1.5">
                    {profile.specializations.map((tag) => (
                      <span
                        key={tag}
                        className="rounded-full bg-white/[0.06] px-2.5 py-[3px] text-xs font-semibold text-[#c4b5fd]"
                      >
                        {tag}
                      </span>
                    ))}
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            <Button href="/consultants" variant="secondary" icon={CalendarIcon}>
              All consultants
            </Button>
          </div>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Profile column */}
        <div className="space-y-6 lg:col-span-2">
          <Panel title="About" subtitle={`${profile.years_experience}+ years of practice`}>
            <p className="text-sm leading-relaxed text-slate-600">
              {profile.bio || "This consultant has not written a bio yet."}
            </p>

            {(profile.specializations || []).length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  Specialisations
                </p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {profile.specializations.map((tag) => (
                    <Badge key={tag} tone="primary">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {(profile.modalities || []).length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  Modalities
                </p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {profile.modalities.map((tag) => (
                    <Badge key={tag} tone="accent">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {(profile.languages || []).length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  Languages
                </p>
                <div className="mt-2 text-sm text-slate-600">
                  {profile.languages.join(", ")}
                </div>
              </div>
            )}
          </Panel>

          <Panel title="Session details">
            <dl className="space-y-2.5 text-sm">
              <div className="flex items-center justify-between gap-3">
                <dt className="text-slate-500">Rate</dt>
                <dd className="font-bold text-slate-900">
                  {profile.currency} {profile.session_rate}
                </dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-slate-500">Duration</dt>
                <dd className="font-semibold text-slate-800">
                  {formatDuration(profile.session_duration_minutes)}
                </dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-slate-500">Sessions held</dt>
                <dd className="font-semibold text-slate-800">{profile.total_sessions}</dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-slate-500">Rating</dt>
                <dd className="flex items-center gap-1.5 font-semibold text-slate-800">
                  {profile.avg_rating != null ? (
                    <>
                      <StarIcon className="h-4 w-4 text-accent-500" />
                      {Number(profile.avg_rating).toFixed(1)}
                      <span className="text-xs text-slate-500">({profile.review_count})</span>
                    </>
                  ) : (
                    <span className="text-xs text-slate-500">No reviews yet</span>
                  )}
                </dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-slate-500">Time zone</dt>
                <dd className="font-semibold text-slate-800">{profile.timezone}</dd>
              </div>
            </dl>
          </Panel>

          <Panel title="Reviews" subtitle="From seekers who completed a session">
            {!reviewsData || reviewsData.items.length === 0 ? (
              <EmptyRow>No reviews yet. Be the first to book.</EmptyRow>
            ) : (
              <ul>
                {reviewsData.items.map((review) => (
                  <li
                    key={review.id}
                    className="border-b border-slate-100 py-3.5 first:pt-0 last:border-0 last:pb-0"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-[13.5px] font-semibold text-slate-700">
                        {review.author_name || "Seeker"}
                      </p>
                      <span className="flex items-center gap-0.5">
                        {[1, 2, 3, 4, 5].map((n) => (
                          <StarIcon
                            key={n}
                            className={`h-3.5 w-3.5 ${
                              n <= review.rating ? "text-accent-500" : "text-slate-300"
                            }`}
                          />
                        ))}
                      </span>
                    </div>
                    {review.review && (
                      <p className="mt-1.5 text-sm leading-relaxed text-slate-600">
                        {review.review}
                      </p>
                    )}
                    <p className="mt-1.5 text-xs tabular-nums text-slate-500">
                      {review.booking_subject} · {formatDateTime(review.created_at)}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </Panel>
        </div>

        {/* Booking column */}
        <div className="lg:col-span-3 lg:sticky lg:top-24 lg:self-start">
          <Panel
            title="Book a session"
            subtitle="Pick a date and time that works for you"
          >
            {!profile.is_accepting_bookings ? (
              <EmptyState
                icon={ClockIcon}
                title="Not accepting bookings right now"
                description="This consultant has paused new bookings. Check back soon."
              />
            ) : availabilityError ? (
              <ErrorState message={availabilityError.message} onRetry={refreshAvailability} />
            ) : availabilityLoading ? (
              <SkeletonRow lines={5} />
            ) : days.length === 0 ? (
              <EmptyState
                icon={CalendarIcon}
                title="No availability published"
                description="This consultant has not published any open slots yet."
              />
            ) : (
              <form onSubmit={submitBooking} className="space-y-5">
                <SlotPicker
                  days={days}
                  daySlots={daySlots}
                  selectedDate={selectedDate}
                  selectedSlotId={selectedSlot?.id}
                  busy={slotsLoading}
                  onSelectDate={(date) => {
                    setPickedDate(date);
                    setPickedSlot(null);
                  }}
                  onSelectSlot={setPickedSlot}
                />

                {selectedSlot && (
                  <div className="rounded-2xl border border-primary-200 bg-primary-50/70 px-4 py-3">
                    <p className="text-xs font-bold uppercase tracking-wide text-primary-700">
                      Selected slot
                    </p>
                    <p className="mt-1 text-sm font-semibold tabular-nums text-primary-900">
                      {selectedDate &&
                        `${selectedDate.slice(8, 10)}/${selectedDate.slice(5, 7)} · `}
                      {formatDateTime(selectedSlot.start_time)} —{" "}
                      {formatDuration(profile.session_duration_minutes)}
                    </p>
                    <p className="mt-1 text-xs text-primary-800">
                      Times are shown in your local timezone ({profile.timezone} consultant time).
                    </p>
                  </div>
                )}

                <div className="space-y-3">
                  <div>
                    <label
                      htmlFor="booking-subject"
                      className="text-xs font-bold uppercase tracking-wide text-slate-500"
                    >
                      What would you like to focus on?
                    </label>
                    <input
                      id="booking-subject"
                      type="text"
                      value={subject}
                      onChange={(event) => setSubject(event.target.value)}
                      placeholder="e.g. Career clarity, relationship guidance"
                      maxLength={200}
                      required
                      className="mt-1.5 w-full rounded-[10px] border border-[#e1dcf0] bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-500 transition focus:border-[#8b5cf6] focus:ring-[3px] focus:ring-primary-600/25 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="booking-notes"
                      className="text-xs font-bold uppercase tracking-wide text-slate-500"
                    >
                      Anything to share in advance? <span className="font-normal">(optional)</span>
                    </label>
                    <textarea
                      id="booking-notes"
                      value={notes}
                      onChange={(event) => setNotes(event.target.value)}
                      rows={4}
                      maxLength={2000}
                      placeholder="Share context, dates, or the question you would like guidance on…"
                      className="mt-1.5 w-full rounded-[10px] border border-[#e1dcf0] bg-white px-4 py-2.5 text-sm leading-normal text-slate-900 placeholder:text-slate-500 transition focus:border-[#8b5cf6] focus:ring-[3px] focus:ring-primary-600/25 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="booking-meeting-link"
                      className="text-xs font-bold uppercase tracking-wide text-slate-500"
                    >
                      Meeting link <span className="font-normal">(optional, for this request only)</span>
                    </label>
                    <input
                      id="booking-meeting-link"
                      type="url"
                      inputMode="url"
                      value={meetingLink}
                      onChange={(event) => setMeetingLink(event.target.value)}
                      placeholder="Paste the meeting link for this session…"
                      maxLength={500}
                      className="mt-1.5 w-full rounded-[10px] border border-[#e1dcf0] bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-500 transition focus:border-[#8b5cf6] focus:ring-[3px] focus:ring-primary-600/25 focus:outline-none"
                    />
                  </div>
                </div>

                {error && <InlineError message={error} />}

                <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
                  <p className="text-sm text-slate-600">
                    Total:{" "}
                    <span className="font-bold tabular-nums text-slate-900">
                      {profile.currency} {profile.session_rate}
                    </span>{" "}
                    · {formatDuration(profile.session_duration_minutes)}
                  </p>
                  <Button
                    type="submit"
                    icon={CheckCircleIcon}
                    loading={busy}
                    disabled={busy || !selectedSlot}
                  >
                    Book session
                  </Button>
                </div>

                <p className="text-xs text-slate-500">
                  Requests stay pending until the consultant accepts. Once confirmed, the Google
                  Meet link shows on your{" "}
                  <Link href="/sessions" className="text-primary-600 hover:underline">
                    sessions
                  </Link>{" "}
                  page.
                </p>
              </form>
            )}
          </Panel>

          {profile.is_accepting_bookings && (
            <section className="surface-card mt-6">
              <div className="border-b border-slate-100 px-5 pb-4 pt-4.5 sm:px-6 sm:pt-5">
                <h2 className="text-[15px] font-semibold tracking-tight text-slate-900">
                  Or propose your own time
                </h2>
                <p className="mt-0.5 text-xs text-slate-500">
                  Suggest a time that suits you — the consultant can accept it or counter with
                  another.
                </p>
              </div>
              <div className="p-5 sm:p-6">
                <TimeProposalForm
                  mode="propose"
                  defaultDurationMinutes={profile.session_duration_minutes}
                  submitLabel="Send time request"
                  onSubmit={handlePropose}
                />
                <p className="mt-3 text-xs text-slate-500">
                  Proposed-time requests stay pending until the consultant accepts. You can
                  keep negotiating the time and chat with them from your{" "}
                  <Link href="/sessions" className="text-primary-600 hover:underline">
                    sessions
                  </Link>{" "}
                  page.
                </p>
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
