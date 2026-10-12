// Administrator application shell (FR-038 — Admin Dashboard).
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import {
  ADMIN_PAGE_META,
  ADMIN_ROUTES,
  ADMIN_SECONDARY_ROUTES,
} from "@/lib/roles";
import { useAuth } from "@/hooks/useAuth";
import { useRoleGuard } from "@/hooks/useRoleGuard";
import NotificationBell from "@/components/ui/NotificationBell";
import {
  CloseIcon,
  LogOutIcon,
  MenuIcon,
  SettingsIcon,
  ShieldIcon,
  SparkleIcon,
  UserIcon,
} from "@/components/icons";
import { initialsOf } from "@/lib/format";

const SIDEBAR_WIDTH = "w-72";

function isActive(pathname, href) {
  if (pathname === href) return true;
  // Prefix match so a nested admin route keeps its section highlighted.
  return pathname.startsWith(`${href}/`);
}

function BrandMark() {
  return (
    <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-primary-600 via-indigo-600 to-accent-500 text-white shadow-md shadow-primary-500/25">
      <SparkleIcon className="h-4 w-4" />
    </span>
  );
}

function NavRow({ href, label, icon: Icon, active, onClick }) {
  return (
    <Link
      href={href}
      onClick={onClick}
      aria-current={active ? "page" : undefined}
      className={`flex cursor-pointer items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 ${
        active
          ? "bg-primary-50 text-primary-700 ring-1 ring-primary-100"
          : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
      }`}
    >
      <Icon className="h-[18px] w-[18px] shrink-0" />
      <span className="truncate">{label}</span>
    </Link>
  );
}

function SidebarBody({ onNavigate }) {
  const router = useRouter();
  const { user, logout } = useAuth();
  const { pathname } = router;
  if (!user) return null;

  const name = user.full_name || user.email.split("@")[0];

  return (
    <div className="flex h-full flex-col gap-6 overflow-y-auto px-4 py-5">
      <Link
        href="/"
        onClick={onNavigate}
        className="flex items-center gap-2.5 rounded-xl focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
      >
        <BrandMark />
        <span className="text-[15px] font-semibold tracking-tight">MysticLens</span>
      </Link>

      <nav aria-label="Admin sections" className="flex-1 space-y-1">
        <p className="px-3 pb-1 text-[11px] font-bold uppercase tracking-wider text-slate-400">
          Console
        </p>
        {ADMIN_ROUTES.map((route) => (
          <NavRow
            key={route.href}
            {...route}
            active={isActive(pathname, route.href)}
            onClick={onNavigate}
          />
        ))}

        <p className="px-3 pb-1 pt-5 text-[11px] font-bold uppercase tracking-wider text-slate-400">
          Account
        </p>
        {ADMIN_SECONDARY_ROUTES.map((route) => (
          <NavRow
            key={route.href}
            {...route}
            active={isActive(pathname, route.href)}
            onClick={onNavigate}
          />
        ))}
      </nav>

      <div className="rounded-2xl border border-slate-200/90 bg-white p-3.5 shadow-xs">
        <div className="flex items-center gap-3">
          <span
            aria-hidden="true"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-primary-600 text-sm font-bold text-white"
          >
            {initialsOf(name)}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-slate-900" title={user.email}>
              {name}
            </p>
            <p className="truncate text-xs text-slate-500">Administrator</p>
          </div>
        </div>
        <div className="mt-3 flex items-center justify-between gap-2 border-t border-slate-100 pt-3">
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-indigo-700">
            <ShieldIcon className="h-3.5 w-3.5" />
            Platform governance
          </span>
          <div className="flex items-center gap-1">
            <Link
              href="/profile"
              onClick={onNavigate}
              aria-label="Your profile"
              className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
            >
              <UserIcon className="h-4 w-4" />
            </Link>
            <button
              type="button"
              onClick={async () => {
                await logout();
                router.push("/");
              }}
              aria-label="Sign out"
              className="cursor-pointer rounded-lg p-1.5 text-slate-400 transition hover:bg-rose-50 hover:text-rose-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
            >
              <LogOutIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ShellHeader({ onOpenMenu }) {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);
  const { pathname } = router;
  const meta = ADMIN_PAGE_META[pathname];
  const activeRoute = ADMIN_ROUTES.find((route) => isActive(pathname, route.href));
  const pageTitle = meta?.title || activeRoute?.label || "Admin Console";

  useEffect(() => {
    if (!menuOpen) return undefined;
    const onClick = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) setMenuOpen(false);
    };
    const onKey = (event) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  const name = user ? user.full_name || user.email.split("@")[0] : "";

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-3 px-4 sm:px-6 lg:px-8">
        <button
          type="button"
          onClick={onOpenMenu}
          aria-label="Open admin navigation"
          className="inline-flex h-10 w-10 cursor-pointer items-center justify-center rounded-xl text-slate-600 transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 lg:hidden"
        >
          <MenuIcon />
        </button>

        <div className="min-w-0 flex-1">
          <nav aria-label="Breadcrumb" className="hidden sm:block">
            <ol className="flex items-center gap-1.5 text-[11px] font-medium text-slate-400">
              <li>
                <Link href="/admin" className="transition hover:text-primary-600">
                  Admin
                </Link>
              </li>
              <li aria-hidden="true">/</li>
              <li className="truncate text-slate-500">{meta?.crumb || activeRoute?.label}</li>
            </ol>
          </nav>
          <h1 className="truncate text-sm font-semibold tracking-tight text-slate-900 sm:text-base">
            {pageTitle}
          </h1>
        </div>

        <div className="flex items-center gap-1.5">
          <NotificationBell />

          <div className="relative" ref={menuRef}>
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              className="flex cursor-pointer items-center gap-2 rounded-full py-1 pl-1 pr-2.5 transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
            >
              <span
                aria-hidden="true"
                className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-primary-600 text-xs font-bold text-white"
              >
                {initialsOf(name || "admin")}
              </span>
              <span className="hidden text-sm font-medium text-slate-700 lg:block">{name}</span>
            </button>

            {menuOpen && (
              <div
                role="menu"
                className="absolute right-0 z-30 mt-2 w-52 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-lg shadow-slate-900/10"
              >
                <Link
                  href="/profile"
                  role="menuitem"
                  onClick={() => setMenuOpen(false)}
                  className="flex cursor-pointer items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700 transition hover:bg-slate-50"
                >
                  <UserIcon className="h-4 w-4 text-slate-400" />
                  Profile
                </Link>
                <Link
                  href="/notifications"
                  role="menuitem"
                  onClick={() => setMenuOpen(false)}
                  className="flex cursor-pointer items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700 transition hover:bg-slate-50"
                >
                  <SettingsIcon className="h-4 w-4 text-slate-400" />
                  Settings
                </Link>
                <button
                  type="button"
                  role="menuitem"
                  onClick={async () => {
                    setMenuOpen(false);
                    await logout();
                    router.push("/");
                  }}
                  className="flex w-full cursor-pointer items-center gap-2.5 border-t border-slate-100 px-4 py-2.5 text-sm text-slate-700 transition hover:bg-rose-50 hover:text-rose-700"
                >
                  <LogOutIcon className="h-4 w-4 text-slate-400" />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export default function AdminLayout({ children }) {
  const router = useRouter();
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Role guard: redirect non-admins away from the console shell.
  const blocked = useRoleGuard();

  useEffect(() => {
    const close = () => setDrawerOpen(false);
    router.events.on("routeChangeStart", close);
    return () => {
      router.events.off("routeChangeStart", close);
    };
  }, [router.events]);

  useEffect(() => {
    if (!drawerOpen) return undefined;
    const onKey = (event) => {
      if (event.key === "Escape") setDrawerOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [drawerOpen]);

  if (blocked) {
    return (
      <div className="page-glow flex min-h-screen items-center justify-center text-slate-500">
        <p className="text-sm">Redirecting…</p>
      </div>
    );
  }

  return (
    <div className="page-glow flex min-h-screen text-slate-900">
      <a
        href="#admin-main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg bg-white px-4 py-2 text-sm font-medium shadow-md"
      >
        Skip to content
      </a>

      {/* Permanent sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 hidden ${SIDEBAR_WIDTH} border-r border-slate-200/70 bg-white/80 backdrop-blur-md lg:block`}
        aria-label="Admin navigation"
      >
        <SidebarBody />
      </aside>

      {/* Mobile drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true">
          <div
            className="absolute inset-0 animate-fade-in bg-slate-900/40 backdrop-blur-sm"
            onClick={() => setDrawerOpen(false)}
            aria-hidden="true"
          />
          <div
            className={`relative h-full ${SIDEBAR_WIDTH} max-w-[85vw] animate-rise-in bg-white shadow-xl`}
          >
            <button
              type="button"
              onClick={() => setDrawerOpen(false)}
              aria-label="Close navigation"
              className="absolute right-3 top-3 z-10 cursor-pointer rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
            >
              <CloseIcon />
            </button>
            <SidebarBody onNavigate={() => setDrawerOpen(false)} />
          </div>
        </div>
      )}

      <div className={`flex min-h-screen min-w-0 flex-1 flex-col lg:pl-72`}>
        <ShellHeader onOpenMenu={() => setDrawerOpen(true)} />

        <main
          id="admin-main"
          className="mx-auto w-full max-w-7xl flex-1 px-4 pb-16 pt-6 sm:px-6 sm:pt-8 lg:px-8"
        >
          {children}
        </main>

        <footer className="border-t border-slate-200/70 bg-white/60 px-4 py-5 sm:px-6 lg:px-8">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
            <span className="inline-flex items-center gap-1.5">
              <ShieldIcon className="h-3.5 w-3.5 text-primary-500" />
              Palmistry &amp; Tarot · Platform administration
            </span>
            <span>
              Interpretive guidance for self-reflection — not medical, financial or legal advice.
            </span>
          </div>
        </footer>
      </div>
    </div>
  );
}
