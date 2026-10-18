// Spiritual Consultant application shell (FR-037).
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import {
  CONSULTANT_DYNAMIC_META,
  CONSULTANT_PAGE_META,
  CONSULTANT_ROUTES,
  CONSULTANT_SECONDARY_ROUTES,
} from "@/lib/roles";
import { useAuth } from "@/hooks/useAuth";
import { useRoleGuard } from "@/hooks/useRoleGuard";
import NotificationBell from "@/components/ui/NotificationBell";
import BrandMark from "@/components/BrandMark";
import {
  CloseIcon,
  CompassIcon,
  LogOutIcon,
  MenuIcon,
  SearchIcon,
  SettingsIcon,
  UserIcon,
} from "@/components/icons";
import { initialsOf } from "@/lib/format";

const SIDEBAR_WIDTH = "w-72";

function isActive(pathname, href) {
  if (pathname === href) return true;
  // Prefix match so /consultant/clients/[id] keeps "Clients" highlighted.
  return pathname.startsWith(`${href}/`);
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

function ConsultantProfileCard({ onNavigate }) {
  const { user, logout } = useAuth();
  const router = useRouter();
  if (!user) return null;

  const name = user.full_name || user.email.split("@")[0];

  return (
    <div className="rounded-2xl border border-slate-200/90 bg-white p-3.5 shadow-xs">
      <div className="flex items-center gap-3">
        <span
          aria-hidden="true"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-indigo-600 text-sm font-bold text-white"
        >
          {initialsOf(name)}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-slate-900" title={user.email}>
            {name}
          </p>
          <p className="truncate text-xs text-slate-500">Spiritual Consultant</p>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between gap-2 border-t border-slate-100 pt-3">
        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-700">
          <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
          Available
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
          <Link
            href="/notifications"
            onClick={onNavigate}
            aria-label="Notification preferences"
            className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
          >
            <SettingsIcon className="h-4 w-4" />
          </Link>
          <button
            type="button"
            onClick={async () => {
              await logout();
              router.push("/");
            }}
            aria-label="Sign out"
            className="cursor-pointer rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-rose-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
          >
            <LogOutIcon className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function SidebarBody({ onNavigate }) {
  const router = useRouter();
  const { pathname } = router;

  return (
    <div className="flex h-full flex-col gap-6 overflow-y-auto p-4">
      <Link
        href="/consultant/dashboard"
        onClick={onNavigate}
        className="flex items-center gap-2.5 rounded-xl px-1 py-1 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
      >
        <BrandMark />
        <span className="min-w-0">
          <span className="block truncate text-[15px] font-semibold tracking-tight text-slate-900">
            Palmistry &amp; Tarot
          </span>
          <span className="block text-[11px] font-medium uppercase tracking-widest text-primary-600">
            Consultant
          </span>
        </span>
      </Link>

      <nav className="flex-1 space-y-1" aria-label="Consultant sections">
        <p className="px-3 pb-1 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
          Workspace
        </p>
        {CONSULTANT_ROUTES.map((item) => (
          <NavRow
            key={item.href}
            {...item}
            active={isActive(pathname, item.href)}
            onClick={onNavigate}
          />
        ))}

        <p className="px-3 pb-1 pt-4 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">
          Account
        </p>
        {CONSULTANT_SECONDARY_ROUTES.map((item) => (
          <NavRow
            key={item.href}
            {...item}
            active={isActive(pathname, item.href)}
            onClick={onNavigate}
          />
        ))}
      </nav>

      <ConsultantProfileCard onNavigate={onNavigate} />
    </div>
  );
}

function ShellHeader({ onOpenMenu }) {
  const router = useRouter();
  const { pathname, asPath } = router;
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [search, setSearch] = useState("");
  const menuRef = useRef(null);

  const meta = CONSULTANT_PAGE_META[pathname] || CONSULTANT_DYNAMIC_META[pathname] || null;
  const activeRoute = CONSULTANT_ROUTES.find((route) => isActive(pathname, route.href));
  const pageTitle = meta?.title || activeRoute?.label || "Consultant Portal";

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

  function submitSearch(event) {
    event.preventDefault();
    const query = search.trim();
    router.push(query ? `/consultant/clients?search=${encodeURIComponent(query)}` : "/consultant/clients");
  }

  const name = user?.full_name || user?.email?.split("@")[0] || "Consultant";

  return (
    <header className="sticky top-0 z-20 border-b border-[#eae6f5] bg-white/85 backdrop-blur-md">
      <div className="flex h-16 items-center gap-3 px-4 sm:px-6 lg:px-8">
        <button
          type="button"
          onClick={onOpenMenu}
          aria-label="Open consultant navigation"
          aria-expanded={false}
          className="inline-flex h-10 w-10 shrink-0 cursor-pointer items-center justify-center rounded-xl text-slate-600 transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 lg:hidden"
        >
          <MenuIcon />
        </button>

        <div className="min-w-0 flex-1">
          <nav aria-label="Breadcrumb" className="hidden sm:block">
            <ol className="flex items-center gap-1.5 text-[11px] font-medium text-slate-500">
              <li>
                <Link href="/consultant/dashboard" className="transition hover:text-primary-600">
                  Consultant
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

        <form
          onSubmit={submitSearch}
          role="search"
          className="relative hidden md:block"
        >
          <label htmlFor="consultant-search" className="sr-only">
            Search clients
          </label>
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            id="consultant-search"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search clients…"
            className="h-9 w-56 rounded-full border border-slate-200 bg-slate-50 pl-9 pr-3 text-sm text-slate-800 transition placeholder:text-slate-500 focus-border-primary-300 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-primary-600"
          />
        </form>

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
                className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-indigo-600 text-xs font-bold text-white"
              >
                {initialsOf(name)}
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

export default function ConsultantLayout({ children }) {
  const router = useRouter();
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Role guard: redirect non-consultants away from the workspace shell.
  const blocked = useRoleGuard();

  // Close the drawer whenever navigation starts.
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
      <div className="aurora flex min-h-screen items-center justify-center text-slate-500">
        <p className="text-sm">Redirecting…</p>
      </div>
    );
  }

  return (
    <div className="aurora flex min-h-screen text-slate-900">
      <a
        href="#consultant-main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg bg-white px-4 py-2 text-sm font-medium shadow-md"
      >
        Skip to content
      </a>

      {/* Permanent sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 hidden ${SIDEBAR_WIDTH} border-r border-slate-200/70 bg-white/80 backdrop-blur-md lg:block`}
        aria-label="Consultant navigation"
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
          id="consultant-main"
          className="mx-auto w-full max-w-7xl flex-1 px-4 pb-16 pt-6 sm:px-6 sm:pt-8 lg:px-8"
        >
          {children}
        </main>

        <footer className="border-t border-[rgba(255,255,255,0.08)] bg-gradient-to-b from-[#1e1836] to-[#241b3f] px-4 py-5 text-[#a79fc6] sm:px-6 lg:px-8">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 text-xs">
            <span className="inline-flex items-center gap-1.5">
              <CompassIcon className="h-3.5 w-3.5 text-accent-300" />
              Palmistry &amp; Tarot · Spiritual Consultant workspace
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
