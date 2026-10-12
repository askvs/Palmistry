// Dashboard: role-aware shell with header, consoles, and assistant.
import { Suspense, useEffect, useState } from "react";
import { useRouter } from "next/router";
import dynamic from "next/dynamic";
import AdminDashboard from "@/components/dashboards/AdminDashboard";
import ConsultantDashboard from "@/components/dashboards/ConsultantDashboard";
import DashboardAssistant from "@/components/dashboards/DashboardAssistant";
import ReaderDashboard from "@/components/dashboards/ReaderDashboard";
import UserDashboard from "@/components/dashboards/UserDashboard";
import ConsultantSessionsPanel from "@/components/booking/ConsultantSessionsPanel";
import SeekerSessionsPanel from "@/components/booking/SeekerSessionsPanel";
import { Button, PageHeader, Spinner } from "@/components/ui";
import {
  CardsIcon,
  CalendarIcon,
  FileTextIcon,
  HandIcon,
  ShieldIcon,
  SparkleIcon,
} from "@/components/icons";
import { ROLES, roleMeta, blockedPageInfo } from "@/lib/roles";
import { useAuth } from "@/hooks/useAuth";
import { fetchAvatarBlobUrl, fetchProfile } from "@/services/profile";

const DynamicLifeTrend = dynamic(() => import("@/components/dashboards/LifeTrendDashboard"), {
  loading: () => <LifeTrendSkeleton />,
  ssr: false,
});

const ROLE_INTROS = {
  user: "Your personal sanctuary for tarot divinations, palm readings, and cosmic guidance.",
  tarot_reader: "Tarot reader console: oversee querent readings, review spreads, and provide interpretations.",
  spiritual_consultant: "Spiritual consultant hub: analyze seeker trends and dispatch tailored counsel.",
  admin:
    "Platform governance console: manage identities, access privileges, analytics, errors and system telemetry.",
};
// PageHeader tile tone per role badge tone (indigo falls back to the brand tile).
const TILE_TONES = { primary: "primary", accent: "accent", emerald: "emerald", indigo: "primary" };

// Icon for each role's primary dashboard CTA (labels/hrefs come from lib/roles).
const CTA_ICONS = { user: HandIcon, tarot_reader: CardsIcon };

// One secondary action per role next to the primary CTA. Consultant and admin
// get none: their goal is operating their workspace below, not opening
// self-analysis flows — a personal archive would be empty and misleading.
const SECONDARY_ACTIONS = {
  user: { href: "/readings/tarot", label: "New tarot reading", icon: SparkleIcon },
  tarot_reader: { href: "/readings", label: "All archives", icon: FileTextIcon },
  spiritual_consultant: { href: "/consultant-studio", label: "Consultant Studio", icon: CalendarIcon },
  admin: { href: "/admin", label: "Admin console", icon: ShieldIcon },
};

function LifeTrendSkeleton() {
  return (
    <div
      className="animate-pulse rounded-3xl border border-slate-200/90 bg-white p-6 shadow-xs sm:p-7"
      aria-hidden="true"
    >
      <div className="h-5 w-56 rounded bg-slate-200/80" />
      <div className="mt-5 h-24 rounded-2xl bg-slate-100" />
      <div className="mt-3 h-64 rounded-2xl bg-slate-100" />
    </div>
  );
}

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [avatarState, setAvatarState] = useState({ email: null, url: null });
  const userEmail = user?.email ?? null;

  // Set by useRoleGuard on restricted pages: staff who followed a stale link
  // land here with ?blocked=<path> and get a one-line explanation.
  const blockedPath = Array.isArray(router.query.blocked)
    ? router.query.blocked[0]
    : router.query.blocked;
  const blockedInfo = blockedPath && user ? blockedPageInfo(blockedPath, user.role) : null;
  const blockedFeature = blockedInfo?.feature || null;

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  // All roles share the same profile endpoint; the photo is optional, so a
  // failed fetch just leaves the role icon tile in place.
  useEffect(() => {
    if (!userEmail) {
      return undefined;
    }
    let cancelled = false;
    let objectUrl = null;
    (async () => {
      try {
        const profile = await fetchProfile();
        if (!profile?.avatar_key || cancelled) {
          return;
        }
        const url = await fetchAvatarBlobUrl(profile.updated_at);
        if (cancelled) {
          URL.revokeObjectURL(url);
          return;
        }
        objectUrl = url;
        setAvatarState({ email: userEmail, url });
      } catch {
        /* avatar is optional on the dashboard */
      }
    })();
    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [userEmail]);

  // Only trust the fetched URL while it belongs to the signed-in account.
  const avatarUrl = userEmail && avatarState.email === userEmail ? avatarState.url : null;

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner label="Connecting to your personal sanctuary…" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner label="Redirecting to sign-in…" />
      </div>
    );
  }

  const firstName = user.full_name ? user.full_name.split(" ")[0] : user.email.split("@")[0];
  const userRole = user.role || "user";
  const meta = roleMeta(userRole);

  const primaryCta = meta.dashboardCta ? (
    <Button href={meta.dashboardCta.href} icon={CTA_ICONS[userRole] || meta.icon}>
      {meta.dashboardCta.label}
    </Button>
  ) : null;
  const secondaryAction = SECONDARY_ACTIONS[userRole];

  return (
    <div className="animate-fade-in space-y-8">
      <PageHeader
        icon={meta.icon}
        avatarUrl={avatarUrl}
        avatarAlt={`${firstName}'s profile picture`}
        tileTone={TILE_TONES[meta.badgeTone] || "primary"}
        eyebrow={meta.label}
        title={`Welcome back, ${firstName}`}
        description={ROLE_INTROS[userRole] || ROLE_INTROS.user}
        actions={
          <>
            {primaryCta}
            {secondaryAction && (
              <Button href={secondaryAction.href} variant="secondary" icon={secondaryAction.icon}>
                {secondaryAction.label}
              </Button>
            )}
          </>
        }
      />

      {blockedFeature && (
        <div className="flex items-start gap-3 rounded-2xl border border-primary-100 bg-primary-50/70 p-4 text-sm text-primary-900">
          <meta.icon className="mt-0.5 h-4 w-4 shrink-0 text-primary-600" />
          <p>
            The <span className="font-semibold">{blockedFeature}</span> workspace is part of the
            seeker experience. As a {meta.label}, your tools live right here on this dashboard.
          </p>
        </div>
      )}

      {/* Role view render — unknown roles fall back to the seeker console */}
      {userRole === "admin" && <AdminDashboard />}
      {userRole === "spiritual_consultant" && <ConsultantDashboard />}
      {userRole === "tarot_reader" && <ReaderDashboard />}
      {(userRole === "user" || !ROLES[userRole]) && (
        <>
          <UserDashboard />
          <Suspense fallback={null}>
            <DynamicLifeTrend />
          </Suspense>
        </>
      )}

      {/* Booking panels per role; admins get read-only counts, never booking controls. */}
      {["spiritual_consultant", "tarot_reader"].includes(userRole) ? (
        <ConsultantSessionsPanel />
      ) : userRole === "user" || !ROLES[userRole] ? (
        <SeekerSessionsPanel />
      ) : null}

      {/* AI assistant: one grounded, role-scoped overall analysis for every role */}
      <DashboardAssistant />
    </div>
  );
}
