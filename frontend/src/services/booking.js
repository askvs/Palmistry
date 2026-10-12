// Live consultation and booking API client.
import { api } from "./api";

const BASE = "/api/v1";

// Consultant directory.
export async function fetchConsultants(params = {}) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== "" && value != null),
  ).toString();
  return api.get(`${BASE}/consultants${qs ? `?${qs}` : ""}`);
}

export async function fetchConsultant(consultantId) {
  return api.get(`${BASE}/consultants/${consultantId}`);
}

export async function fetchConsultantReviews(consultantId, params = {}) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== "" && value != null),
  ).toString();
  return api.get(`${BASE}/consultants/${consultantId}/reviews${qs ? `?${qs}` : ""}`);
}

// Day to open-slot counts for the booking calendar.
export async function fetchConsultantAvailability(consultantId, { from, to } = {}) {
  const qs = new URLSearchParams(
    Object.entries({ from, to }).filter(([, value]) => value != null && value !== ""),
  ).toString();
  return api.get(`${BASE}/consultants/${consultantId}/availability${qs ? `?${qs}` : ""}`);
}

// Open slots for one calendar day.
export async function fetchConsultantDaySlots(consultantId, date) {
  const qs = new URLSearchParams({ date }).toString();
  return api.get(`${BASE}/consultants/${consultantId}/slots?${qs}`);
}

export async function createBooking(consultantId, { slotId, subject, notes, meetingLink }) {
  return api.post(`${BASE}/consultants/${consultantId}/bookings`, {
    slot_id: slotId,
    subject,
    notes,
    meeting_link: meetingLink?.trim() || undefined,
  });
}

// Request a session at a seeker-proposed time.
export async function proposeBooking(
  consultantId,
  { startTime, durationMinutes, subject, notes, meetingLink },
) {
  return api.post(`${BASE}/consultants/${consultantId}/bookings/propose`, {
    start_time: startTime,
    duration_minutes: durationMinutes ?? null,
    subject,
    notes,
    meeting_link: meetingLink?.trim() || undefined,
  });
}

// Seeker session hub.
export async function fetchMyBookings(params = {}) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== "" && value != null),
  ).toString();
  return api.get(`${BASE}/bookings${qs ? `?${qs}` : ""}`);
}

export async function fetchBooking(bookingId) {
  return api.get(`${BASE}/bookings/${bookingId}`);
}

export async function cancelBooking(bookingId, reason) {
  return api.post(`${BASE}/bookings/${bookingId}/cancel`, { reason });
}

// Seeker-proposed new time; booking awaits the consultant.
export async function counterBookingAsSeeker(bookingId, { startTime, durationMinutes, message }) {
  return api.post(`${BASE}/bookings/${bookingId}/counter`, {
    start_time: startTime,
    duration_minutes: durationMinutes ?? null,
    message: message ?? null,
  });
}

// Seeker confirms the consultant-proposed time.
export async function confirmBooking(bookingId) {
  return api.post(`${BASE}/bookings/${bookingId}/confirm`);
}

// Per-booking chat for either side.
export async function fetchBookingMessages(bookingId, params = {}) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== "" && value != null),
  ).toString();
  return api.get(`${BASE}/bookings/${bookingId}/messages${qs ? `?${qs}` : ""}`);
}

export async function sendBookingMessage(bookingId, body) {
  return api.post(`${BASE}/bookings/${bookingId}/messages`, { body });
}

export async function submitFeedback(bookingId, { rating, review, isPublic = true }) {
  return api.post(`${BASE}/bookings/${bookingId}/feedback`, {
    rating,
    review,
    is_public: isPublic,
  });
}

export async function fetchBookingNotes(bookingId) {
  return api.get(`${BASE}/bookings/${bookingId}/notes`);
}

// Consultant studio.
export async function fetchMyConsultantProfile() {
  return api.get(`${BASE}/consultants/me/profile`);
}

export async function upsertMyConsultantProfile(payload) {
  return api.put(`${BASE}/consultants/me/profile`, payload);
}

export async function patchMyConsultantProfile(payload) {
  return api.patch(`${BASE}/consultants/me/profile`, payload);
}

export async function toggleAcceptingBookings(isAcceptingBookings) {
  const qs = new URLSearchParams({ is_accepting_bookings: isAcceptingBookings }).toString();
  return api.post(`${BASE}/consultants/me/profile/availability-toggle?${qs}`);
}

export async function fetchConsultantStats() {
  return api.get(`${BASE}/consultants/me/stats`);
}

// Availability rules.
export async function fetchAvailabilityRules() {
  return api.get(`${BASE}/consultants/me/availability/rules`);
}

export async function createAvailabilityRule(payload) {
  return api.post(`${BASE}/consultants/me/availability/rules`, payload);
}

export async function updateAvailabilityRule(ruleId, payload) {
  return api.patch(`${BASE}/consultants/me/availability/rules/${ruleId}`, payload);
}

export async function deleteAvailabilityRule(ruleId) {
  return api.delete(`${BASE}/consultants/me/availability/rules/${ruleId}`);
}

export async function generateSlots({ fromDate, toDate }) {
  return api.post(`${BASE}/consultants/me/availability/generate`, {
    from_date: fromDate,
    to_date: toDate,
  });
}

// Slots.
export async function fetchMySlots(params = {}) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== "" && value != null),
  ).toString();
  return api.get(`${BASE}/consultants/me/availability/slots${qs ? `?${qs}` : ""}`);
}

export async function blockSlot(slotId) {
  return api.post(`${BASE}/consultants/me/availability/slots/${slotId}/block`);
}

export async function unblockSlot(slotId) {
  return api.post(`${BASE}/consultants/me/availability/slots/${slotId}/unblock`);
}

export async function deleteSlot(slotId) {
  return api.delete(`${BASE}/consultants/me/availability/slots/${slotId}`);
}

// Consultant bookings.
export async function fetchConsultantBookings(params = {}) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== "" && value != null),
  ).toString();
  return api.get(`${BASE}/consultants/me/bookings${qs ? `?${qs}` : ""}`);
}

export async function fetchConsultantBooking(bookingId) {
  return api.get(`${BASE}/consultants/me/bookings/${bookingId}`);
}

export async function acceptBooking(bookingId) {
  return api.post(`${BASE}/consultants/me/bookings/${bookingId}/accept`);
}

export async function rejectBooking(bookingId, reason) {
  return api.post(`${BASE}/consultants/me/bookings/${bookingId}/reject`, { reason });
}

// Consultant-proposed new time; booking awaits the seeker.
export async function counterBookingAsConsultant(bookingId, { startTime, durationMinutes, message }) {
  return api.post(`${BASE}/consultants/me/bookings/${bookingId}/counter`, {
    start_time: startTime,
    duration_minutes: durationMinutes ?? null,
    message: message ?? null,
  });
}

export async function completeBooking(bookingId, { force = false } = {}) {
  const qs = new URLSearchParams({ force }).toString();
  return api.post(`${BASE}/consultants/me/bookings/${bookingId}/complete?${qs}`);
}

export async function cancelConsultantBooking(bookingId, reason) {
  return api.post(`${BASE}/consultants/me/bookings/${bookingId}/cancel`, { reason });
}

// Session notes.
export async function addSessionNote(bookingId, { body, visibility = "private" }) {
  return api.post(`${BASE}/consultants/me/bookings/${bookingId}/notes`, {
    body,
    visibility,
  });
}

export async function updateSessionNote(noteId, payload) {
  return api.patch(`${BASE}/consultants/me/notes/${noteId}`, payload);
}

export async function deleteSessionNote(noteId) {
  return api.delete(`${BASE}/consultants/me/notes/${noteId}`);
}

// Google Calendar connection.
export async function fetchCalendarStatus() {
  return api.get(`${BASE}/consultants/me/google-calendar`);
}

// Returns auth URL; the frontend navigates there.
export async function requestCalendarAuthorization() {
  return api.post(`${BASE}/consultants/me/google-calendar/authorize`);
}

export async function connectCalendar(code) {
  return api.post(`${BASE}/consultants/me/google-calendar/connect`, { code });
}

export async function updateCalendarConnection(payload) {
  return api.patch(`${BASE}/consultants/me/google-calendar`, payload);
}

export async function disconnectCalendar() {
  return api.delete(`${BASE}/consultants/me/google-calendar`);
}

export async function retryCalendarSync(bookingId) {
  return api.post(`${BASE}/consultants/me/bookings/${bookingId}/calendar/retry`);
}

// Combined loaders with stable references for useAsyncData.
// Seeker dashboard: upcoming plus recent past sessions.
export async function fetchSeekerSessions({ upcomingLimit = 4, pastLimit = 4 } = {}) {
  const [upcoming, past] = await Promise.all([
    fetchMyBookings({ scope: "upcoming", limit: upcomingLimit }),
    fetchMyBookings({ scope: "past", limit: pastLimit }),
  ]);
  return { upcoming, past };
}

// Consultant studio header: profile plus counters.
export async function fetchConsultantStudioOverview() {
  const [profile, stats] = await Promise.all([
    fetchMyConsultantProfile(),
    fetchConsultantStats(),
  ]);
  return { profile, stats };
}

// Consultant session board split by lifecycle stage.
export async function fetchConsultantSessions({ limit = 50 } = {}) {
  const [requests, awaitingSeeker, upcoming, past] = await Promise.all([
    fetchConsultantBookings({ status: "pending", scope: "all", limit }),
    fetchConsultantBookings({ status: "countered", scope: "all", limit }),
    fetchConsultantBookings({ status: "accepted", scope: "upcoming", limit }),
    fetchConsultantBookings({ scope: "past", limit }),
  ]);
  // Pending and countered both belong in the requests queue.
  const requestItems = [
    ...(requests?.items || []),
    ...(awaitingSeeker?.items || []),
  ];
  return {
    requests: { items: requestItems, total: requestItems.length },
    upcoming,
    past,
  };
}
