// Consultant detail + booking page.
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import {
  Button,
  EmptyState,
  ErrorState,
  InlineError,
  Panel,
  PageHeader,
  SkeletonRow,
  useToast,
} from "@/components/ui";
import { Badge } from "@/components/ui";
import {
  CalendarIcon,
  CheckCircleIcon,
  ClockIcon,
  CompassIcon,
  StarIcon,
  VideoIcon,
} from "@/components/icons";
import { EmptyRow, SlotPicker } from "@/components/booking/shared";
import TimeProposalForm from "@/components/booking/TimeProposalForm";
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
        <SkeletonRow lines={4} />
        <SkeletonRow lines={6} />
      </div>
    );
  }

  if (consultantError || !consultantData) {
    return (
      <div className="animate-fade-in space-y-6">
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
      <PageHeader
        icon={CompassIcon}
        tileTone="emerald"
        eyebrow="Consultant profile"
        title={profile.full_name || "Consultant"}
        description={profile.headline}
        gradient="gold"
        actions={
          <Button href="/consultants" variant="secondary" icon={CalendarIcon}>
            All consultants
          </Button>
        }
      />

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
              <ul className="space-y-3">
                {reviewsData.items.map((review) => (
                  <li
                    key={review.id}
                    className="rounded-2xl border border-slate-200 bg-slate-50/60 p-3.5"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-xs font-semibold text-slate-700">
                        {review.author_name || "Seeker"}
                      </p>
                      <span className="flex items-center gap-0.5 text-accent-500">
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
                      <p className="mt-1.5 text-xs leading-relaxed text-slate-600">
                        {review.review}
                      </p>
                    )}
                    <p className="mt-1.5 text-[11px] text-slate-500">
                      {review.booking_subject} · {formatDateTime(review.created_at)}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </Panel>
        </div>

        {/* Booking column */}
        <div className="lg:col-span-3">
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
                    <p className="mt-1 text-sm font-semibold text-primary-900">
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
                      className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-500 shadow-xs transition focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
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
                      className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-500 shadow-xs transition focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
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
                      className="mt-1.5 w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-500 shadow-xs transition focus:ring-2 focus:ring-primary-500/20 focus:outline-none"
                    />
                  </div>
                </div>

                {error && <InlineError message={error} />}

                <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
                  <p className="text-sm text-slate-600">
                    Total:{" "}
                    <span className="font-bold text-slate-900">
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
                    Request this session
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
            <Panel
              title="Or propose your own time"
              subtitle="Suggest a time that suits you — the consultant can accept it or counter with another."
              className="mt-6"
            >
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
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}
