// Notification Center Page
import { useState, useEffect } from "react";
import { useToast } from "@/components/ui/Toast";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { PageHeader, Spinner } from "@/components/ui";
import Seo from "@/components/Seo";
import { BellIcon } from "@/components/icons";
import {
  fetchNotifications,
  getNotificationPreferences,
  updateNotificationPreferences,
  markNotificationRead,
  markAllNotificationsRead,
} from "@/services/notifications";

const NotificationType = {
  ALL: "all",
  UNREAD: "unread",
  GUIDANCE: "guidance",
  READING: "reading",
  INSIGHTS: "insights",
  GROWTH: "growth",
  ANNOUNCEMENTS: "announcements",
};

// In-app notification preferences, mirroring the backend profile flags.
const PREF_TOGGLES = [
  ["Daily Guidance", "daily_guidance", "Your personalized guidance at 8 AM."],
  ["Reading Reminders", "reading_reminders", "Nudges to continue your reading journey."],
  ["Insight Updates", "insight_updates", "When new palm or tarot insights are ready."],
  ["Spiritual Growth", "spiritual_growth", "Personal-growth insights and prompts."],
  ["Platform Announcements", "platform_announcements", "Important news from the MysticLens team."],
];

const NotificationCenter = () => {
  const { user } = useAuth();
  const { success, error } = useToast();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [filter, setFilter] = useState(NotificationType.ALL);
  const [preferences, setPreferences] = useState({});
  const [loading, setLoading] = useState(true);

  // Load notifications
  useEffect(() => {
    if (!user) return;

    const loadNotifications = async () => {
      try {
        setLoading(true);
        const data = await fetchNotifications();
        setNotifications(data);

        // Calculate unread count
        const unread = data.filter((n) => !n.is_read);
        setUnreadCount(unread.length);
      } catch (err) {
        console.error("Failed to load notifications:", err);
        error("Failed to load notifications");
      } finally {
        setLoading(false);
      }
    };

    loadNotifications();
  }, [user, error]);

  // Load preferences
  useEffect(() => {
    if (!user) return;

    const loadPreferences = async () => {
      try {
        const data = await getNotificationPreferences();
        setPreferences(data);
      } catch (err) {
        console.error("Failed to load preferences:", err);
      }
    };

    loadPreferences();
  }, [user]);

  const handleMarkRead = async (notificationId) => {
    try {
      await markNotificationRead(notificationId);
      setNotifications((prev) =>
        prev.map((n) =>
          n.id === notificationId ? { ...n, is_read: true } : n
        )
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error("Failed to mark read:", err);
      error("Failed to mark as read");
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error("Failed to mark all read:", err);
      error("Failed to mark all as read");
    }
  };

  const togglePreference = async (key, value) => {
    // Optimistic update, then persist; revert to the server state on failure.
    setPreferences((prev) => ({ ...prev, [key]: value }));
    try {
      const updated = await updateNotificationPreferences({ [key]: value });
      setPreferences(updated);
      success("Notification preferences updated");
    } catch (err) {
      console.error("Failed to update preferences:", err);
      error("Failed to update preferences");
      try {
        const data = await getNotificationPreferences();
        setPreferences(data);
      } catch {
        /* ignore revert failure */
      }
    }
  };

  const filteredNotifications = notifications.filter((n) => {
    if (filter === NotificationType.ALL) return true;
    if (filter === NotificationType.UNREAD) return !n.is_read;
    return false;
  });

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center px-6 py-12 text-center">
        <BellIcon className="h-10 w-10 text-slate-300" />
        <p className="mt-4 text-sm font-medium text-slate-600">Please log in to view notifications</p>
        <Link href="/login" className="mt-2 text-sm font-semibold text-primary-700 hover:underline">
          Log In
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <Seo
        title="Notifications"
        description="Session updates, report-ready alerts and system notices — all in one place."
      />

      <PageHeader icon={BellIcon} tileTone="primary" title="Notifications" />

      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div
            role="group"
            aria-label="Notification scope"
            className="inline-flex items-center rounded-full border border-slate-200 bg-slate-100/80 p-0.5"
          >
            <button
              onClick={() => setFilter(NotificationType.ALL)}
              aria-pressed={filter === NotificationType.ALL}
              className={`cursor-pointer rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 ${
                filter === NotificationType.ALL
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-500 hover:text-slate-800"
              }`}
              aria-label="All notifications"
            >
              All
            </button>
            <button
              onClick={() => setFilter(NotificationType.UNREAD)}
              aria-pressed={filter === NotificationType.UNREAD}
              className={`cursor-pointer rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 ${
                filter === NotificationType.UNREAD
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-500 hover:text-slate-800"
              }`}
              aria-label="Unread notifications"
            >
              Unread ({unreadCount})
            </button>
          </div>
          <button
            onClick={handleMarkAllRead}
            disabled={unreadCount === 0}
            className="cursor-pointer rounded-full px-3.5 py-1.5 text-sm font-medium text-primary-600 transition hover:bg-primary-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent"
          >
            Mark all read
          </button>
        </div>

        <div className="space-y-4">
          {filteredNotifications.length === 0 ? (
            <div className="py-12 text-center">
              <BellIcon className="mx-auto h-10 w-10 text-slate-300" />
              <p className="mt-4 text-sm font-medium text-slate-600">
                {filter === NotificationType.UNREAD
                  ? "No unread notifications"
                  : "No notifications yet"}
              </p>
              <p className="mt-1 text-sm text-slate-500">
                {filter === NotificationType.UNREAD
                  ? "You're all caught up!"
                  : "Check back soon for updates"}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {filteredNotifications.map((notification) => (
                <div
                  key={notification.id}
                  className="flex items-start gap-3 py-4"
                >
                  <span
                    className={`mt-[7px] h-2 w-2 shrink-0 rounded-full ${
                      notification.is_read ? "bg-slate-200" : "bg-primary-500"
                    }`}
                    aria-hidden="true"
                  />
                  <div className="flex-1 min-w-0">
                    <span
                      className={`text-[15px] ${
                        notification.is_read
                          ? "font-medium text-slate-700"
                          : "font-semibold text-slate-900"
                      }`}
                    >
                      {notification.title}
                    </span>
                    <div className="text-sm text-slate-600 mt-1 leading-relaxed">
                      {notification.message}
                    </div>
                    <div className="mt-1.5 text-xs text-slate-500 tabular-nums">
                      {new Date(notification.created_at).toLocaleString()}
                    </div>
                  </div>

                  {!notification.is_read && (
                    <button
                      onClick={() => handleMarkRead(notification.id)}
                      className="ml-3 shrink-0 cursor-pointer rounded-full px-3 py-1.5 text-[13px] font-medium text-primary-700 transition hover:bg-primary-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                    >
                      Mark as read
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-8 pt-6 border-t border-slate-100">
          <h2 className="text-[15px] font-semibold tracking-tight text-slate-900 mb-4">Preferences</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-4 rounded-2xl border border-emerald-200/60 bg-emerald-50/60 px-3.5 py-2.5">
              <div className="min-w-0">
                <p className="text-[13.5px] font-medium text-slate-700">In-App Notifications</p>
                <p className="text-xs text-slate-500">
                  Always on — notifications appear here and in the header bell for every role.
                </p>
              </div>
              <span className="inline-flex shrink-0 items-center gap-1.5 text-xs font-semibold text-emerald-600">
                <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
                Enabled
              </span>
            </div>

            {PREF_TOGGLES.map(([label, key, description]) => (
              <label
                key={key}
                className="flex items-center justify-between gap-4 border-b border-slate-100 pb-3 last:border-b-0"
              >
                <span className="min-w-0">
                  <span className="block text-[13.5px] font-medium text-slate-700">{label}</span>
                  <span className="block text-xs text-slate-500">{description}</span>
                </span>
                <input
                  type="checkbox"
                  checked={Boolean(preferences[key])}
                  onChange={(e) => togglePreference(key, e.target.checked)}
                  className="h-4 w-4 shrink-0 cursor-pointer rounded border-slate-300 accent-primary-600 focus:ring-primary-400"
                />
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationCenter;
