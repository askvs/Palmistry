import { api } from "./api";

export async function fetchNotifications(params = {}) {
  const query = new URLSearchParams(params).toString();
  return api.get(`/api/v1/notifications${query ? `?${query}` : ""}`);
}

export async function fetchUnreadCount() {
  return api.get("/api/v1/notifications/unread-count");
}

export async function markNotificationRead(notificationId) {
  return api.patch(`/api/v1/notifications/${notificationId}/read`);
}

export async function markAllNotificationsRead() {
  return api.patch("/api/v1/notifications/read-all");
}

export async function getNotificationPreferences() {
  return api.get("/api/v1/notifications/preferences");
}

export async function updateNotificationPreferences(prefs) {
  return api.put("/api/v1/notifications/preferences", prefs);
}