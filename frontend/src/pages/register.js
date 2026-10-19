import Link from "next/link";
import { ArrowRightIcon, SparkleIcon } from "@/components/icons";
import Seo from "@/components/Seo";
import { Badge, PageHeader } from "@/components/ui";
import { ROLES } from "@/lib/roles";
import { ROLE_PORTALS } from "@/services/auth";

// Portal tile styling shared by the chooser cards and form headers.
const PORTAL_TILES = {
  user: "bg-primary-600 text-white",
  "tarot-reader": "bg-accent-400 text-slate-900",
  "spiritual-consultant": "bg-emerald-500 text-white",
  admin: "bg-slate-200 text-slate-700",
};

export default function RegisterPage() {
  return (
    <div className="animate-fade-in">
      <Seo
        title="Create your account"
        description="Create your MysticLens account — each role signs up through its own portal. AI-guided palm and tarot readings, private by design."
      />
      <PageHeader
        icon={SparkleIcon}
        gradient="violet"
        eyebrow="Join MysticLens"
        title="Create your account"
        description="Pick your role — each role signs up through its own portal."
      />

      <div className="mt-10 grid gap-4 sm:grid-cols-2">
        {ROLE_PORTALS.map((portal) => {
          const RoleIcon = ROLES[portal.role]?.icon || SparkleIcon;
          return (
            <Link
              key={portal.slug}
              href={`/register/${portal.slug}`}
              className="surface-card group flex cursor-pointer flex-col p-6 transition duration-200 hover:-translate-y-0.5 hover:shadow-lift focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
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
              {portal.inviteOnly && (
                <Badge tone="rose" className="mt-2 self-start">
                  Invite code required
                </Badge>
              )}
              <p className="mt-1 text-sm leading-relaxed text-slate-500">{portal.tagline}</p>
              <span className="mt-auto inline-flex items-center gap-1.5 pt-4 text-sm font-medium text-primary-600">
                Sign up
                <ArrowRightIcon className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
              </span>
            </Link>
          );
        })}
      </div>

      <p className="mt-8 text-center text-sm text-slate-500">
        Already registered?{" "}
        <Link
          href="/login"
          className="cursor-pointer rounded-full font-medium text-primary-600 transition-colors hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
        >
          Sign in via your role portal
        </Link>
      </p>
    </div>
  );
}
