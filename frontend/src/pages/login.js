import Link from "next/link";
import { ArrowRightIcon, SparkleIcon } from "@/components/icons";
import { PageHeader } from "@/components/ui";
import { ROLES } from "@/lib/roles";
import { ROLE_PORTALS } from "@/services/auth";

// Portal tile styling shared by the chooser cards and form headers.
const PORTAL_TILES = {
  user: "bg-gradient-to-br from-primary-600 to-fuchsia-500 text-white shadow-md shadow-primary-500/30",
  "tarot-reader":
    "bg-gradient-to-br from-accent-400 to-accent-600 text-white shadow-md shadow-accent-500/30",
  "spiritual-consultant": "bg-emerald-50 text-emerald-600 ring-1 ring-emerald-100",
  admin: "bg-slate-100 text-slate-600 ring-1 ring-slate-200",
};

export default function LoginPage() {
  return (
    <div className="animate-fade-in">
      <PageHeader
        icon={SparkleIcon}
        gradient="violet"
        eyebrow="Welcome back"
        title="Sign in to MysticLens"
        description="Choose the portal for your role — each role has its own sign-in page."
      />

      <div className="mt-10 grid gap-4 sm:grid-cols-2">
        {ROLE_PORTALS.map((portal) => {
          const RoleIcon = ROLES[portal.role]?.icon || SparkleIcon;
          return (
            <Link
              key={portal.slug}
              href={`/login/${portal.slug}`}
              className="group flex cursor-pointer flex-col rounded-3xl border border-slate-200/90 bg-white p-6 shadow-xs transition hover:-translate-y-0.5 hover:border-primary-200 hover:shadow-lg hover:shadow-slate-900/5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
            >
              <span
                className={`flex h-11 w-11 items-center justify-center rounded-2xl ${
                  PORTAL_TILES[portal.slug] || PORTAL_TILES.user
                }`}
              >
                <RoleIcon className="h-5 w-5" />
              </span>
              <h2 className="mt-4 font-display text-lg font-semibold tracking-tight text-slate-900">
                {portal.label}
              </h2>
              <p className="mt-1 text-sm leading-relaxed text-slate-500">{portal.tagline}</p>
              <span className="mt-auto inline-flex items-center gap-1.5 pt-4 text-sm font-medium text-primary-600">
                Continue to sign in
                <ArrowRightIcon className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
              </span>
            </Link>
          );
        })}
      </div>

      <p className="mt-8 text-center text-sm text-slate-500">
        New here?{" "}
        <Link
          href="/register"
          className="cursor-pointer rounded-full font-medium text-primary-600 transition-colors hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
        >
          Create an account for your role
        </Link>
      </p>
    </div>
  );
}
