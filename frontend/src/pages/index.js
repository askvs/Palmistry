import Link from "next/link";
import BackendStatus from "@/components/BackendStatus";
import Seo from "@/components/Seo";
import { Button } from "@/components/ui";
import {
  ArrowRightIcon,
  CardsIcon,
  HandIcon,
  ScanIcon,
  ShieldIcon,
  SparkleIcon,
} from "@/components/icons";

const READING_TYPES = [
  {
    href: "/readings/palm",
    title: "Palm Analysis",
    description:
      "Upload a palm photo and let computer vision trace your major lines — heart, head, life, and fate.",
    cta: "Start a palm reading",
    icon: HandIcon,
    tile: "bg-primary-600 text-white",
  },
  {
    href: "/readings/tarot",
    title: "Tarot Reading",
    description:
      "Choose from six guided spreads, draw your cards, and receive a personalized interpretation.",
    cta: "Draw tarot cards",
    icon: CardsIcon,
    tile: "bg-accent-400 text-slate-900",
  },
];

const FEATURES = [
  {
    icon: ScanIcon,
    title: "Vision-based line analysis",
    description:
      "AI detects and interprets palm lines and hand shape, then translates them into plain language.",
    tint: "bg-primary-50 text-primary-600",
  },
  {
    icon: CardsIcon,
    title: "Six guided spreads",
    description:
      "From a single daily card to the Celtic Cross — each spread comes with structured guidance.",
    tint: "bg-accent-50 text-accent-600",
  },
  {
    icon: ShieldIcon,
    title: "Private by design",
    description:
      "Your images and readings stay yours. Built for reflection first — never judgment or diagnosis.",
    tint: "bg-emerald-50 text-emerald-600",
  },
];

export default function Home() {
  return (
    <div className="space-y-16 sm:space-y-20">
      <Seo />

      {/* Hero */}
      <section className="text-center">
        <span className="animate-rise-in inline-flex items-center gap-1.5 rounded-full border border-primary-200/80 bg-primary-50 px-3 py-1 text-xs font-medium text-primary-700">
          <SparkleIcon className="h-3 w-3" />
          AI-guided readings · Early access
        </span>

        <h1 className="animate-rise-in [animation-delay:90ms] mx-auto mt-6 max-w-3xl font-display font-semibold tracking-[-0.02em] text-4xl leading-tight text-slate-900 sm:text-[56px] sm:leading-[1.06]">
          Self-insight,{" "}
          <em className="font-display italic text-primary-600">beautifully decoded</em>.
        </h1>

        <p className="animate-rise-in [animation-delay:180ms] mx-auto mt-5 max-w-2xl text-base leading-relaxed text-slate-600 sm:text-lg">
          MysticLens pairs modern AI with centuries-old symbolism. Upload a palm photo or draw
          tarot cards — and receive thoughtful, personal guidance for reflection and growth.
        </p>

        <div className="animate-rise-in [animation-delay:270ms] mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Button href="/readings/palm" size="lg" iconRight={ArrowRightIcon}>
            Read my palm
          </Button>
          <Button href="/readings/tarot" variant="secondary" size="lg">
            Draw tarot cards
          </Button>
        </div>

        <p className="mt-4 text-xs text-slate-500">
          Free during early access · No account required
        </p>
      </section>

      <BackendStatus />

      {/* Reading types */}
      <section className="grid gap-5 sm:grid-cols-2">
        {READING_TYPES.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className="group flex flex-col surface-card p-8 transition duration-200 hover:-translate-y-0.5 hover:border-primary-200 hover:shadow-lift focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
            >
              <span
                className={`flex h-12 w-12 items-center justify-center rounded-2xl shadow-lg ${item.tile}`}
              >
                <Icon className="h-6 w-6" />
              </span>
              <h2 className="mt-5 text-lg font-semibold tracking-tight">{item.title}</h2>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-500">{item.description}</p>
              <span className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-primary-600">
                {item.cta}
                <ArrowRightIcon className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
              </span>
            </Link>
          );
        })}
      </section>

      {/* Features */}
      <section>
        <p className="text-center text-[11px] font-bold uppercase tracking-[0.16em] text-primary-700">
          Why MysticLens
        </p>
        <div className="mt-8 grid gap-10 sm:grid-cols-3">
          {FEATURES.map((feature) => {
            const Icon = feature.icon;
            return (
              <div key={feature.title} className="text-center sm:text-left">
                <span
                  className={`inline-flex h-11 w-11 items-center justify-center rounded-xl ${feature.tint}`}
                >
                  <Icon className="h-5 w-5" />
                </span>
                <h3 className="mt-4 text-base font-semibold tracking-tight">{feature.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-500">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Trust band — reuses existing product facts; do NOT invent metrics (spec §6.1 honesty note) */}
      <section className="text-center">
        <div className="divider-rule mx-auto max-w-xl" aria-hidden="true"><span className="font-display">✦</span></div>
        <p className="mx-auto mt-6 max-w-2xl font-display text-xl leading-relaxed text-slate-800 sm:text-2xl">
          Built for reflection first — never judgment or diagnosis.
        </p>
      </section>

      {/* Closing CTA */}
      <section className="aurora rounded-[20px] border border-slate-200/70 px-6 py-12 text-center sm:py-14">
        <h2 className="font-display text-2xl font-semibold tracking-[-0.02em] text-slate-900 sm:text-3xl">
          Begin with a single reading.
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-[15px] leading-relaxed text-slate-600">
          Free during early access · No account required
        </p>
        <div className="mt-7 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Button href="/readings/palm" size="lg" iconRight={ArrowRightIcon}>Read my palm</Button>
          <Button href="/readings/tarot" variant="secondary" size="lg">Draw tarot cards</Button>
        </div>
      </section>
    </div>
  );
}
