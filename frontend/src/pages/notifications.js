// Notification Center Page
import { useState, useEffect } from "react";
import { useToast } from "@/components/ui/Toast";
import { Link } from "next/link";
import { useAuth } from "@/hooks/useAuth";
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

const BellIcon = () => (
  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
  </svg>
);

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
    return <div className="text-center py-8">Loading...</div>;
  }

  if (!user) {
    return (
      <div className="text-center py-8">
        <p>Please log in to view notifications</p>
        <Link href="/login" className="text-primary-600">
          Log In
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Notifications</h1>

      <div className="space-y-4">
        <div className="flex justify-between items-center mb-4">
          <div className="flex gap-2">
            <button
              onClick={() => setFilter(NotificationType.ALL)}
              className={`px-3 py-1.5 rounded-full border text-sm font-medium transition-colors ${
                filter === NotificationType.ALL
                  ? "bg-primary-600 text-white border-transparent"
                  : "bg-gray-100 text-gray-700 border-primary-600 hover:bg-primary-50"
              }`}
              aria-label="All notifications"
            >
              All
            </button>
            <button
              onClick={() => setFilter(NotificationType.UNREAD)}
              className={`px-3 py-1.5 rounded-full border text-sm font-medium transition-colors ${
                filter === NotificationType.UNREAD
                  ? "bg-primary-600 text-white border-transparent"
                  : "bg-gray-100 text-gray-700 border-primary-600 hover:bg-primary-50"
              }`}
              aria-label="Unread notifications"
            >
              Unread ({unreadCount})
            </button>
          </div>
          <button
            onClick={handleMarkAllRead}
            disabled={unreadCount === 0}
            className="cursor-pointer rounded-full px-3 py-1.5 text-sm font-medium text-primary-600 transition hover:bg-primary-50 disabled:cursor-not-allowed disabled:text-slate-300 disabled:hover:bg-transparent"
          >
            Mark all read
          </button>
        </div>

        <div className="space-y-4">
          {filteredNotifications.length === 0 ? (
            <div className="text-center py-8">
              <BellIcon className="mx-auto h-12 w-12 text-gray-300" />
              <p className="mt-4 text-gray-500">
                {filter === NotificationType.UNREAD
                  ? "No unread notifications"
                  : "No notifications yet"}
              </p>
              <p className="mt-2 text-sm text-gray-500">
                {filter === NotificationType.UNREAD
                  ? "You're all caught up!"
                  : "Check back soon for updates"}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredNotifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`flex items-start p-4 border rounded-lg ${
                    !notification.is_read ? "bg-blue-50 border-primary-200" : "bg-white border-gray-200"
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3">
                      <BellIcon className="h-5 w-5 text-primary-600 flex-shrink-0" />
                      <span className="text-lg font-medium">{notification.title}</span>
                      {!notification.is_read && (
                        <span className="text-xs bg-primary-600 text-white px-2 py-0.5 rounded-full">
                          New
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      {notification.message}
                    </div>
                    <div className="mt-2 text-sm text-gray-500">
                      {new Date(notification.created_at).toLocaleString()}
                    </div>
                  </div>

                  {!notification.is_read && (
                    <button
                      onClick={() => handleMarkRead(notification.id)}
                      className="ml-4 text-sm text-primary-600 hover:text-primary-800 font-medium"
                    >
                      Mark as read
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-8 pt-6 border-t border-gray-200">
          <h2 className="text-xl font-semibold mb-4">Preferences</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-4 rounded-2xl border border-emerald-100 bg-emerald-50/60 px-3.5 py-2.5">
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-700">In-App Notifications</p>
                <p className="text-xs text-gray-500">
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
                className="flex items-center justify-between gap-4 border-b border-gray-100 pb-3 last:border-b-0"
              >
                <span className="min-w-0">
                  <span className="block text-sm font-medium text-gray-700">{label}</span>
                  <span className="block text-xs text-gray-500">{description}</span>
                </span>
                <input
                  type="checkbox"
                  checked={Boolean(preferences[key])}
                  onChange={(e) => togglePreference(key, e.target.checked)}
                  className="h-4 w-4 shrink-0 cursor-pointer rounded border-slate-300 text-primary-600 focus:ring-primary-400"
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
