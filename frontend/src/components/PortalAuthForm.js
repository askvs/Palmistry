// Shared per-role auth form (D-014): used by /login/[role] and /register/[role].
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import BrandMark from "@/components/BrandMark";
import { ArrowLeftIcon, SparkleIcon } from "@/components/icons";
import { Button, InlineError, PageHeader, Panel } from "@/components/ui";
import { ROLES } from "@/lib/roles";
import { useAuth } from "@/hooks/useAuth";

// One input class for every field in the form.
const INPUT_CLASS =
  "w-full rounded-[10px] border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-500 shadow-xs transition focus:border-[#8b5cf6] focus:outline-none focus:ring-[3px] focus:ring-primary-600/25 disabled:cursor-not-allowed disabled:opacity-60";
const LABEL_CLASS = "mb-1.5 block text-sm font-medium text-slate-700";

// Header tile per portal, mirroring the portal chooser cards.
const PORTAL_TILE = {
  user: { gradient: "violet" },
  tarot_reader: { gradient: "gold" },
  spiritual_consultant: { tileTone: "emerald" },
  admin: { tileTone: "slate" },
};

export default function PortalAuthForm({ portal, mode }) {
  const router = useRouter();
  const { loginPortal, registerPortal, loading: authLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [adminInviteCode, setAdminInviteCode] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [banner, setBanner] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});

  const isRegister = mode === "register";
  const otherHref = isRegister ? `/login/${portal.slug}` : `/register/${portal.slug}`;
  const otherLabel = isRegister ? "Sign in instead" : "Create an account";
  const heading = isRegister
    ? `Join as ${portal.label}`
    : `${portal.label} sign in`;
  const RoleIcon = ROLES[portal.role]?.icon || SparkleIcon;
  const tile = PORTAL_TILE[portal.role] || {};
  const oauthBanner =
    router.query.oauth === "error"
      ? { tone: "error", text: "Google sign-in failed. Please try again or use your email and password." }
      : null;
  const activeBanner = banner || oauthBanner;

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setBanner(null);
    setFieldErrors({});
    try {
      if (isRegister) {
        await registerPortal(portal.slug, {
          email,
          password,
          fullName,
          adminInviteCode: portal.inviteOnly ? adminInviteCode : null,
        });
      } else {
        await loginPortal(portal.slug, { email, password });
      }
      router.push("/dashboard");
    } catch (err) {
      if (err.status === 401) {
        setBanner({ tone: "error", text: "Invalid email or password." });
      } else if (err.status === 403 && err.code === "WRONG_PORTAL") {
        setBanner({ tone: "error", text: err.message });
      } else if (err.status === 403 && err.code === "ADMIN_SIGNUP_FORBIDDEN") {
        setBanner({ tone: "error", text: "A valid admin invite code is required to sign up." });
      } else if (err.status === 409) {
        setBanner({
          tone: "error",
          text: "An account with this email already exists. Try signing in instead.",
        });
      } else if (err.status === 429) {
        setBanner({
          tone: "error",
          text: "Too many attempts. Please wait a minute and try again.",
        });
      } else if (Array.isArray(err.fields) && err.fields.length > 0) {
        const map = {};
        for (const f of err.fields) {
          map[f.loc?.[f.loc.length - 1]] = f.msg;
        }
        setFieldErrors(map);
        setBanner({ tone: "error", text: "Please fix the highlighted fields." });
      } else {
        setBanner({
          tone: "error",
          text: err.message || (isRegister ? "Sign-up failed." : "Sign-in failed."),
        });
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl animate-fade-in">
      <div className="grid items-stretch gap-6 lg:grid-cols-[1.05fr_1fr]">
        <aside className="relative hidden overflow-hidden rounded-[20px] bg-gradient-to-b from-[#1e1836] to-[#241b3f] p-8 text-[#ede9fe] lg:flex lg:flex-col lg:justify-between">
          <div aria-hidden="true" className="pointer-events-none absolute inset-0 text-accent-300/[0.04]">
            <span className="absolute left-[12%] top-10 text-3xl">✦</span>
            <span className="absolute right-[18%] bottom-24 text-2xl">✦</span>
            <span className="absolute right-[40%] top-1/2 text-sm">✦</span>
          </div>
          <div className="relative flex items-center gap-2.5">
            <BrandMark />
            <span className="text-sm font-semibold tracking-tight text-[#ede9fe]">MysticLens</span>
          </div>
          <blockquote className="relative font-display text-2xl leading-snug">
            The cards don&rsquo;t tell you what to do. They show you what you already know.
          </blockquote>
          <p className="relative text-[11px] uppercase tracking-[0.16em] text-[#a79fc6]">
            ✦ Palm &amp; tarot divination · private by design
          </p>
        </aside>
        <div className="mx-auto w-full max-w-lg lg:mx-0 lg:max-w-none">
          <PageHeader
            icon={RoleIcon}
            gradient={tile.gradient || false}
            tileTone={tile.tileTone}
            eyebrow={isRegister ? "Create your account" : "Welcome back"}
            title={heading}
            description={portal.tagline}
            actions={
              <Button
                variant="ghost"
                href={isRegister ? "/register" : "/login"}
                icon={ArrowLeftIcon}
              >
                All portals
              </Button>
            }
          />

          <Panel className="mt-6">
            <form onSubmit={handleSubmit} className="space-y-5" noValidate>
              {router.query.oauth === "success" ? (
                <div
                  role="status"
                  className="flex items-center justify-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"
                >
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-300 border-t-emerald-600" />
                  Completing Google sign-in…
                </div>
              ) : (
                activeBanner &&
                (activeBanner.tone === "error" ? (
                  <InlineError message={activeBanner.text} />
                ) : (
                  <div
                    role="status"
                    className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"
                  >
                    {activeBanner.text}
                  </div>
                ))
              )}

              {isRegister && (
                <div>
                  <label htmlFor="fullName" className={LABEL_CLASS}>
                    Name <span className="text-rose-500">*</span>
                  </label>
                  <input
                    id="fullName"
                    type="text"
                    autoComplete="name"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    disabled={submitting}
                    className={INPUT_CLASS}
                    placeholder="Jane Doe"
                  />
                  {fieldErrors.full_name && (
                    <InlineError message={fieldErrors.full_name} className="mt-2" />
                  )}
                </div>
              )}

              <div>
                <label htmlFor="email" className={LABEL_CLASS}>
                  Email <span className="text-rose-500">*</span>
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={submitting}
                  className={INPUT_CLASS}
                  placeholder="you@example.com"
                />
                {fieldErrors.email && <InlineError message={fieldErrors.email} className="mt-2" />}
              </div>

              <div>
                <label htmlFor="password" className={LABEL_CLASS}>
                  Password <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete={isRegister ? "new-password" : "current-password"}
                    required
                    minLength={isRegister ? 8 : undefined}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={submitting}
                    className={`${INPUT_CLASS} pr-12`}
                    placeholder={isRegister ? "At least 8 characters" : "••••••••"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    className="absolute right-2 top-1/2 -translate-y-1/2 cursor-pointer rounded-lg px-2 py-1 text-xs font-medium text-slate-500 transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
                {fieldErrors.password && (
                  <InlineError message={fieldErrors.password} className="mt-2" />
                )}
              </div>

              {isRegister && portal.inviteOnly && (
                <div>
                  <label htmlFor="adminInviteCode" className={LABEL_CLASS}>
                    Admin invite code <span className="text-rose-500">*</span>
                  </label>
                  <input
                    id="adminInviteCode"
                    type="text"
                    required
                    value={adminInviteCode}
                    onChange={(e) => setAdminInviteCode(e.target.value)}
                    disabled={submitting}
                    className={INPUT_CLASS}
                    placeholder="Provided by the platform owner"
                  />
                  {fieldErrors.admin_invite_code && (
                    <InlineError message={fieldErrors.admin_invite_code} className="mt-2" />
                  )}
                </div>
              )}

              <Button
                type="submit"
                size="lg"
                fullWidth
                loading={submitting}
                disabled={submitting || authLoading}
              >
                {submitting
                  ? isRegister
                    ? "Creating account…"
                    : "Signing in…"
                  : isRegister
                    ? `Create ${portal.label} account`
                    : "Sign in"}
              </Button>

              <p className="text-center text-sm text-slate-500">
                <Link
                  href={otherHref}
                  className="cursor-pointer rounded-full font-medium text-primary-600 transition-colors hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                >
                  {otherLabel}
                </Link>
                {" · "}
                <Link
                  href={isRegister ? "/login" : "/register"}
                  className="cursor-pointer rounded-full font-medium text-slate-500 transition-colors hover:text-slate-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                >
                  Choose a different role
                </Link>
              </p>
            </form>
          </Panel>
        </div>
      </div>
    </div>
  );
}
