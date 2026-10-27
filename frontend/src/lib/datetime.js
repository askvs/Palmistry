// Date helpers for the booking module.
const MINUTE = 60 * 1000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

// Today as YYYY-MM-DD.
export function todayKey(now = new Date()) {
  return toDateKey(now);
}

// Local date as YYYY-MM-DD.
export function toDateKey(value) {
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  const month = `${d.getMonth() + 1}`.padStart(2, "0");
  const day = `${d.getDate()}`.padStart(2, "0");
  return `${d.getFullYear()}-${month}-${day}`;
}

// Add calendar days to a date key.
export function addDays(key, days) {
  const d = new Date(`${key}T00:00:00`);
  d.setDate(d.getDate() + days);
  return toDateKey(d);
}

// Whole days between two date keys.
export function daysBetween(fromKey, toKey) {
  const a = new Date(`${fromKey}T00:00:00`).getTime();
  const b = new Date(`${toKey}T00:00:00`).getTime();
  return Math.round((b - a) / DAY);
}

// Inclusive date-key list.
export function dateRange(fromKey, toKey) {
  const keys = [];
  let cursor = fromKey;
  let guard = 0;
  while (cursor <= toKey && guard < 400) {
    keys.push(cursor);
    cursor = addDays(cursor, 1);
    guard += 1;
  }
  return keys;
}

// Next count days from a key.
export function upcomingDays(count, fromKey = todayKey()) {
  return dateRange(fromKey, addDays(fromKey, count - 1));
}

// Short weekday label.
export function weekdayShort(key, locale = undefined) {
  const d = new Date(`${key}T00:00:00`);
  return d.toLocaleDateString(locale, { weekday: "short" });
}

// Day of month.
export function dayOfMonth(key) {
  const d = new Date(`${key}T00:00:00`);
  return d.getDate();
}

// Compact day heading.
export function dayLabel(key, locale = undefined) {
  const d = new Date(`${key}T00:00:00`);
  return d.toLocaleDateString(locale, {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

// Full timestamp for session rows.
export function formatDateTime(value, locale = undefined) {
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString(locale, {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Clock time only.
export function formatTime(value, locale = undefined) {
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" });
}

// Date without time.
export function formatDate(value, locale = undefined) {
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString(locale, { day: "numeric", month: "short", year: "numeric" });
}

// Canonical session range.
export function formatRange(startValue, endValue, locale = undefined) {
  const start = new Date(startValue);
  const end = new Date(endValue);
  if (Number.isNaN(start.getTime())) return "—";
  const left = `${start.toLocaleDateString(locale, { day: "numeric", month: "short" })} · ${formatTime(
    start,
    locale,
  )}`;
  if (Number.isNaN(end.getTime())) return left;
  return `${left} – ${formatTime(end, locale)}`;
}

// Duration label.
export function formatDuration(minutes) {
  if (minutes == null || Number.isNaN(minutes)) return "—";
  const total = Math.round(minutes);
  if (total < 60) return `${total} min`;
  const hours = Math.floor(total / 60);
  const rest = total % 60;
  return rest ? `${hours} h ${rest} min` : `${hours} h`;
}

// Relative time label.
export function relativeFromNow(value, now = Date.now()) {
  const d = value instanceof Date ? value : new Date(value);
  const target = d.getTime();
  if (Number.isNaN(target)) return "—";
  const delta = target - now;
  const abs = Math.abs(delta);
  const suffix = delta >= 0 ? "left" : "ago";
  if (abs < MINUTE) return delta >= 0 ? "starting now" : "just now";
  if (abs < HOUR) {
    const mins = Math.round(abs / MINUTE);
    return `${mins} min ${suffix}`;
  }
  if (abs < DAY) {
    const hours = Math.round(abs / HOUR);
    return `${hours} h ${suffix}`;
  }
  const days = Math.round(abs / DAY);
  if (days < 31) return `${days} day${days === 1 ? "" : "s"} ${suffix}`;
  return formatDate(d);
}

// Minutes until a timestamp.
export function minutesUntil(value, now = Date.now()) {
  const target = new Date(value).getTime();
  if (Number.isNaN(target)) return 0;
  return Math.round((target - now) / MINUTE);
}

// Whether now lies inside a range.
export function isWithin(startValue, endValue, now = Date.now()) {
  const start = new Date(startValue).getTime();
  const end = new Date(endValue).getTime();
  if (Number.isNaN(start) || Number.isNaN(end)) return false;
  return now >= start && now <= end;
}

// Whether a session is joinable.
export function canJoinMeet(booking, now = Date.now(), graceMinutes = 30) {
  if (!booking || booking.status !== "accepted" || !booking.meet_link) return false;
  return new Date(booking.start_time).getTime() - now <= graceMinutes * MINUTE;
}

// "Starts in 2 h 15 min" / "Happening now" / "Session ended" for a booking.
export function countdownLabel(booking, now = Date.now()) {
  const start = new Date(booking?.start_time).getTime();
  const end = new Date(booking?.end_time).getTime();
  if (Number.isNaN(start) || Number.isNaN(end)) return "";
  if (now > end) return "Session ended";
  if (now >= start) return "Happening now";
  const minutes = Math.ceil((start - now) / 60000);
  const days = Math.floor(minutes / (24 * 60));
  if (days >= 1) return `Starts in ${days} day${days === 1 ? "" : "s"}`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (hours >= 1) return rest ? `Starts in ${hours} h ${rest} min` : `Starts in ${hours} h`;
  return `Starts in ${minutes} min`;
}

// UTC stamp (YYYYMMDDTHHMMSSZ) used by calendar links.
function toUtcStamp(value) {
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
}

// "Add to Google Calendar" template URL for one session.
export function googleCalendarUrl({ title, start, end, details, location } = {}) {
  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: title || "Live consultation",
    dates: `${toUtcStamp(start)}/${toUtcStamp(end)}`,
  });
  if (details) params.set("details", details);
  if (location) params.set("location", location);
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

// Current time as ISO string.
export function nowIso() {
  return new Date().toISOString();
}

// First day of the containing month.
export function monthStart(key) {
  const d = new Date(`${key}T00:00:00`);
  return toDateKey(new Date(d.getFullYear(), d.getMonth(), 1));
}

// Last day of the containing month.
export function monthEnd(key) {
  const d = new Date(`${key}T00:00:00`);
  return toDateKey(new Date(d.getFullYear(), d.getMonth() + 1, 0));
}

// Add display fields to availability rows.
export function decorateAvailabilityDays(days = []) {
  return days.map((day) => {
    const key = day.date;
    return {
      ...day,
      weekday: weekdayShort(key),
      dayOfMonth: dayOfMonth(key),
      label: dayLabel(key),
    };
  });
}

// Split availability into open and full days.
export function partitionAvailabilityDays(days = []) {
  const open = [];
  const full = [];
  for (const day of days) {
    (day.available_slots > 0 ? open : full).push(day);
  }
  return { open, full };
}
