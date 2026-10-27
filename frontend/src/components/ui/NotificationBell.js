import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import { useAuth } from "@/hooks/useAuth";
import {
  fetchNotifications,
  fetchUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/services/notifications";
import { NotificationBadge } from "./NotificationBadge";
import { BellIcon } from "@/components/icons";

const POLL_INTERVAL_MS = 30000;
const RECENT_LIMIT = 6;

function timeAgo(value) {
  if (!value) return "";
  const then = new Date(value).getTime();
  if (Number.isNaN(then)) return "";
  const mins = Math.max(0, Math.floor((Date.now() - then) / 60000));
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

// Header notification bell shown to every signed-in role.
export default function NotificationBell() {
  const { user } = useAuth();
  const { pathname, push, events } = useRouter();
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [loadingItems, setLoadingItems] = useState(false);
  const wrapRef = useRef(null);
  const bellRef = useRef(null);

  // Keep setState in promise callbacks, not the effect body.
  const refresh = useCallback(() => {
    if (!user) return;
    fetchUnreadCount()
      .then((data) => setUnread(Number(data?.unread_count ?? 0)))
      .catch(() => {
        // Transient errors are non-fatal.
      });
  }, [user]);

  // Initial load + light polling while signed in.
  useEffect(() => {
    if (!user) return undefined;
    refresh();
    const id = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [user, refresh]);

  // Re-check the count whenever the user navigates (e.g. back from the center).
  useEffect(() => {
    if (!user) return undefined;
    refresh();
  }, [user, pathname, refresh]);

  // Navigation always dismisses the panel, including keyboard-triggered links.
  useEffect(() => {
    const close = () => setOpen(false);
    events.on("routeChangeStart", close);
    return () => events.off("routeChangeStart", close);
  }, [events]);

  // Dismiss the dropdown on outside click or Escape.
  useEffect(() => {
    if (!open) return undefined;
    const onClick = (event) => {
      if (wrapRef.current && !wrapRef.current.contains(event.target)) setOpen(false);
    };
    const onKey = (event) => {
      if (event.key === "Escape") {
        setOpen(false);
        bellRef.current?.focus();
      }
    };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (!user) return null;

  const loadItems = async () => {
    setLoadingItems(true);
    try {
      const data = (await fetchNotifications({ include_read: true })) || [];
      setItems(data.slice(0, RECENT_LIMIT));
    } catch {
      setItems([]);
    } finally {
      setLoadingItems(false);
    }
  };

  const toggle = async () => {
    const next = !open;
    setOpen(next);
    if (next) await loadItems();
  };

  const handleOpenNotification = async (notification) => {
    try {
      if (!notification.is_read) {
        await markNotificationRead(notification.id);
        setItems((prev) => prev.map((n) => (n.id === notification.id ? { ...n, is_read: true } : n)));
        setUnread((prev) => Math.max(0, prev - 1));
      }
    } catch {
      // ignore
    }
    setOpen(false);
    const target = notification.action_url;
    if (typeof target === "string" && target.startsWith("/")) {
      push(target);
    }
  };

  const handleMarkAll = async () => {
    try {
      await markAllNotificationsRead();
      setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnread(0);
    } catch {
      // ignore
    }
  };

  return (
    <div className="relative" ref={wrapRef}>
      <button
        ref={bellRef}
        type="button"
        onClick={toggle}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={unread > 0 ? `Notifications, ${unread} unread` : "Notifications"}
        className="relative inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-full text-slate-500 transition hover:bg-slate-100 hover:text-slate-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
      >
        <BellIcon className="h-5 w-5" />
        <NotificationBadge count={unread} />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-30 mt-2 w-80 max-w-[85vw] origin-top-right animate-menu-in overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-lg shadow-slate-900/10"
        >
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2.5">
            <span className="text-sm font-semibold text-slate-800">Notifications</span>
            {unread > 0 && (
              <button
                type="button"
                onClick={handleMarkAll}
                className="cursor-pointer text-xs font-medium text-primary-600 transition hover:text-primary-800"
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {loadingItems ? (
              <div className="space-y-3.5 px-4 py-3.5" aria-busy="true">
                <span className="sr-only">Loading notifications…</span>
                {[0, 1, 2].map((row) => (
                  <div key={row} className="flex items-start gap-3" aria-hidden="true">
                    <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full skeleton-shimmer" />
                    <span className="min-w-0 flex-1 space-y-1.5">
                      <span className="block h-3 w-3/4 rounded-[4px] skeleton-shimmer" />
                      <span className="block h-2.5 w-1/2 rounded-[4px] skeleton-shimmer" />
                    </span>
                  </div>
                ))}
              </div>
            ) : items.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-slate-500">You&rsquo;re all caught up</p>
            ) : (
              <ul className="divide-y divide-slate-100">
                {items.map((n) => (
                  <li key={n.id}>
                    <button
                      type="button"
                      onClick={() => handleOpenNotification(n)}
                      role="menuitem"
                      className="flex w-full cursor-pointer items-start gap-3 px-4 py-3 text-left transition hover:bg-slate-50"
                    >
                      <span
                        className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${n.is_read ? "bg-transparent" : "bg-primary-500"}`}
                        aria-hidden="true"
                      />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-medium text-slate-800">{n.title}</span>
                        {n.message ? (
                          <span className="mt-0.5 block truncate text-xs text-slate-500">{n.message}</span>
                        ) : null}
                      </span>
                      <span className="shrink-0 text-[11px] text-slate-500">{timeAgo(n.created_at)}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="border-t border-slate-100 px-4 py-2">
            <Link
              href="/notifications"
              onClick={() => setOpen(false)}
              className="block cursor-pointer text-center text-xs font-semibold text-primary-600 transition hover:text-primary-800"
            >
              View all notifications
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
