import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import { CloseIcon, MenuIcon, SparkleIcon } from "@/components/icons";
import { useAuth } from "@/hooks/useAuth";
import { GUEST_NAV_KEYS, NAV_ITEMS, roleMeta } from "@/lib/roles";
import NotificationBell from "@/components/ui/NotificationBell";

// Public footer links (visible to guests and every role alike).
const FOOTER_NAV = [
  { href: "/", label: "Home" },
  { href: "/readings/tarot", label: "Tarot Sanctuary" },
  { href: "/readings/palm", label: "Palm Reading" },
  { href: "/readings", label: "Archives" },
  { href: "/life-trends", label: "Life Trends" },
  { href: "/personality", label: "Personality" },
];

function BrandMark() {
  return (
    <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-primary-600 via-indigo-600 to-accent-500 text-white shadow-md shadow-primary-500/25">
      <SparkleIcon className="h-4 w-4" />
    </span>
  );
}

function NavLink({ href, label, active, onClick }) {
  return (
    <Link
      href={href}
      onClick={onClick}
      aria-current={active ? "page" : undefined}
      className={`cursor-pointer rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 ${
        active
          ? "bg-primary-50 font-semibold text-primary-700"
          : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
      }`}
    >
      {label}
    </Link>
  );
}

function AuthButtons() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  if (loading) {
    return (
      <span className="inline-flex h-9 w-24 items-center justify-center rounded-full bg-slate-100">
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-500" />
      </span>
    );
  }

  if (user) {
    const role = roleMeta(user.role);

    return (
      <div className="flex items-center gap-2">
        <NotificationBell />
        <div className="hidden items-center gap-1.5 sm:flex">
          <Link
            href="/dashboard"
            className="max-w-[10rem] truncate rounded-full px-3 py-1 text-sm font-semibold text-slate-800 transition hover:bg-primary-50 hover:text-primary-700"
            title={user.email}
          >
            {user.full_name || user.email.split("@")[0]}
          </Link>
          <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-600">
            {role.label}
          </span>
        </div>

        <Link
          href="/profile"
          aria-current={router.pathname === "/profile" ? "page" : undefined}
          className={`cursor-pointer rounded-full px-3 py-1.5 text-xs font-medium transition ${
            router.pathname === "/profile"
              ? "bg-primary-50 font-semibold text-primary-700"
              : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
          }`}
        >
          Profile
        </Link>

        <button
          type="button"
          onClick={async () => {
            await logout();
            router.push("/");
          }}
          className="cursor-pointer rounded-full px-3 py-1.5 text-xs font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
        >
          Sign out
        </button>
      </div>
    );
  }

  return (
    <>
      <Link
        href="/login"
        className="rounded-full px-3.5 py-1.5 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
      >
        Sign in
      </Link>
      <Link
        href="/register"
        className="rounded-full bg-primary-600 px-4 py-1.5 text-sm font-medium text-white shadow-sm shadow-primary-600/25 transition hover:bg-primary-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
      >
        Get started
      </Link>
    </>
  );
}

function isActive(pathname, href) {
  if (href === "/") return pathname === "/";
  // Prefix match so nested reading routes stay highlighted.
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function MainLayout({ children }) {
  const router = useRouter();
  const { user } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const closeMenu = () => setMenuOpen(false);

  // Role-aware navigation per role.
  const role = user ? roleMeta(user.role) : null;
  const navLinks = [
    ...(user ? role.navKeys : GUEST_NAV_KEYS)
      .map((key) => NAV_ITEMS[key])
      .filter(Boolean),
    ...(user ? [{ href: "/dashboard", label: role.dashboardLabel }] : []),
    // Staff workspace entry point.
    ...(user && role.workspace ? [role.workspace] : []),
  ];

  return (
    <div className="page-glow flex min-h-screen flex-col text-slate-900">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:shadow-md"
      >
        Skip to content
      </a>

      <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <Link
            href="/"
            onClick={closeMenu}
            className="flex items-center gap-2.5 rounded-xl focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
          >
            <BrandMark />
            <span className="text-[17px] font-semibold tracking-tight">MysticLens</span>
          </Link>

          <nav className="hidden items-center gap-1 md:flex" aria-label="Primary">
            {navLinks.map((link) => (
              <NavLink
                key={link.href + link.label}
                {...link}
                active={isActive(router.pathname, link.href)}
              />
            ))}
          </nav>

          <div className="hidden items-center gap-2 md:flex">
            <AuthButtons />
          </div>

          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            aria-expanded={menuOpen}
            aria-label="Toggle navigation menu"
            className="inline-flex h-10 w-10 cursor-pointer items-center justify-center rounded-xl text-slate-600 transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 md:hidden"
          >
            {menuOpen ? <CloseIcon /> : <MenuIcon />}
          </button>
        </div>

        {menuOpen && (
          <nav
            className="border-t border-slate-200/70 bg-white px-4 pb-4 pt-3 md:hidden"
            aria-label="Primary mobile"
          >
            <div className="flex flex-col gap-1">
              {navLinks.map((link) => (
                <NavLink
                  key={link.href + link.label}
                  {...link}
                  active={isActive(router.pathname, link.href)}
                  onClick={closeMenu}
                />
              ))}
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-slate-200/70 pt-3">
              <AuthButtons />
            </div>
          </nav>
        )}
      </header>

      <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-4 pb-16 pt-8 sm:px-6 sm:pt-10">
        {children}
      </main>

      <footer className="border-t border-slate-200/70 bg-white/60">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8 sm:flex-row sm:items-start sm:justify-between sm:px-6">
          <div className="max-w-sm">
            <div className="flex items-center gap-2.5">
              <BrandMark />
              <span className="text-sm font-semibold tracking-tight">MysticLens Divination</span>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-slate-500">
              Sacred tarot divination and chirognomic palm analysis crafted for intuitive
              self-reflection, mindfulness, and archetypal guidance.
            </p>
          </div>
          <nav
            className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs font-medium text-slate-500"
            aria-label="Footer"
          >
            {FOOTER_NAV.map((link) => (
              <Link key={link.href} href={link.href} className="transition hover:text-primary-700">
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      </footer>
    </div>
  );
}
